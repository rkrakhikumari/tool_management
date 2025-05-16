from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import *

User = get_user_model()  

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class MembershipSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    class Meta:
        model = Membership
        fields = ['id', 'user', 'role', 'organization']

class OrganizationSerializer(serializers.ModelSerializer):
    memberships = MembershipSerializer(source='membership_set', many=True, read_only=True)
    class Meta:
        model = Organization
        fields = ['id', 'name', 'created_at', 'memberships']

class ProjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Project
        fields = ['id', 'name', 'description', 'organization', 'created_at']

class BoardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Board
        fields = ['id', 'name', 'project']

class ColumnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Column
        fields = ['id', 'name', 'board', 'order']

class LabelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Label
        fields = ['id', 'name', 'color']

class TaskSerializer(serializers.ModelSerializer):
    assignees = serializers.PrimaryKeyRelatedField(queryset=User.objects.all(), many=True)
    labels = serializers.PrimaryKeyRelatedField(queryset=Label.objects.all(), many=True, required=False)

    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'column', 'assignees', 'due_date', 'priority', 'created_at', 'updated_at', 'labels']

    def create(self, validated_data):
        assignees = validated_data.pop('assignees', [])
        labels = validated_data.pop('labels', [])
        task = Task.objects.create(**validated_data)
        task.assignees.set(assignees)
        task.labels.set(labels)
        return task

    def update(self, instance, validated_data):
        assignees = validated_data.pop('assignees', None)
        labels = validated_data.pop('labels', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if assignees is not None:
            instance.assignees.set(assignees)
        if labels is not None:
            instance.labels.set(labels)
        return instance
    

class RecursiveField(serializers.Serializer):
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data



class CommentSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = ['id', 'task', 'user', 'content', 'parent', 'created_at', 'replies']

    def get_replies(self, obj):
        return CommentSerializer(obj.replies.all(), many=True).data


class ActivityLogSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    task = serializers.StringRelatedField()
    project = serializers.StringRelatedField()

    class Meta:
        model = ActivityLog
        fields = '__all__'


class TasksCompletedSerializer(serializers.Serializer):
    date = serializers.DateField()
    completed_tasks_count = serializers.IntegerField()

class MemberProductivitySerializer(serializers.Serializer):
    user_id = serializers.IntegerField()
    user_name = serializers.CharField()
    completed_tasks_count = serializers.IntegerField()

class MissedDeadlinesSerializer(serializers.Serializer):
    date = serializers.DateField()
    missed_tasks_count = serializers.IntegerField()

class BurndownChartSerializer(serializers.Serializer):
    date = serializers.DateField()
    remaining_tasks_count = serializers.IntegerField()

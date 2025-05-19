from rest_framework import viewsets, permissions, serializers, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import *
from .utils import *
from .serializers import *
from .permissions import IsMember
from rest_framework.permissions import IsAuthenticated
from django.utils.timezone import now
from datetime import timedelta
from rest_framework.views import APIView
from django.db.models import Count
from django.shortcuts import render



def home(request):
    context = {
        'title': 'TaskManager Home',
        'app_name': 'TaskManager',
        'welcome_message': 'Manage your organizations, projects, and tasks efficiently.'
    }
    return render(request, 'core/home.html', context)


class OrganizationViewSet(viewsets.ModelViewSet):
    queryset = Organization.objects.all()
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        org = serializer.save()
        Membership.objects.create(user=self.request.user, organization=org, role='admin')
        self.request.session['active_org'] = org.id

    @action(detail=True, methods=['post'], url_path='join')
    def join_organization(self, request, pk=None):
        org = self.get_object()
        user = request.user

        membership, created = Membership.objects.get_or_create(
            user=user,
            organization=org,
            defaults={'role': 'member'}
        )

        return Response(
            {'status': 'joined', 'role': membership.role},
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'], url_path='switch')
    def switch_organization(self, request, pk=None):
        org = self.get_object()

        if not Membership.objects.filter(user=request.user, organization=org).exists():
            return Response(
                {'detail': 'You are not a member of this organization.'},
                status=status.HTTP_403_FORBIDDEN
            )

        request.session['active_org'] = org.id
        return Response({'status': 'switched', 'organization': org.name}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['get'], url_path='my-organizations')
    def my_organizations(self, request):
        memberships = Membership.objects.filter(user=request.user)
        data = [
            {
                "id": m.organization.id,
                "name": m.organization.name,
                "role": m.role
            }
            for m in memberships
        ]
        active_org_id = request.session.get('active_org')
        return Response({
            "organizations": data,
            "active_org_id": active_org_id
        })


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        org = get_active_organization(self.request)
        return Project.objects.filter(organization=org)

    def perform_create(self, serializer):
        org = get_active_organization(self.request)
        serializer.save(organization=org)


class BoardViewSet(viewsets.ModelViewSet):
    queryset = Board.objects.all()
    serializer_class = BoardSerializer
    permission_classes = [permissions.IsAuthenticated, IsMember]

    def get_queryset(self):
        org = get_active_organization(self.request)
        return Board.objects.filter(project__organization=org)

    def perform_create(self, serializer):
        org = get_active_organization(self.request)
        project = serializer.validated_data.get('project')
        if project.organization != org:
            raise serializers.ValidationError("Project does not belong to the active organization.")
        serializer.save()


class ColumnViewSet(viewsets.ModelViewSet):
    queryset = Column.objects.all()
    serializer_class = ColumnSerializer
    permission_classes = [permissions.IsAuthenticated, IsMember]

    def get_queryset(self):
        org = get_active_organization(self.request)
        return Column.objects.filter(board__project__organization=org)

    def perform_create(self, serializer):
        org = get_active_organization(self.request)
        board = serializer.validated_data.get('board')
        if board.project.organization != org:
            raise serializers.ValidationError("Board does not belong to the active organization.")
        serializer.save()


User = get_user_model()

class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated, IsMember]

    def get_queryset(self):
        org = get_active_organization(self.request)
        return Task.objects.filter(column__board__project__organization=org)

    def perform_create(self, serializer):
        org = get_active_organization(self.request)
        column = serializer.validated_data.get('column')
        if column.board.project.organization != org:
            raise serializers.ValidationError("Column does not belong to the active organization.")
        serializer.save()

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def assign_member(self, request, pk=None):
        task = self.get_object()
        user_id = request.data.get("user_id")

        try:
            user_to_assign = User.objects.get(pk=user_id)
            task.assignees.add(user_to_assign) 

            log_activity(
                user=request.user,
                task=task,
                action='assigned',
                description=f"Assigned '{user_to_assign.username}' to task '{task.title}'"
            )
            return Response({"message": "User assigned successfully."})
        except User.DoesNotExist:
            return Response({"error": "User not found."}, status=404)


class LabelViewSet(viewsets.ModelViewSet):
    queryset = Label.objects.all()
    serializer_class = LabelSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        org = get_active_organization(self.request)
        return Label.objects.filter(organization=org)

    def perform_create(self, serializer):
        org = get_active_organization(self.request)
        serializer.save(organization=org)


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Comment.objects.filter(task__id=self.request.query_params.get('task'))

    def perform_create(self, serializer):
        comment = serializer.save(user=self.request.user)
        log_activity(
            user=self.request.user,
            task=comment.task,
            action='commented',
            description=f"Commented on task '{comment.task.title}'"
        )


class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ActivityLog.objects.all()
    serializer_class = ActivityLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()

        project = self.request.query_params.get('project')
        user = self.request.query_params.get('user')
        task = self.request.query_params.get('task')

        filters = {}
        if project:
            filters['project__id'] = project
        if user:
            filters['user__id'] = user
        if task:
            filters['task__id'] = task
        return qs.filter(**filters)




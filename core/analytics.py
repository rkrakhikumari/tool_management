from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.utils.timezone import now
from datetime import timedelta
from core.models import Task, Membership  
from .serializers import *


def is_member_of_organization(user, org_id):
    return Membership.objects.filter(user=user, organization_id=org_id).exists()


class TasksCompletedPerDay(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        org_id = request.query_params.get("org_id")
        project_id = request.query_params.get("project_id")
        start_date = request.query_params.get("start_date")
        end_date = request.query_params.get("end_date")

        if not org_id:
            return Response({"detail": "Missing required parameter: org_id"}, status=400)

        if not is_member_of_organization(user, org_id):
            return Response({"detail": "Unauthorized for this organization."}, status=403)

        today = now().date()
        start_date = start_date or (today - timedelta(days=7)).isoformat()
        end_date = end_date or today.isoformat()

        tasks = Task.objects.filter(
            organization_id=org_id,
            completed_at__date__range=(start_date, end_date)
        )

        if project_id:
            tasks = tasks.filter(column__board__project_id=project_id)

        tasks = tasks.annotate(date=TruncDate("completed_at")).values("date").annotate(
            completed_tasks_count=Count("id")
        ).order_by("date")

        serializer = TasksCompletedSerializer(tasks, many=True)
        return Response(serializer.data)


class MemberProductivity(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        org_id = request.query_params.get("org_id")
        project_id = request.query_params.get("project_id")

        if not org_id:
            return Response({"detail": "Missing required parameter: org_id"}, status=400)

        if not is_member_of_organization(user, org_id):
            return Response({"detail": "Unauthorized for this organization."}, status=403)

        tasks = Task.objects.filter(organization_id=org_id)

        if project_id:
            tasks = tasks.filter(column__board__project_id=project_id)

        tasks = tasks.values("assignees__id", "assignees__username").annotate(
            completed=Count("id", filter=Q(completed_at__isnull=False)),
            pending=Count("id", filter=Q(completed_at__isnull=True)),
        ).order_by("-completed")

        serializer = MemberProductivitySerializer(tasks, many=True)
        return Response(serializer.data)


class MissedDeadlines(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        org_id = request.query_params.get("org_id")
        project_id = request.query_params.get("project_id")

        if not org_id:
            return Response({"detail": "Missing required parameter: org_id"}, status=400)

        if not is_member_of_organization(user, org_id):
            return Response({"detail": "Unauthorized for this organization."}, status=403)

        today = now().date()

        tasks = Task.objects.filter(
            organization_id=org_id,
            due_date__lt=today,
            completed_at__isnull=True
        )

        if project_id:
            tasks = tasks.filter(column__board__project_id=project_id)

        serializer = MissedDeadlinesSerializer(tasks, many=True)
        return Response(serializer.data)


class BurnDownChart(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        org_id = request.query_params.get("org_id")
        project_id = request.query_params.get("project_id")

        if not org_id:
            return Response({"detail": "Missing required parameter: org_id"}, status=400)

        if not is_member_of_organization(user, org_id):
            return Response({"detail": "Unauthorized for this organization."}, status=403)

        tasks = Task.objects.filter(organization_id=org_id)

        if project_id:
            tasks = tasks.filter(column__board__project_id=project_id)

        tasks = tasks.annotate(date=TruncDate("created_at")).values("date").annotate(
            created_count=Count("id"),
            completed_count=Count("id", filter=Q(completed_at__isnull=False))
        ).order_by("date")

        serializer = BurndownChartSerializer(tasks, many=True)
        return Response(serializer.data)

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import *
from .analytics import *

router = DefaultRouter()
router.register(r'organizations', OrganizationViewSet)
router.register(r'projects', ProjectViewSet)
router.register(r'tasks', TaskViewSet)
router.register(r'labels', LabelViewSet)
router.register(r'boards', BoardViewSet, basename='board')
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'columns', ColumnViewSet, basename='column')
router.register(r'activity-logs', ActivityLogViewSet)



urlpatterns = [
    path('api/', include(router.urls)),
    path('',home, name="home"),
    path("analytics/tasks-completed/", TasksCompletedPerDay.as_view()),
    path("analytics/member-productivity/", MemberProductivity.as_view()),
    path("analytics/missed-deadlines/", MissedDeadlines.as_view()),
    path("analytics/burndown-chart/", BurnDownChart.as_view()),
]


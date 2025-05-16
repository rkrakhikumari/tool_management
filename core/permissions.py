from rest_framework import permissions
from .models import Membership

class IsOrganizationAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return Membership.objects.filter(user=request.user, organization=obj.organization, role='admin').exists()

class IsManagerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return Membership.objects.filter(user=request.user, organization=obj.organization, role__in=['admin', 'manager']).exists()

class IsMember(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return Membership.objects.filter(user=request.user, organization=obj.organization).exists()
    

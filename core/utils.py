from .models import Membership, Organization

from .models import ActivityLog

def log_activity(user, task, action, description):
    ActivityLog.objects.create(
        user=user,
        task=task,
        project=task.column.board.project,
        action=action,
        description=description
    )

def has_role(user, org, role):
    try:
        membership = Membership.objects.get(user=user, organization=org)
        return membership.role == role
    except Membership.DoesNotExist:
        return False

def get_active_organization(request):
    org_id = request.session.get('active_org')
    if not org_id:
        return None
    try:
        return Organization.objects.get(id=org_id)
    except Organization.DoesNotExist:
        return None

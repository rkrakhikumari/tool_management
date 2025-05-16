from django.contrib import admin
from .models import *

admin.site.register(CustomUser)
admin.site.register(Organization)
admin.site.register(Project)
admin.site.register(Board)
admin.site.register(Column)
admin.site.register(Comment)
admin.site.register(Membership)
admin.site.register(ActivityLog)
class TaskAdmin(admin.ModelAdmin):
    filter_horizontal = ('assignees',)  
    
admin.site.register(Task, TaskAdmin)

@admin.register(Label)
class LabelAdmin(admin.ModelAdmin):
    filter_horizontal = ('tasks',)


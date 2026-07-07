from django.contrib import admin
from .models import PipelineStage, Lead, Activity, EmailTemplate, EmailLog, AutomationRule


@admin.register(PipelineStage)
class PipelineStageAdmin(admin.ModelAdmin):
    list_display = ['name', 'order', 'color']
    ordering = ['order']


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = ['name', 'company', 'stage', 'value', 'owner', 'created_at']
    list_filter = ['stage', 'source']
    search_fields = ['name', 'company', 'email']


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ['lead', 'activity_type', 'owner', 'created_at']
    list_filter = ['activity_type']


@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject', 'owner', 'created_at']


@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ['lead', 'subject', 'status', 'sent_at']
    list_filter = ['status']


@admin.register(AutomationRule)
class AutomationRuleAdmin(admin.ModelAdmin):
    list_display = ['name', 'trigger_stage', 'delay_days', 'template', 'is_active']
    list_filter = ['is_active']
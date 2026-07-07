from django.db import models
from django.conf import settings


class PipelineStage(models.Model):
    name = models.CharField(max_length=100)
    order = models.PositiveIntegerField(default=0)
    color = models.CharField(max_length=20, default='#3b82f6')

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.name


class Lead(models.Model):
    SOURCE_CHOICES = [
        ('website', 'Website'),
        ('referral', 'Referral'),
        ('cold_call', 'Cold Call'),
        ('social_media', 'Social Media'),
        ('other', 'Other'),
    ]

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='leads')
    stage = models.ForeignKey(PipelineStage, on_delete=models.SET_NULL, null=True, related_name='leads')

    name = models.CharField(max_length=200)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    company = models.CharField(max_length=200, blank=True)
    source = models.CharField(max_length=20, choices=SOURCE_CHOICES, default='other')
    value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    stage_changed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Activity(models.Model):
    ACTIVITY_TYPES = [
        ('call', 'Call'),
        ('email', 'Email'),
        ('meeting', 'Meeting'),
        ('note', 'Note'),
    ]

    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='activities')
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=20, choices=ACTIVITY_TYPES, default='note')
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.activity_type} - {self.lead.name}"
class EmailTemplate(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='email_templates')
    name = models.CharField(max_length=150)
    subject = models.CharField(max_length=200)
    body = models.TextField(help_text="Use {{ name }} and {{ company }} as placeholders.")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class EmailLog(models.Model):
    STATUS_CHOICES = [
        ('sent', 'Sent'),
        ('failed', 'Failed'),
    ]

    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='email_logs')
    lead = models.ForeignKey(Lead, on_delete=models.CASCADE, related_name='email_logs')
    template = models.ForeignKey(EmailTemplate, on_delete=models.SET_NULL, null=True, blank=True)
    subject = models.CharField(max_length=200)
    body = models.TextField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='sent')
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.subject} -> {self.lead.name}"

class AutomationRule(models.Model):
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='automation_rules')
    name = models.CharField(max_length=150)
    trigger_stage = models.ForeignKey(PipelineStage, on_delete=models.CASCADE, related_name='automation_rules')
    delay_days = models.PositiveIntegerField(default=2, help_text="Days a lead must sit in this stage before the email sends.")
    template = models.ForeignKey(EmailTemplate, on_delete=models.CASCADE)
    is_active = models.BooleanField(default=True)
    triggered_leads = models.ManyToManyField(Lead, blank=True, related_name='triggered_rules')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
import json
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_protect
from django.db.models import Sum
from .models import Lead, PipelineStage
from django.template import Template, Context
from django.core.mail import send_mail
from .models import EmailTemplate, EmailLog
from .models import AutomationRule

def run_automation_check(user):
    from django.utils import timezone
    from datetime import timedelta

    rules = AutomationRule.objects.filter(owner=user, is_active=True)
    sent_count = 0

    for rule in rules:
        cutoff = timezone.now() - timedelta(days=rule.delay_days)
        matching_leads = Lead.objects.filter(
            owner=user,
            stage=rule.trigger_stage,
            stage_changed_at__lte=cutoff,
        ).exclude(id__in=rule.triggered_leads.values_list('id', flat=True))

        for lead in matching_leads:
            rendered_subject = Template(rule.template.subject).render(Context({'name': lead.name, 'company': lead.company}))
            rendered_body = Template(rule.template.body).render(Context({'name': lead.name, 'company': lead.company}))

            status = 'sent'
            try:
                send_mail(
                    subject=rendered_subject,
                    message=rendered_body,
                    from_email=None,
                    recipient_list=[lead.email] if lead.email else ['no-email@example.com'],
                    fail_silently=False,
                )
            except Exception:
                status = 'failed'

            EmailLog.objects.create(
                owner=user,
                lead=lead,
                template=rule.template,
                subject=rendered_subject,
                body=rendered_body,
                status=status,
            )
            rule.triggered_leads.add(lead)
            sent_count += 1

    return sent_count

@login_required
def pipeline_view(request):
    stages = PipelineStage.objects.all()
    leads = Lead.objects.filter(owner=request.user).select_related('stage')

    columns = []
    for stage in stages:
        stage_leads = leads.filter(stage=stage)
        columns.append({
            'stage': stage,
            'leads': stage_leads,
            'count': stage_leads.count(),
            'total_value': stage_leads.aggregate(total=Sum('value'))['total'] or 0,
        })

    context = {
        'active_nav': 'pipeline',
        'page_title': 'Pipeline',
        'columns': columns,
        'email_templates': EmailTemplate.objects.filter(owner=request.user),
    }
    return render(request, 'leads/pipeline.html', context)


@login_required
@csrf_protect
def update_lead_stage(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        lead_id = data.get('lead_id')
        stage_id = data.get('stage_id')
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Invalid request body'}, status=400)

    lead = Lead.objects.filter(id=lead_id, owner=request.user).first()
    if not lead:
        return JsonResponse({'error': 'Lead not found'}, status=404)

    stage = PipelineStage.objects.filter(id=stage_id).first()
    if not stage:
        return JsonResponse({'error': 'Stage not found'}, status=404)

    if lead.stage_id != stage.id:
        from django.utils import timezone
        lead.stage = stage
        lead.stage_changed_at = timezone.now()
        lead.save()
    else:
        lead.stage = stage
        lead.save()

    return JsonResponse({'success': True})

@login_required
@csrf_protect
def send_lead_email(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        lead_id = data.get('lead_id')
        template_id = data.get('template_id')
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Invalid request body'}, status=400)

    lead = Lead.objects.filter(id=lead_id, owner=request.user).first()
    if not lead:
        return JsonResponse({'error': 'Lead not found'}, status=404)

    template = EmailTemplate.objects.filter(id=template_id, owner=request.user).first()
    if not template:
        return JsonResponse({'error': 'Template not found'}, status=404)

    rendered_subject = Template(template.subject).render(Context({'name': lead.name, 'company': lead.company}))
    rendered_body = Template(template.body).render(Context({'name': lead.name, 'company': lead.company}))

    status = 'sent'
    try:
        send_mail(
            subject=rendered_subject,
            message=rendered_body,
            from_email=None,
            recipient_list=[lead.email] if lead.email else ['no-email@example.com'],
            fail_silently=False,
        )
    except Exception:
        status = 'failed'

    EmailLog.objects.create(
        owner=request.user,
        lead=lead,
        template=template,
        subject=rendered_subject,
        body=rendered_body,
        status=status,
    )

    return JsonResponse({'success': True, 'status': status})

@login_required
def email_automation_view(request):
    sent_count = run_automation_check(request.user)

    templates = EmailTemplate.objects.filter(owner=request.user)
    rules = AutomationRule.objects.filter(owner=request.user).select_related('trigger_stage', 'template')
    logs = EmailLog.objects.filter(owner=request.user).select_related('lead')[:15]
    stages = PipelineStage.objects.all()

    context = {
        'active_nav': 'email',
        'page_title': 'Email Automation',
        'templates': templates,
        'rules': rules,
        'logs': logs,
        'stages': stages,
        'sent_count': sent_count,
    }
    return render(request, 'leads/email_automation.html', context)


@login_required
@csrf_protect
def create_template(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    name = request.POST.get('name', '').strip()
    subject = request.POST.get('subject', '').strip()
    body = request.POST.get('body', '').strip()

    if not name or not subject or not body:
        return JsonResponse({'error': 'All fields are required'}, status=400)

    EmailTemplate.objects.create(owner=request.user, name=name, subject=subject, body=body)
    return JsonResponse({'success': True})


@login_required
@csrf_protect
def create_rule(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    name = request.POST.get('name', '').strip()
    stage_id = request.POST.get('trigger_stage')
    template_id = request.POST.get('template')
    delay_days = request.POST.get('delay_days', 2)

    stage = PipelineStage.objects.filter(id=stage_id).first()
    template = EmailTemplate.objects.filter(id=template_id, owner=request.user).first()

    if not name or not stage or not template:
        return JsonResponse({'error': 'All fields are required'}, status=400)

    AutomationRule.objects.create(
        owner=request.user,
        name=name,
        trigger_stage=stage,
        template=template,
        delay_days=delay_days,
    )
    return JsonResponse({'success': True})


@login_required
@csrf_protect
def toggle_rule(request, rule_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    rule = AutomationRule.objects.filter(id=rule_id, owner=request.user).first()
    if not rule:
        return JsonResponse({'error': 'Not found'}, status=404)

    rule.is_active = not rule.is_active
    rule.save()
    return JsonResponse({'success': True, 'is_active': rule.is_active})
import json
import os
from groq import Groq
import calendar
from datetime import date
from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_protect
from django.db.models import Sum, Count
from .forms import SignupForm
from leads.models import Lead, PipelineStage, Activity
from django.db.models import Count, Avg
from datetime import date, timedelta


def signup_view(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('dashboard')
    else:
        form = SignupForm()

    return render(request, 'accounts/signup.html', {'form': form})


@login_required
def dashboard_view(request):
    leads = Lead.objects.filter(owner=request.user)
    total_leads = leads.count()
    pipeline_value = leads.exclude(stage__name='Lost').aggregate(total=Sum('value'))['total'] or 0
    deals_won = leads.filter(stage__name='Won').count()
    conversion_rate = round((deals_won / total_leads) * 100, 1) if total_leads else 0

    stages = PipelineStage.objects.all()
    stage_labels = [s.name for s in stages]
    stage_counts = [leads.filter(stage=s).count() for s in stages]

    top_leads = leads.order_by('-value')[:5]

    recent_activities = (
        Activity.objects.filter(owner=request.user)
        .select_related('lead')
        .order_by('-created_at')[:6]
    )

    source_choices = dict(Lead.SOURCE_CHOICES)
    source_data = leads.values('source').annotate(count=Count('id')).order_by('-count')
    source_labels = [source_choices.get(item['source'], item['source']) for item in source_data]
    source_counts = [item['count'] for item in source_data]

    today = date.today()
    try:
        year = int(request.GET.get('year', today.year))
        month = int(request.GET.get('month', today.month))
    except ValueError:
        year, month = today.year, today.month

    cal = calendar.Calendar(firstweekday=6)
    month_days = cal.monthdayscalendar(year, month)

    leads_this_month = leads.filter(created_at__year=year, created_at__month=month)
    leads_by_day = {}
    for lead in leads_this_month:
        day = lead.created_at.day
        leads_by_day[day] = leads_by_day.get(day, 0) + 1

    calendar_weeks = []
    for week in month_days:
        week_data = []
        for day in week:
            if day == 0:
                week_data.append(None)
            else:
                week_data.append({
                    'day': day,
                    'count': leads_by_day.get(day, 0),
                    'is_today': day == today.day and month == today.month and year == today.year,
                })
        calendar_weeks.append(week_data)

    prev_month, prev_year = month - 1, year
    if prev_month == 0:
        prev_month, prev_year = 12, year - 1

    next_month, next_year = month + 1, year
    if next_month == 13:
        next_month, next_year = 1, year + 1

    context = {
        'active_nav': 'dashboard',
        'page_title': 'Dashboard',
        'total_leads': total_leads,
        'pipeline_value': pipeline_value,
        'deals_won': deals_won,
        'conversion_rate': conversion_rate,
        'stage_labels': stage_labels,
        'stage_counts': stage_counts,
        'top_leads': top_leads,
        'recent_activities': recent_activities,
        'source_labels': source_labels,
        'source_counts': source_counts,
        'calendar_weeks': calendar_weeks,
        'month_name': calendar.month_name[month],
        'year': year,
        'prev_month': prev_month,
        'prev_year': prev_year,
        'next_month': next_month,
        'next_year': next_year,
    }
    return render(request, 'accounts/dashboard.html', context)

@login_required
def analytics_view(request):
    from django.db.models.functions import TruncMonth
    leads = Lead.objects.filter(owner=request.user)

    total_leads = leads.count()
    won_leads = leads.filter(stage__name='Won')
    deals_won = won_leads.count()
    total_revenue = won_leads.aggregate(total=Sum('value'))['total'] or 0
    avg_deal_size = won_leads.aggregate(avg=Avg('value'))['avg'] or 0
    conversion_rate = round((deals_won / total_leads) * 100, 1) if total_leads else 0

    monthly_revenue = (
        won_leads
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total=Sum('value'), count=Count('id'))
        .order_by('month')
    )

    revenue_labels = [item['month'].strftime('%b %Y') for item in monthly_revenue]
    revenue_data = [float(item['total']) for item in monthly_revenue]
    won_counts = [item['count'] for item in monthly_revenue]

    stages = PipelineStage.objects.all()
    funnel_data = []
    for stage in stages:
        count = leads.filter(stage=stage).count()
        funnel_data.append({
            'name': stage.name,
            'count': count,
            'color': stage.color,
        })

    source_choices = dict(Lead.SOURCE_CHOICES)
    source_stats = []
    for source_key, source_label in Lead.SOURCE_CHOICES:
        source_leads = leads.filter(source=source_key)
        source_total = source_leads.count()
        source_won = source_leads.filter(stage__name='Won').count()
        source_value = source_leads.filter(stage__name='Won').aggregate(total=Sum('value'))['total'] or 0
        source_rate = round((source_won / source_total) * 100, 1) if source_total else 0
        if source_total > 0:
            source_stats.append({
                'label': source_label,
                'total': source_total,
                'won': source_won,
                'value': source_value,
                'rate': source_rate,
            })

    source_stats.sort(key=lambda x: x['rate'], reverse=True)

    best_source = source_stats[0]['label'] if source_stats else 'N/A'

    context = {
        'active_nav': 'analytics',
        'page_title': 'Analytics',
        'total_leads': total_leads,
        'deals_won': deals_won,
        'total_revenue': total_revenue,
        'avg_deal_size': avg_deal_size,
        'conversion_rate': conversion_rate,
        'best_source': best_source,
        'revenue_labels': revenue_labels,
        'revenue_data': revenue_data,
        'won_counts': won_counts,
        'funnel_data': funnel_data,
        'source_stats': source_stats,
    }
    return render(request, 'accounts/analytics.html', context)

@login_required
def ai_assistant_view(request):
    leads = Lead.objects.filter(owner=request.user)
    total_leads = leads.count()
    pipeline_value = leads.exclude(stage__name='Lost').aggregate(total=Sum('value'))['total'] or 0
    deals_won = leads.filter(stage__name='Won').count()
    top_leads = leads.order_by('-value')[:5]

    stages = PipelineStage.objects.all()
    stage_summary = []
    for stage in stages:
        count = leads.filter(stage=stage).count()
        stage_summary.append(f"{stage.name}: {count} leads")

    context = {
        'active_nav': 'ai_assistant',
        'page_title': 'AI Assistant',
        'total_leads': total_leads,
        'pipeline_value': pipeline_value,
        'deals_won': deals_won,
        'top_leads': top_leads,
        'stage_summary': ', '.join(stage_summary),
    }
    return render(request, 'accounts/ai_assistant.html', context)


@login_required
@csrf_protect
def ai_chat(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)

    try:
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        history = data.get('history', [])
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Invalid request'}, status=400)

    if not user_message:
        return JsonResponse({'error': 'Empty message'}, status=400)

    leads = Lead.objects.filter(owner=request.user)
    total_leads = leads.count()
    pipeline_value = leads.exclude(stage__name='Lost').aggregate(total=Sum('value'))['total'] or 0
    deals_won = leads.filter(stage__name='Won').count()
    conversion_rate = round((deals_won / total_leads) * 100, 1) if total_leads else 0

    stages = PipelineStage.objects.all()
    stage_lines = []
    for stage in stages:
        count = leads.filter(stage=stage).count()
        stage_lines.append(f"  - {stage.name}: {count} leads")

    top_leads = leads.order_by('-value')[:5]
    top_lead_lines = [f"  - {l.name} ({l.company}): ${l.value}" for l in top_leads]

    system_prompt = f"""You are an expert AI sales assistant built into AgenticFlow, a CRM platform. You help sales professionals manage their pipeline, draft emails, and close more deals.

Here is the current pipeline data for this user:
- Total leads: {total_leads}
- Pipeline value: ${pipeline_value}
- Deals won: {deals_won}
- Conversion rate: {conversion_rate}%

Leads by stage:
{chr(10).join(stage_lines)}

Top opportunities:
{chr(10).join(top_lead_lines)}

Be concise, practical, and specific. When drafting emails, use a professional but warm tone. When giving sales advice, base it on the actual pipeline data above. Never make up lead names or numbers that aren't in the data provided."""

    messages = [{'role': 'system', 'content': system_prompt}]

    for msg in history[-10:]:
        if msg.get('role') in ('user', 'assistant') and msg.get('content'):
            messages.append({'role': msg['role'], 'content': msg['content']})

    messages.append({'role': 'user', 'content': user_message})

    try:
        client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        response = client.chat.completions.create(
            model='llama-3.1-8b-instant',
            messages=messages,
            max_tokens=1024,
            temperature=0.7,
        )
        reply = response.choices[0].message.content
        return JsonResponse({'success': True, 'reply': reply})

    except Exception as e:
        print(f"GROQ ERROR: {str(e)}")
        return JsonResponse({'error': f'AI error: {str(e)}'}, status=500)
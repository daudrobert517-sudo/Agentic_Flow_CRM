from django.urls import path
from . import views

urlpatterns = [
    path('pipeline/', views.pipeline_view, name='pipeline'),
    path('update-stage/', views.update_lead_stage, name='update_lead_stage'),
    path('send-email/', views.send_lead_email, name='send_lead_email'),
    path('email-automation/', views.email_automation_view, name='email_automation'),
    path('templates/create/', views.create_template, name='create_template'),
    path('rules/create/', views.create_rule, name='create_rule'),
    path('rules/<int:rule_id>/toggle/', views.toggle_rule, name='toggle_rule'),
]
"""
URL Configuration for AI Agent API
===================================
Maps endpoints to view functions.
"""
from django.contrib import admin
from django.urls import path, include
from . import views
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

app_name = 'agent'

urlpatterns = [
    # Main agent endpoints
    path('analyze-event/', views.analyze_event, name='analyze_event'),
    path('decide-action/', views.decide_action, name='decide_action'),
    path('execute-action/', views.execute_action, name='execute_action'),
    
    # Utility endpoints
    path('validate-payload/', views.validate_payload, name='validate_payload'),
    path('health/', views.health_check, name='health_check'),
]
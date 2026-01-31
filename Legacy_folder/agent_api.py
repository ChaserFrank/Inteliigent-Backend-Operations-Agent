"""
Django REST API for AI Agent Decision Execution
================================================
Production-ready API endpoint that receives decisions from AI agents
and executes appropriate backend actions.

Installation Requirements:
    pip install djangorestframework django-ratelimit
"""

import logging
from typing import Dict, Any
from datetime import datetime

from django.core.mail import send_mail
from django.conf import settings
from rest_framework import serializers, status
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator


# ============================================================================
# Logger Configuration
# ============================================================================

logger = logging.getLogger(__name__)


# ============================================================================
# Serializers
# ============================================================================

class AgentDecisionSerializer(serializers.Serializer):
    """
    Serializer for AI agent decision payloads.
    
    Validates incoming decision data and ensures all required fields are present.
    """
    action = serializers.ChoiceField(
        choices=['log_only', 'notify_admin', 'trigger_workflow', 'escalate'],
        required=True,
        help_text="Action to execute based on AI agent decision"
    )
    priority = serializers.IntegerField(
        min_value=1,
        max_value=5,
        required=True,
        help_text="Priority level (1=highest, 5=lowest)"
    )
    event_type = serializers.CharField(
        max_length=100,
        required=True,
        help_text="Type of event that triggered this decision"
    )
    severity = serializers.ChoiceField(
        choices=['low', 'medium', 'high', 'critical'],
        required=True,
        help_text="Severity level of the event"
    )
    message = serializers.CharField(
        required=True,
        help_text="Event message or description"
    )
    context = serializers.JSONField(
        required=False,
        default=dict,
        help_text="Additional context data"
    )
    metadata = serializers.JSONField(
        required=False,
        default=dict,
        help_text="Decision metadata from AI agent"
    )
    
    def validate_action(self, value):
        """Validate action field"""
        valid_actions = ['log_only', 'notify_admin', 'trigger_workflow', 'escalate']
        if value not in valid_actions:
            raise serializers.ValidationError(
                f"Invalid action. Must be one of: {', '.join(valid_actions)}"
            )
        return value
    
    def validate_priority(self, value):
        """Validate priority is within acceptable range"""
        if not 1 <= value <= 5:
            raise serializers.ValidationError("Priority must be between 1 and 5")
        return value


class ActionResponseSerializer(serializers.Serializer):
    """
    Serializer for action execution responses.
    
    Provides structured response data for API consumers.
    """
    success = serializers.BooleanField(
        help_text="Whether the action was executed successfully"
    )
    action = serializers.CharField(
        help_text="Action that was executed"
    )
    message = serializers.CharField(
        help_text="Human-readable result message"
    )
    execution_time = serializers.DateTimeField(
        help_text="Timestamp of execution"
    )
    details = serializers.JSONField(
        required=False,
        help_text="Additional execution details"
    )


# ============================================================================
# Action Executors
# ============================================================================

class ActionExecutor:
    """
    Executes backend actions based on AI agent decisions.
    
    Handles logging, notifications, workflow triggers, and escalations.
    """
    
    def __init__(self):
        self.execution_time = datetime.utcnow()
    
    def execute(self, decision_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the appropriate action based on decision data.
        
        Args:
            decision_data: Validated decision data from serializer
            
        Returns:
            Dictionary with execution results
        """
        action = decision_data['action']
        
        # Route to appropriate handler
        handlers = {
            'log_only': self._handle_log_only,
            'notify_admin': self._handle_notify_admin,
            'trigger_workflow': self._handle_trigger_workflow,
            'escalate': self._handle_escalate,
        }
        
        handler = handlers.get(action)
        if not handler:
            return self._error_response(f"Unknown action: {action}")
        
        try:
            return handler(decision_data)
        except Exception as e:
            logger.error(f"Error executing action {action}: {str(e)}", exc_info=True)
            return self._error_response(f"Failed to execute action: {str(e)}")
    
    def _handle_log_only(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle log_only action - record event for monitoring.
        
        Args:
            data: Decision data
            
        Returns:
            Execution result
        """
        log_level = self._get_log_level(data['severity'])
        log_message = (
            f"[AI Agent] {data['event_type']} - {data['message']} "
            f"(Priority: {data['priority']}, Severity: {data['severity']})"
        )
        
        # Log at appropriate level
        logger.log(log_level, log_message, extra={
            'event_type': data['event_type'],
            'severity': data['severity'],
            'priority': data['priority'],
            'context': data.get('context', {}),
            'metadata': data.get('metadata', {})
        })
        
        return {
            'success': True,
            'action': 'log_only',
            'message': 'Event logged successfully',
            'execution_time': self.execution_time.isoformat(),
            'details': {
                'log_level': logging.getLevelName(log_level),
                'event_type': data['event_type']
            }
        }
    
    def _handle_notify_admin(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle notify_admin action - send email notification to administrators.
        
        Args:
            data: Decision data
            
        Returns:
            Execution result
        """
        # Log the event first
        self._handle_log_only(data)
        
        # Prepare email
        subject = f"[AI Agent Alert] {data['event_type']} - {data['severity'].upper()}"
        message = self._build_notification_message(data)
        
        # Get admin emails from settings
        admin_emails = self._get_admin_emails()
        
        if not admin_emails:
            logger.warning("No admin emails configured for notifications")
            return {
                'success': False,
                'action': 'notify_admin',
                'message': 'No admin emails configured',
                'execution_time': self.execution_time.isoformat()
            }
        
        try:
            # Send email notification
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=admin_emails,
                fail_silently=False,
            )
            
            return {
                'success': True,
                'action': 'notify_admin',
                'message': f'Admin notification sent to {len(admin_emails)} recipient(s)',
                'execution_time': self.execution_time.isoformat(),
                'details': {
                    'recipients': len(admin_emails),
                    'subject': subject
                }
            }
        except Exception as e:
            logger.error(f"Failed to send admin notification: {str(e)}")
            return {
                'success': False,
                'action': 'notify_admin',
                'message': f'Failed to send notification: {str(e)}',
                'execution_time': self.execution_time.isoformat()
            }
    
    def _handle_trigger_workflow(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle trigger_workflow action - initiate automated workflow.
        
        Args:
            data: Decision data
            
        Returns:
            Execution result
        """
        # Log the event
        self._handle_log_only(data)
        
        # Determine workflow type
        workflow_type = data.get('metadata', {}).get('workflow_type', 'generic_handler')
        
        # In production, this would trigger actual workflow systems
        # (e.g., Celery tasks, AWS Step Functions, etc.)
        logger.info(
            f"Triggering workflow: {workflow_type}",
            extra={
                'workflow_type': workflow_type,
                'event_type': data['event_type'],
                'priority': data['priority']
            }
        )
        
        # Placeholder for workflow trigger
        # Example: trigger_celery_task.delay(workflow_type, data)
        
        return {
            'success': True,
            'action': 'trigger_workflow',
            'message': f'Workflow triggered: {workflow_type}',
            'execution_time': self.execution_time.isoformat(),
            'details': {
                'workflow_type': workflow_type,
                'event_type': data['event_type']
            }
        }
    
    def _handle_escalate(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle escalate action - immediate critical response.
        
        Args:
            data: Decision data
            
        Returns:
            Execution result
        """
        # Log at critical level
        logger.critical(
            f"[ESCALATION] {data['event_type']} - {data['message']}",
            extra=data
        )
        
        # Send urgent notification
        notification_result = self._handle_notify_admin(data)
        
        # Trigger emergency workflow
        workflow_result = self._handle_trigger_workflow(data)
        
        # In production, might also:
        # - Send SMS alerts
        # - Create PagerDuty incidents
        # - Post to Slack emergency channel
        # - Trigger on-call rotation
        
        return {
            'success': True,
            'action': 'escalate',
            'message': 'Critical escalation initiated',
            'execution_time': self.execution_time.isoformat(),
            'details': {
                'notification_sent': notification_result['success'],
                'workflow_triggered': workflow_result['success'],
                'escalation_level': 'critical',
                'event_type': data['event_type']
            }
        }
    
    def _build_notification_message(self, data: Dict[str, Any]) -> str:
        """Build email notification message"""
        return f"""
AI Agent Alert
==============

Event Type: {data['event_type']}
Severity: {data['severity'].upper()}
Priority: {data['priority']}

Message:
{data['message']}

Context:
{self._format_dict(data.get('context', {}))}

Metadata:
{self._format_dict(data.get('metadata', {}))}

Timestamp: {self.execution_time.isoformat()}

---
This is an automated notification from the AI Backend Operations Agent.
        """.strip()
    
    def _format_dict(self, d: Dict[str, Any]) -> str:
        """Format dictionary for email display"""
        if not d:
            return "None"
        return "\n".join(f"  {k}: {v}" for k, v in d.items())
    
    def _get_log_level(self, severity: str) -> int:
        """Map severity to logging level"""
        mapping = {
            'low': logging.INFO,
            'medium': logging.WARNING,
            'high': logging.ERROR,
            'critical': logging.CRITICAL,
        }
        return mapping.get(severity, logging.INFO)
    
    def _get_admin_emails(self) -> list:
        """Get admin email addresses from settings"""
        # Try to get from settings
        if hasattr(settings, 'ADMIN_NOTIFICATION_EMAILS'):
            return settings.ADMIN_NOTIFICATION_EMAILS
        
        # Fallback to ADMINS setting
        if hasattr(settings, 'ADMINS'):
            return [email for name, email in settings.ADMINS]
        
        return []
    
    def _error_response(self, error_message: str) -> Dict[str, Any]:
        """Generate error response"""
        return {
            'success': False,
            'action': 'error',
            'message': error_message,
            'execution_time': self.execution_time.isoformat()
        }


# ============================================================================
# Rate Limiting
# ============================================================================

class AgentDecisionRateThrottle(UserRateThrottle):
    """Custom rate throttle for agent decision endpoint"""
    rate = '100/hour'  # Adjust based on your needs


# ============================================================================
# API View
# ============================================================================

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AgentDecisionRateThrottle])
def execute_agent_decision(request):
    """
    Execute an action based on AI agent decision.
    
    This endpoint receives decisions from AI agents and executes
    the appropriate backend actions (logging, notifications, workflows, etc.).
    
    **Authentication Required**: Yes (Token/Session)
    
    **Rate Limit**: 100 requests per hour per user
    
    **Request Body**:
    ```json
    {
        "action": "notify_admin",
        "priority": 2,
        "event_type": "security_issue",
        "severity": "high",
        "message": "Unauthorized access attempt detected",
        "context": {
            "ip": "192.168.1.100",
            "endpoint": "/admin/users"
        },
        "metadata": {
            "confidence": 0.95
        }
    }
    ```
    
    **Response**:
    ```json
    {
        "success": true,
        "action": "notify_admin",
        "message": "Admin notification sent to 2 recipient(s)",
        "execution_time": "2024-01-31T12:00:00.000000",
        "details": {
            "recipients": 2,
            "subject": "[AI Agent Alert] security_issue - HIGH"
        }
    }
    ```
    
    **Status Codes**:
    - 200: Action executed successfully
    - 400: Invalid request data
    - 401: Authentication required
    - 429: Rate limit exceeded
    - 500: Server error during execution
    """
    # Validate request data
    serializer = AgentDecisionSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {
                'success': False,
                'message': 'Invalid request data',
                'errors': serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Execute action
    executor = ActionExecutor()
    result = executor.execute(serializer.validated_data)
    
    # Determine response status
    response_status = (
        status.HTTP_200_OK if result['success']
        else status.HTTP_500_INTERNAL_SERVER_ERROR
    )
    
    return Response(result, status=response_status)


# ============================================================================
# URL Configuration
# ============================================================================

"""
Add to your Django urls.py:

from django.urls import path
from .agent_api import execute_agent_decision

urlpatterns = [
    path('api/agent/execute-decision/', execute_agent_decision, name='execute_agent_decision'),
]
"""

# Example urls.py content:
"""
# urls.py
from django.urls import path
from . import agent_api

app_name = 'agent'

urlpatterns = [
    path('execute-decision/', agent_api.execute_agent_decision, name='execute_decision'),
]
"""


# ============================================================================
# Settings Configuration
# ============================================================================

"""
Add to your Django settings.py:

# AI Agent API Settings
ADMIN_NOTIFICATION_EMAILS = [
    'admin@example.com',
    'ops@example.com',
]

# Email Configuration (if not already configured)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@example.com'
EMAIL_HOST_PASSWORD = 'your-password'
DEFAULT_FROM_EMAIL = 'noreply@example.com'

# REST Framework Settings
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_THROTTLE_RATES': {
        'user': '100/hour',
    }
}

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/agent_decisions.log',
            'maxBytes': 1024 * 1024 * 10,  # 10 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'agent_api': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
"""
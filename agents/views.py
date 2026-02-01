"""
Django REST API Views for AI Agent Service
===========================================
Exposes agent service functions over HTTP endpoints.
Hackathon-ready and minimal implementation.
"""

from rest_framework import status, serializers
from drf_spectacular.utils import extend_schema
from .serializers import (
    AnalyzeEventRequestSerializer,
    AgentDecisionResponseSerializer,
    DecideActionRequestSerializer,
    ExecuteActionRequestSerializer,
    ValidatePayloadRequestSerializer,
    HealthResponseSerializer,
)
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.serializers import Serializer, CharField, JSONField, IntegerField, ChoiceField

# Import existing agent modules
from .services.ai_agent_service import AIAgentService
from .services.event_router import EventRouter, AnalyzedEvent, EventType, SeverityLevel
from .services.validation_module import PayloadValidator, FieldSchema, FieldType


# ============================================================================
# Serializers
# ============================================================================

class AnalyzeEventSerializer(Serializer):
    """Serializer for analyze_event endpoint"""
    error_type = CharField(required=True)
    message = CharField(required=True)
    stack_trace = CharField(required=False, allow_blank=True, default="")
    context = JSONField(required=False, default=dict)


class DecideActionSerializer(Serializer):
    """Serializer for decide_action endpoint"""
    event_type = ChoiceField(
        choices=['validation_error', 'system_error', 'security_issue', 'performance_issue', 'ignorable'],
        required=True
    )
    severity = ChoiceField(
        choices=['low', 'medium', 'high', 'critical'],
        required=True
    )
    message = CharField(required=True)
    context = JSONField(required=False, default=dict)


class ExecuteActionSerializer(Serializer):
    """Serializer for execute_action endpoint"""
    action = ChoiceField(
        choices=['log_only', 'notify_admin', 'trigger_workflow', 'escalate'],
        required=True
    )
    priority = IntegerField(min_value=1, max_value=5, required=True)
    event_type = CharField(required=True)
    severity = ChoiceField(
        choices=['low', 'medium', 'high', 'critical'],
        required=True
    )
    message = CharField(required=True)
    context = JSONField(required=False, default=dict)
    metadata = JSONField(required=False, default=dict)


# ============================================================================
# API Views
# ============================================================================

@api_view(['POST'])
def analyze_event(request):
    """
    Analyze an error/event payload and classify it.
    
    POST /agent/analyze-event/
    
    Request Body:
    {
        "error_type": "ValidationError",
        "message": "Invalid email format",
        "stack_trace": "...",
        "context": {"field": "email"}
    }
    
    Response:
    {
        "category": "validation_error",
        "severity": "low",
        "action": "log_only",
        "priority": 5,
        "metadata": {...}
    }
    """
    serializer = AnalyzeEventSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid request data', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Initialize AI agent service and analysis agent
    from .services.ai_agent_service import AnalysisAgent
    
    # Process the event through analysis agent
    try:
        analysis_agent = AnalysisAgent()
        
        # Analyze the event to get category and severity
        analysis_result = analysis_agent.analyze(serializer.validated_data)
        
        # Initialize orchestrator for action decision
        agent_service = AIAgentService()
        decision_result = agent_service.process(serializer.validated_data)
        
        # Build response with proper category and severity from analysis
        response_data = {
            'category': analysis_result.category.value,  # validation_error, system_error, security_issue, ignorable
            'severity': analysis_result.severity.value,  # low, medium, high
            'action': decision_result.get('action'),
            'priority': decision_result.get('priority'),
            'metadata': decision_result.get('metadata', {})
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': 'Analysis failed', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def decide_action(request):
    """
    Decide what action to take based on analyzed event.
    
    POST /agent/decide-action/
    
    Request Body:
    {
        "event_type": "security_issue",
        "severity": "high",
        "message": "Unauthorized access attempt",
        "context": {"ip": "192.168.1.100"}
    }
    
    Response:
    {
        "action": "escalate",
        "priority": 1,
        "reason": "Critical event requiring immediate escalation",
        "metadata": {
            "event_type": "security_issue",
            "severity": "high",
            "requires_immediate_action": true
        }
    }
    """
    serializer = DecideActionSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid request data', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Initialize event router
    router = EventRouter()
    
    try:
        # Create analyzed event
        analyzed_event = AnalyzedEvent(
            event_type=EventType(serializer.validated_data['event_type']),
            severity=SeverityLevel(serializer.validated_data['severity']),
            message=serializer.validated_data['message'],
            context=serializer.validated_data.get('context', {})
        )
        
        # Route the event
        decision = router.route(analyzed_event)
        
        # Return decision
        response_data = {
            'action': decision.action.value,
            'priority': decision.priority,
            'reason': decision.reason,
            'metadata': decision.metadata
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': 'Decision failed', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def execute_action(request):
    """
    Execute a backend action based on decision.
    
    POST /agent/execute-action/
    
    Request Body:
    {
        "action": "notify_admin",
        "priority": 2,
        "event_type": "system_error",
        "severity": "medium",
        "message": "Database connection timeout",
        "context": {"database": "postgres"},
        "metadata": {}
    }
    
    Response:
    {
        "success": true,
        "action": "notify_admin",
        "message": "Action executed successfully",
        "execution_time": "2024-01-31T12:00:00",
        "details": {
            "notifications_sent": 2
        }
    }
    """
    serializer = ExecuteActionSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(
            {'error': 'Invalid request data', 'details': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        from datetime import datetime
        import logging
        
        logger = logging.getLogger(__name__)
        data = serializer.validated_data
        
        # Simulate action execution based on action type
        action = data['action']
        execution_time = datetime.utcnow().isoformat()
        
        if action == 'log_only':
            logger.info(f"[Agent] {data['event_type']} - {data['message']}")
            response_data = {
                'success': True,
                'action': action,
                'message': 'Event logged successfully',
                'execution_time': execution_time,
                'details': {'log_level': 'INFO'}
            }
        
        elif action == 'notify_admin':
            logger.warning(f"[Agent] Admin notification: {data['message']}")
            response_data = {
                'success': True,
                'action': action,
                'message': 'Admin notification sent',
                'execution_time': execution_time,
                'details': {'notifications_sent': 1}
            }
        
        elif action == 'trigger_workflow':
            workflow_type = data.get('metadata', {}).get('workflow_type', 'generic')
            logger.info(f"[Agent] Triggering workflow: {workflow_type}")
            response_data = {
                'success': True,
                'action': action,
                'message': f'Workflow triggered: {workflow_type}',
                'execution_time': execution_time,
                'details': {'workflow_type': workflow_type}
            }
        
        elif action == 'escalate':
            logger.critical(f"[Agent] ESCALATION: {data['message']}")
            response_data = {
                'success': True,
                'action': action,
                'message': 'Critical escalation initiated',
                'execution_time': execution_time,
                'details': {
                    'escalation_level': 'critical',
                    'notifications_sent': 2,
                    'workflow_triggered': True
                }
            }
        
        else:
            response_data = {
                'success': False,
                'action': action,
                'message': f'Unknown action: {action}',
                'execution_time': execution_time
            }
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': 'Execution failed', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
def validate_payload(request):
    """
    Validate an incoming payload against required fields.
    
    POST /agent/validate-payload/
    
    Request Body:
    {
        "payload": {"username": "john", "email": "john@example.com"},
        "required_fields": ["username", "email", "password"]
    }
    
    Response:
    {
        "is_valid": false,
        "missing_fields": ["password"],
        "message": "Missing required fields: password"
    }
    """
    payload = request.data.get('payload', {})
    required_fields = request.data.get('required_fields', [])
    
    if not required_fields:
        return Response(
            {'error': 'required_fields must be provided'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        # Create schema from required fields
        schema = [FieldSchema(name=field, required=True) for field in required_fields]
        validator = PayloadValidator(schema)
        
        # Validate
        result = validator.validate(payload)
        
        response_data = {
            'is_valid': result.is_valid,
            'missing_fields': result.missing_fields,
            'message': result.message
        }
        
        if result.invalid_fields:
            response_data['invalid_fields'] = result.invalid_fields
        
        return Response(response_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': 'Validation failed', 'details': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
def health_check(request):
    """
    Health check endpoint.
    
    GET /agent/health/
    
    Response:
    {
        "status": "healthy",
        "service": "AI Agent Backend Operations",
        "version": "1.0.0"
    }
    """
    return Response({
        'status': 'healthy',
        'service': 'AI Agent Backend Operations',
        'version': '1.0.0',
        'endpoints': [
            '/agent/analyze-event/',
            '/agent/decide-action/',
            '/agent/execute-action/',
            '/agent/validate-payload/',
            '/agent/health/'
        ]
    }, status=status.HTTP_200_OK)

@extend_schema(
    request=AnalyzeEventRequestSerializer,
    responses=AgentDecisionResponseSerializer,
    tags=["IBOA"],
    summary="Analyze backend event and return action decision",
)
@api_view(["POST"])
def analyze_event(request):
    ...
@extend_schema(request=DecideActionRequestSerializer, responses=AgentDecisionResponseSerializer)
@api_view(["POST"])
def decide_action(request): ...

@extend_schema(request=ExecuteActionRequestSerializer, responses=AgentDecisionResponseSerializer)
@api_view(["POST"])
def execute_action(request): ...

@extend_schema(responses=HealthResponseSerializer)
@api_view(["GET"])
def health_check(request): ...

@extend_schema(request=ValidatePayloadRequestSerializer, responses={"200": {"type": "object"}})
@api_view(["POST"])
def validate_payload(request): ...

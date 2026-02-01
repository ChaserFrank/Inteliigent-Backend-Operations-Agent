"""
Django REST API Views for IBOA (Intelligent Backend Operations Agent)
====================================================================
Fixes:
- Removes duplicate placeholder view definitions that returned `...` (None).
- Uses your real DRF serializers from agents/serializers.py for schema + validation.
- Ensures every endpoint ALWAYS returns a DRF Response.
"""

import logging
from datetime import datetime

from django.views.decorators.csrf import csrf_exempt
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from .serializers import (
    AnalyzeEventRequestSerializer,
    AgentDecisionResponseSerializer,
    DecideActionRequestSerializer,
    ExecuteActionRequestSerializer,
    ValidatePayloadRequestSerializer,
    HealthResponseSerializer,
)

from .services.ai_agent_service import AIAgentService, AnalysisAgent

logger = logging.getLogger(__name__)


# -----------------------------------------------------------------------------
# POST /analyze-event/
# -----------------------------------------------------------------------------
@extend_schema(
    request=AnalyzeEventRequestSerializer,
    responses=AgentDecisionResponseSerializer,
    tags=["IBOA"],
    summary="Analyze backend event and return action decision",
)
@api_view(["POST"])
@csrf_exempt
def analyze_event(request):
    serializer = AnalyzeEventRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"error": "Invalid request data", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        payload = serializer.validated_data

        analysis_agent = AnalysisAgent()
        analysis_result = analysis_agent.analyze(payload)

        agent_service = AIAgentService()
        decision_result = agent_service.process(payload)  # returns dict: action/priority/metadata

        response_data = {
            "category": analysis_result.category.value,
            "severity": analysis_result.severity.value,
            "action": decision_result.get("action"),
            "priority": decision_result.get("priority"),
            "metadata": decision_result.get("metadata", {}),
        }
        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.exception("analyze_event failed")
        return Response(
            {"error": "Analysis failed", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# -----------------------------------------------------------------------------
# POST /decide-action/
# -----------------------------------------------------------------------------
@extend_schema(
    request=DecideActionRequestSerializer,
    responses=AgentDecisionResponseSerializer,
    tags=["IBOA"],
    summary="Decide action from category/severity",
)
@api_view(["POST"])
@csrf_exempt
def decide_action(request):
    """
    Uses AIAgentService on a minimal payload.
    Your DecideActionRequestSerializer only has: category, severity, context.
    """
    serializer = DecideActionRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"error": "Invalid request data", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        data = serializer.validated_data
        payload = {
            "error_type": data.get("category", "unknown"),
            "message": f"Decision request: category={data.get('category')} severity={data.get('severity')}",
            "context": data.get("context", {}) or {},
        }

        analysis_agent = AnalysisAgent()
        analysis_result = analysis_agent.analyze(payload)

        agent_service = AIAgentService()
        decision_result = agent_service.process(payload)

        response_data = {
            "category": analysis_result.category.value,
            "severity": analysis_result.severity.value,
            "action": decision_result.get("action"),
            "priority": decision_result.get("priority"),
            "metadata": decision_result.get("metadata", {}),
        }
        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.exception("decide_action failed")
        return Response(
            {"error": "Decision failed", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# -----------------------------------------------------------------------------
# POST /execute-action/
# -----------------------------------------------------------------------------
@extend_schema(
    request=ExecuteActionRequestSerializer,
    responses={"200": {"type": "object"}},
    tags=["IBOA"],
    summary="Execute an action (hackathon simulation)",
)
@api_view(["POST"])
@csrf_exempt
def execute_action(request):
    """
    Your ExecuteActionRequestSerializer only has: action, metadata.
    This endpoint simulates execution (log/notify/workflow/escalate) for demo.
    """
    serializer = ExecuteActionRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"error": "Invalid request data", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        data = serializer.validated_data
        action = data.get("action")
        metadata = data.get("metadata", {}) or {}
        execution_time = datetime.utcnow().isoformat()

        if action == "log_only":
            logger.info("[IBOA] log_only: %s", metadata)
            response_data = {
                "success": True,
                "action": action,
                "message": "Event logged successfully",
                "execution_time": execution_time,
                "details": {"log_level": "INFO"},
            }

        elif action == "notify_admin":
            logger.warning("[IBOA] notify_admin: %s", metadata)
            response_data = {
                "success": True,
                "action": action,
                "message": "Admin notification sent",
                "execution_time": execution_time,
                "details": {"notifications_sent": 1},
            }

        elif action == "trigger_workflow":
            workflow_type = metadata.get("workflow_type", "generic")
            logger.info("[IBOA] trigger_workflow: %s", workflow_type)
            response_data = {
                "success": True,
                "action": action,
                "message": f"Workflow triggered: {workflow_type}",
                "execution_time": execution_time,
                "details": {"workflow_type": workflow_type},
            }

        elif action == "escalate":
            logger.critical("[IBOA] escalate: %s", metadata)
            response_data = {
                "success": True,
                "action": action,
                "message": "Critical escalation initiated",
                "execution_time": execution_time,
                "details": {"escalation_level": "critical", "workflow_triggered": True},
            }

        else:
            response_data = {
                "success": False,
                "action": action,
                "message": f"Unknown action: {action}",
                "execution_time": execution_time,
            }

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.exception("execute_action failed")
        return Response(
            {"error": "Execution failed", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# -----------------------------------------------------------------------------
# POST /validate-payload/
# -----------------------------------------------------------------------------
@extend_schema(
    request=ValidatePayloadRequestSerializer,
    responses={"200": {"type": "object"}},
    tags=["IBOA"],
    summary="Validate payload",
)
@api_view(["POST"])
@csrf_exempt
def validate_payload(request):
    """
    Your ValidatePayloadRequestSerializer only has: payload.
    We'll validate it's present and return basic info.
    """
    serializer = ValidatePayloadRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(
            {"error": "Invalid request data", "details": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        payload = serializer.validated_data.get("payload") or {}
        # Minimal demo validation: payload must not be empty
        is_valid = bool(payload)
        return Response(
            {
                "is_valid": is_valid,
                "message": "Payload received" if is_valid else "Payload is empty",
            },
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        logger.exception("validate_payload failed")
        return Response(
            {"error": "Validation failed", "details": str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# -----------------------------------------------------------------------------
# GET /health/
# -----------------------------------------------------------------------------
@extend_schema(
    responses=HealthResponseSerializer,
    tags=["IBOA"],
    summary="Health check",
)
@api_view(["GET"])
def health_check(request):
    return Response({"status": "healthy"}, status=status.HTTP_200_OK)

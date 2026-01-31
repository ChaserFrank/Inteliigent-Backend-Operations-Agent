"""
Event Router for AI Backend Operations Agent
=============================================
Routes analyzed events to appropriate actions based on type and severity.
Uses a simple, readable rule-based approach.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


# ============================================================================
# Type Definitions
# ============================================================================

class EventType(Enum):
    """Event classification types"""
    VALIDATION_ERROR = "validation_error"
    SYSTEM_ERROR = "system_error"
    SECURITY_ISSUE = "security_issue"
    PERFORMANCE_ISSUE = "performance_issue"
    IGNORABLE = "ignorable"


class SeverityLevel(Enum):
    """Severity levels for events"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ActionType(Enum):
    """Available actions for event handling"""
    LOG_ONLY = "log_only"
    NOTIFY_ADMIN = "notify_admin"
    TRIGGER_WORKFLOW = "trigger_workflow"
    ESCALATE = "escalate"


@dataclass
class AnalyzedEvent:
    """Analyzed event with classification"""
    event_type: EventType
    severity: SeverityLevel
    message: str
    context: Dict[str, Any]
    timestamp: Optional[int] = None


@dataclass
class RoutingDecision:
    """Decision made by the router"""
    action: ActionType
    priority: int  # 1 (highest) to 5 (lowest)
    reason: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            "action": self.action.value,
            "priority": self.priority,
            "reason": self.reason,
            "metadata": self.metadata
        }


# ============================================================================
# Event Router
# ============================================================================

class EventRouter:
    """
    Routes analyzed events to appropriate actions.
    
    Uses a simple, readable rule-based approach to determine
    the best action for each event based on type and severity.
    """
    
    def __init__(self, custom_rules: Optional[Dict[str, Any]] = None):
        """
        Initialize the event router.
        
        Args:
            custom_rules: Optional custom routing rules to override defaults
        """
        self.custom_rules = custom_rules or {}
        self._initialize_routing_rules()
    
    def _initialize_routing_rules(self):
        """
        Initialize default routing rules.
        
        Rules are organized by event type and severity level.
        Each rule specifies the action to take and priority.
        """
        self.routing_rules = {
            # Security issues - always high priority
            EventType.SECURITY_ISSUE: {
                SeverityLevel.CRITICAL: (ActionType.ESCALATE, 1),
                SeverityLevel.HIGH: (ActionType.ESCALATE, 1),
                SeverityLevel.MEDIUM: (ActionType.NOTIFY_ADMIN, 2),
                SeverityLevel.LOW: (ActionType.NOTIFY_ADMIN, 3),
            },
            
            # System errors - priority based on severity
            EventType.SYSTEM_ERROR: {
                SeverityLevel.CRITICAL: (ActionType.ESCALATE, 1),
                SeverityLevel.HIGH: (ActionType.TRIGGER_WORKFLOW, 2),
                SeverityLevel.MEDIUM: (ActionType.NOTIFY_ADMIN, 3),
                SeverityLevel.LOW: (ActionType.LOG_ONLY, 4),
            },
            
            # Performance issues - trigger workflows or notify
            EventType.PERFORMANCE_ISSUE: {
                SeverityLevel.CRITICAL: (ActionType.TRIGGER_WORKFLOW, 2),
                SeverityLevel.HIGH: (ActionType.TRIGGER_WORKFLOW, 2),
                SeverityLevel.MEDIUM: (ActionType.NOTIFY_ADMIN, 3),
                SeverityLevel.LOW: (ActionType.LOG_ONLY, 4),
            },
            
            # Validation errors - usually just log
            EventType.VALIDATION_ERROR: {
                SeverityLevel.CRITICAL: (ActionType.NOTIFY_ADMIN, 3),
                SeverityLevel.HIGH: (ActionType.NOTIFY_ADMIN, 3),
                SeverityLevel.MEDIUM: (ActionType.LOG_ONLY, 4),
                SeverityLevel.LOW: (ActionType.LOG_ONLY, 5),
            },
            
            # Ignorable events - always just log
            EventType.IGNORABLE: {
                SeverityLevel.CRITICAL: (ActionType.LOG_ONLY, 5),
                SeverityLevel.HIGH: (ActionType.LOG_ONLY, 5),
                SeverityLevel.MEDIUM: (ActionType.LOG_ONLY, 5),
                SeverityLevel.LOW: (ActionType.LOG_ONLY, 5),
            },
        }
        
        # Apply custom rules if provided
        if self.custom_rules:
            self._apply_custom_rules()
    
    def _apply_custom_rules(self):
        """Apply custom routing rules to override defaults"""
        for event_type_str, severity_rules in self.custom_rules.items():
            try:
                event_type = EventType(event_type_str)
                for severity_str, (action_str, priority) in severity_rules.items():
                    severity = SeverityLevel(severity_str)
                    action = ActionType(action_str)
                    if event_type not in self.routing_rules:
                        self.routing_rules[event_type] = {}
                    self.routing_rules[event_type][severity] = (action, priority)
            except (ValueError, KeyError):
                # Skip invalid custom rules
                continue
    
    def route(self, event: AnalyzedEvent) -> RoutingDecision:
        """
        Route an analyzed event to the appropriate action.
        
        Args:
            event: AnalyzedEvent with type, severity, and context
            
        Returns:
            RoutingDecision with action, priority, and reasoning
        """
        # Get action and priority from routing rules
        action, priority = self._get_action_for_event(event)
        
        # Generate reasoning
        reason = self._generate_reason(event, action)
        
        # Build metadata
        metadata = self._build_metadata(event, action)
        
        return RoutingDecision(
            action=action,
            priority=priority,
            reason=reason,
            metadata=metadata
        )
    
    def _get_action_for_event(self, event: AnalyzedEvent) -> tuple[ActionType, int]:
        """
        Get the action and priority for an event based on routing rules.
        
        Args:
            event: AnalyzedEvent to route
            
        Returns:
            Tuple of (ActionType, priority)
        """
        # Check if event type exists in rules
        if event.event_type not in self.routing_rules:
            # Default fallback
            return ActionType.LOG_ONLY, 5
        
        # Check if severity exists for this event type
        severity_rules = self.routing_rules[event.event_type]
        if event.severity not in severity_rules:
            # Default fallback
            return ActionType.LOG_ONLY, 5
        
        return severity_rules[event.severity]
    
    def _generate_reason(self, event: AnalyzedEvent, action: ActionType) -> str:
        """
        Generate a human-readable reason for the routing decision.
        
        Args:
            event: AnalyzedEvent being routed
            action: ActionType that was chosen
            
        Returns:
            Reason string explaining the decision
        """
        reasons = {
            ActionType.LOG_ONLY: f"Event classified as {event.event_type.value} with {event.severity.value} severity - logging for record keeping",
            ActionType.NOTIFY_ADMIN: f"Event requires admin attention: {event.event_type.value} with {event.severity.value} severity",
            ActionType.TRIGGER_WORKFLOW: f"Event triggers automated workflow: {event.event_type.value} with {event.severity.value} severity",
            ActionType.ESCALATE: f"Critical event requiring immediate escalation: {event.event_type.value} with {event.severity.value} severity",
        }
        
        return reasons.get(action, f"Routing {event.event_type.value} event")
    
    def _build_metadata(self, event: AnalyzedEvent, action: ActionType) -> Dict[str, Any]:
        """
        Build metadata for the routing decision.
        
        Args:
            event: AnalyzedEvent being routed
            action: ActionType that was chosen
            
        Returns:
            Dictionary with relevant metadata
        """
        metadata = {
            "event_type": event.event_type.value,
            "severity": event.severity.value,
            "message": event.message,
            "requires_immediate_action": action in [ActionType.ESCALATE, ActionType.TRIGGER_WORKFLOW],
            "user_facing": event.event_type == EventType.VALIDATION_ERROR,
        }
        
        # Add action-specific metadata
        if action == ActionType.ESCALATE:
            metadata["escalation_level"] = "immediate"
            metadata["notify_channels"] = ["email", "sms", "slack"]
        
        elif action == ActionType.NOTIFY_ADMIN:
            metadata["notify_channels"] = ["email", "slack"]
        
        elif action == ActionType.TRIGGER_WORKFLOW:
            metadata["workflow_type"] = self._determine_workflow_type(event)
        
        # Include original context
        metadata["original_context"] = event.context
        
        return metadata
    
    def _determine_workflow_type(self, event: AnalyzedEvent) -> str:
        """
        Determine which workflow to trigger based on event type.
        
        Args:
            event: AnalyzedEvent being processed
            
        Returns:
            Workflow type identifier
        """
        workflow_mapping = {
            EventType.SYSTEM_ERROR: "system_recovery",
            EventType.PERFORMANCE_ISSUE: "performance_optimization",
            EventType.SECURITY_ISSUE: "security_response",
        }
        
        return workflow_mapping.get(event.event_type, "generic_handler")
    
    def get_routing_summary(self) -> Dict[str, Any]:
        """
        Get a summary of current routing rules.
        
        Returns:
            Dictionary summarizing all routing rules
        """
        summary = {}
        for event_type, severity_rules in self.routing_rules.items():
            summary[event_type.value] = {
                severity.value: {
                    "action": action.value,
                    "priority": priority
                }
                for severity, (action, priority) in severity_rules.items()
            }
        return summary


# ============================================================================
# Convenience Functions
# ============================================================================

def route_event(
    event_type: str,
    severity: str,
    message: str,
    context: Optional[Dict[str, Any]] = None
) -> RoutingDecision:
    """
    Quick function to route an event without creating objects.
    
    Args:
        event_type: Event type as string
        severity: Severity level as string
        message: Event message
        context: Optional context dictionary
        
    Returns:
        RoutingDecision with action and details
    """
    event = AnalyzedEvent(
        event_type=EventType(event_type),
        severity=SeverityLevel(severity),
        message=message,
        context=context or {}
    )
    
    router = EventRouter()
    return router.route(event)


# ============================================================================
# Example Usage and Tests
# ============================================================================

if __name__ == "__main__":
    print("=== Event Router Examples ===\n")
    
    # Initialize router
    router = EventRouter()
    
    # Example 1: Critical security issue
    print("Example 1: Critical Security Issue")
    event1 = AnalyzedEvent(
        event_type=EventType.SECURITY_ISSUE,
        severity=SeverityLevel.CRITICAL,
        message="Unauthorized access attempt detected",
        context={"ip": "192.168.1.100", "endpoint": "/admin"}
    )
    decision1 = router.route(event1)
    print(f"Action: {decision1.action.value}")
    print(f"Priority: {decision1.priority}")
    print(f"Reason: {decision1.reason}")
    print(f"Metadata: {decision1.metadata}\n")
    
    # Example 2: Medium system error
    print("Example 2: Medium System Error")
    event2 = AnalyzedEvent(
        event_type=EventType.SYSTEM_ERROR,
        severity=SeverityLevel.MEDIUM,
        message="Database connection timeout",
        context={"database": "postgres", "timeout": 30}
    )
    decision2 = router.route(event2)
    print(f"Action: {decision2.action.value}")
    print(f"Priority: {decision2.priority}")
    print(f"Reason: {decision2.reason}\n")
    
    # Example 3: Low validation error
    print("Example 3: Low Validation Error")
    event3 = AnalyzedEvent(
        event_type=EventType.VALIDATION_ERROR,
        severity=SeverityLevel.LOW,
        message="Invalid email format",
        context={"field": "email", "value": "invalid"}
    )
    decision3 = router.route(event3)
    print(f"Action: {decision3.action.value}")
    print(f"Priority: {decision3.priority}")
    print(f"Reason: {decision3.reason}\n")
    
    # Example 4: High performance issue
    print("Example 4: High Performance Issue")
    event4 = AnalyzedEvent(
        event_type=EventType.PERFORMANCE_ISSUE,
        severity=SeverityLevel.HIGH,
        message="API response time exceeds threshold",
        context={"endpoint": "/api/users", "response_time_ms": 5000}
    )
    decision4 = router.route(event4)
    print(f"Action: {decision4.action.value}")
    print(f"Priority: {decision4.priority}")
    print(f"Reason: {decision4.reason}\n")
    
    # Example 5: Using convenience function
    print("Example 5: Using Convenience Function")
    decision5 = route_event(
        event_type="system_error",
        severity="critical",
        message="Service unavailable",
        context={"service": "payment-gateway"}
    )
    print(f"Action: {decision5.action.value}")
    print(f"Priority: {decision5.priority}\n")
    
    # Example 6: Custom routing rules
    print("Example 6: Custom Routing Rules")
    custom_rules = {
        "validation_error": {
            "high": ("notify_admin", 2),  # Override default
        }
    }
    custom_router = EventRouter(custom_rules=custom_rules)
    
    event6 = AnalyzedEvent(
        event_type=EventType.VALIDATION_ERROR,
        severity=SeverityLevel.HIGH,
        message="Critical validation failure",
        context={"field": "payment_amount"}
    )
    decision6 = custom_router.route(event6)
    print(f"Action: {decision6.action.value} (custom rule applied)")
    print(f"Priority: {decision6.priority}\n")
    
    # Example 7: Routing summary
    print("Example 7: Routing Rules Summary")
    summary = router.get_routing_summary()
    print("Security Issue Rules:")
    for severity, rule in summary["security_issue"].items():
        print(f"  {severity}: {rule['action']} (priority {rule['priority']})")
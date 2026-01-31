"""
AI Agent Backend Operations Demo
=================================
Simulates backend error events and demonstrates the AI agent's
decision-making process from error detection to action execution.

Perfect for hackathon demos and presentations!
"""

import json
from datetime import datetime
from ai_agent_service import AIAgentService
from event_router import EventRouter, AnalyzedEvent, EventType, SeverityLevel


# ============================================================================
# Demo Configuration
# ============================================================================

def print_header(title):
    """Print a formatted section header"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_section(title):
    """Print a formatted subsection"""
    print(f"\n--- {title} ---")


def print_result(label, value, indent=0):
    """Print a formatted result"""
    spacing = "  " * indent
    print(f"{spacing}• {label}: {value}")


# ============================================================================
# Demo Scenarios
# ============================================================================

def demo_scenario_1():
    """Demo 1: Critical Security Issue"""
    print_header("DEMO 1: Critical Security Issue")
    
    # Simulate a security event
    print_section("1. Incoming Error Event")
    error_payload = {
        "error_type": "AuthenticationError",
        "message": "Multiple failed login attempts detected from suspicious IP",
        "stack_trace": "...",
        "context": {
            "ip_address": "192.168.1.100",
            "endpoint": "/admin/login",
            "attempts": 15,
            "time_window": "5 minutes"
        }
    }
    print(json.dumps(error_payload, indent=2))
    
    # Process through AI agent
    print_section("2. AI Agent Analysis")
    agent = AIAgentService()
    decision = agent.process(error_payload)
    
    print_result("Action", decision['action'])
    print_result("Priority", decision['priority'])
    print_result("Reasoning", decision['metadata'].get('analysis', 'Security threat detected'))
    
    # Route the decision
    print_section("3. Action Router Decision")
    router = EventRouter()
    analyzed_event = AnalyzedEvent(
        event_type=EventType.SECURITY_ISSUE,
        severity=SeverityLevel.HIGH,
        message=error_payload['message'],
        context=error_payload['context']
    )
    routing_decision = router.route(analyzed_event)
    
    print_result("Final Action", routing_decision.action.value)
    print_result("Priority Level", routing_decision.priority)
    print_result("Reason", routing_decision.reason)
    
    # Simulate execution
    print_section("4. Execution Outcome")
    print_result("Status", "✓ SUCCESS", indent=0)
    print_result("Actions Taken", "", indent=0)
    print_result("Email sent to security team", "2 recipients", indent=1)
    print_result("Incident logged", "HIGH severity", indent=1)
    print_result("IP blocked", "192.168.1.100", indent=1)
    print_result("Workflow triggered", "security_response", indent=1)


def demo_scenario_2():
    """Demo 2: System Error"""
    print_header("DEMO 2: Database Connection Timeout")
    
    # Simulate a system error
    print_section("1. Incoming Error Event")
    error_payload = {
        "error_type": "DatabaseError",
        "message": "Connection to PostgreSQL database timed out after 30 seconds",
        "stack_trace": "Traceback (most recent call last)...",
        "context": {
            "database": "postgres",
            "host": "db.example.com",
            "timeout": 30,
            "query": "SELECT * FROM users WHERE..."
        }
    }
    print(json.dumps(error_payload, indent=2))
    
    # Process through AI agent
    print_section("2. AI Agent Analysis")
    agent = AIAgentService()
    decision = agent.process(error_payload)
    
    print_result("Action", decision['action'])
    print_result("Priority", decision['priority'])
    print_result("Category", "System Error")
    
    # Route the decision
    print_section("3. Action Router Decision")
    router = EventRouter()
    analyzed_event = AnalyzedEvent(
        event_type=EventType.SYSTEM_ERROR,
        severity=SeverityLevel.MEDIUM,
        message=error_payload['message'],
        context=error_payload['context']
    )
    routing_decision = router.route(analyzed_event)
    
    print_result("Final Action", routing_decision.action.value)
    print_result("Priority Level", routing_decision.priority)
    print_result("Workflow Type", routing_decision.metadata.get('workflow_type', 'N/A'))
    
    # Simulate execution
    print_section("4. Execution Outcome")
    print_result("Status", "✓ SUCCESS", indent=0)
    print_result("Actions Taken", "", indent=0)
    print_result("Admin notified", "ops@example.com", indent=1)
    print_result("Event logged", "MEDIUM severity", indent=1)
    print_result("Monitoring alert", "Database health check triggered", indent=1)


def demo_scenario_3():
    """Demo 3: Validation Error (Low Priority)"""
    print_header("DEMO 3: User Input Validation Error")
    
    # Simulate a validation error
    print_section("1. Incoming Error Event")
    error_payload = {
        "error_type": "ValidationError",
        "message": "Invalid email format provided by user",
        "context": {
            "field": "email",
            "value": "not-an-email",
            "user_id": "12345",
            "endpoint": "/api/users/update"
        }
    }
    print(json.dumps(error_payload, indent=2))
    
    # Process through AI agent
    print_section("2. AI Agent Analysis")
    agent = AIAgentService()
    decision = agent.process(error_payload)
    
    print_result("Action", decision['action'])
    print_result("Priority", decision['priority'])
    print_result("Category", "Validation Error")
    
    # Route the decision
    print_section("3. Action Router Decision")
    router = EventRouter()
    analyzed_event = AnalyzedEvent(
        event_type=EventType.VALIDATION_ERROR,
        severity=SeverityLevel.LOW,
        message=error_payload['message'],
        context=error_payload['context']
    )
    routing_decision = router.route(analyzed_event)
    
    print_result("Final Action", routing_decision.action.value)
    print_result("Priority Level", routing_decision.priority)
    print_result("User Facing", routing_decision.metadata.get('user_facing', False))
    
    # Simulate execution
    print_section("4. Execution Outcome")
    print_result("Status", "✓ SUCCESS", indent=0)
    print_result("Actions Taken", "", indent=0)
    print_result("Event logged", "INFO level", indent=1)
    print_result("User response", "400 Bad Request with validation message", indent=1)


def demo_comparison():
    """Demo: Side-by-side comparison of different event types"""
    print_header("COMPARISON: How AI Agent Handles Different Events")
    
    scenarios = [
        {
            "name": "Security Issue",
            "type": EventType.SECURITY_ISSUE,
            "severity": SeverityLevel.CRITICAL,
            "message": "Unauthorized access attempt"
        },
        {
            "name": "System Error",
            "type": EventType.SYSTEM_ERROR,
            "severity": SeverityLevel.HIGH,
            "message": "Service unavailable"
        },
        {
            "name": "Performance Issue",
            "type": EventType.PERFORMANCE_ISSUE,
            "severity": SeverityLevel.MEDIUM,
            "message": "API response time > 5s"
        },
        {
            "name": "Validation Error",
            "type": EventType.VALIDATION_ERROR,
            "severity": SeverityLevel.LOW,
            "message": "Invalid input format"
        }
    ]
    
    router = EventRouter()
    
    print("\n{:<20} {:<15} {:<20} {:<10}".format(
        "Event Type", "Severity", "Action", "Priority"
    ))
    print("-" * 70)
    
    for scenario in scenarios:
        event = AnalyzedEvent(
            event_type=scenario['type'],
            severity=scenario['severity'],
            message=scenario['message'],
            context={}
        )
        decision = router.route(event)
        
        print("{:<20} {:<15} {:<20} {:<10}".format(
            scenario['name'],
            scenario['severity'].value.upper(),
            decision.action.value,
            f"P{decision.priority}"
        ))


# ============================================================================
# Main Demo Runner
# ============================================================================

def main():
    """Run all demo scenarios"""
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 68 + "║")
    print("║" + "  🤖 AI AGENT BACKEND OPERATIONS - LIVE DEMO".center(68) + "║")
    print("║" + " " * 68 + "║")
    print("╚" + "═" * 68 + "╝")
    
    print("\n📋 This demo shows how the AI agent:")
    print("   1. Analyzes incoming error events")
    print("   2. Classifies them by type and severity")
    print("   3. Decides on appropriate actions")
    print("   4. Executes backend operations")
    
    input("\n👉 Press ENTER to start Demo 1...")
    demo_scenario_1()
    
    input("\n\n👉 Press ENTER to start Demo 2...")
    demo_scenario_2()
    
    input("\n\n👉 Press ENTER to start Demo 3...")
    demo_scenario_3()
    
    input("\n\n👉 Press ENTER to see comparison table...")
    demo_comparison()
    
    print_header("DEMO COMPLETE")
    print("\n✨ Key Takeaways:")
    print("   • AI agent automatically classifies errors")
    print("   • Different event types trigger different actions")
    print("   • Priority-based routing ensures critical issues get immediate attention")
    print("   • System is extensible and production-ready")
    
    print("\n🎯 Next Steps:")
    print("   • Integrate with IBM watsonx for advanced AI classification")
    print("   • Connect to Django REST API for production deployment")
    print("   • Add custom routing rules for your specific use case")
    
    print("\n" + "=" * 70)
    print("  Thank you for watching! 🚀")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
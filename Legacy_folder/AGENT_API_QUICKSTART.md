# AI Agent API - Quickstart Guide

## 🚀 Hackathon-Ready Django REST API

This guide shows how to quickly integrate the AI Agent service into your Django project.

## File Structure

```
your_django_project/
├── agent_views.py          # API view functions
├── agent_urls.py           # URL routing
├── ai_agent_service.py     # AI agent logic
├── event_router.py         # Event routing
├── validation_module.py    # Payload validation
└── requirements.txt        # Dependencies
```

## Quick Setup

### 1. Install Dependencies
```bash
pip install djangorestframework
```

### 2. Add to Django Settings

In your `settings.py`:

```python
INSTALLED_APPS = [
    # ... other apps
    'rest_framework',
]

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
}
```

### 3. Configure URLs

In your main `urls.py`:

```python
from django.urls import path, include

urlpatterns = [
    # ... other patterns
    path('agent/', include('agent_urls')),
]
```

### 4. Run Server
```bash
python manage.py runserver
```

## API Endpoints

### 1. Analyze Event
**POST** `/agent/analyze-event/`

Analyzes an error event and classifies it.

**Request:**
```json
{
    "error_type": "ValidationError",
    "message": "Invalid email format",
    "stack_trace": "",
    "context": {"field": "email"}
}
```

**Response:**
```json
{
    "category": "validation_error",
    "severity": "low",
    "action": "log_only",
    "priority": 5,
    "metadata": {}
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/agent/analyze-event/ \
  -H "Content-Type: application/json" \
  -d '{
    "error_type": "ValidationError",
    "message": "Invalid email format",
    "context": {"field": "email"}
  }'
```

---

### 2. Decide Action
**POST** `/agent/decide-action/`

Decides what action to take based on event classification.

**Request:**
```json
{
    "event_type": "security_issue",
    "severity": "high",
    "message": "Unauthorized access attempt",
    "context": {"ip": "192.168.1.100"}
}
```

**Response:**
```json
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
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/agent/decide-action/ \
  -H "Content-Type: application/json" \
  -d '{
    "event_type": "security_issue",
    "severity": "high",
    "message": "Unauthorized access attempt",
    "context": {"ip": "192.168.1.100"}
  }'
```

---

### 3. Execute Action
**POST** `/agent/execute-action/`

Executes a backend action based on the decision.

**Request:**
```json
{
    "action": "notify_admin",
    "priority": 2,
    "event_type": "system_error",
    "severity": "medium",
    "message": "Database connection timeout",
    "context": {"database": "postgres"},
    "metadata": {}
}
```

**Response:**
```json
{
    "success": true,
    "action": "notify_admin",
    "message": "Admin notification sent",
    "execution_time": "2024-01-31T12:00:00",
    "details": {
        "notifications_sent": 1
    }
}
```

**cURL Example:**
```bash
curl -X POST http://localhost:8000/agent/execute-action/ \
  -H "Content-Type: application/json" \
  -d '{
    "action": "notify_admin",
    "priority": 2,
    "event_type": "system_error",
    "severity": "medium",
    "message": "Database connection timeout"
  }'
```

---

### 4. Validate Payload
**POST** `/agent/validate-payload/`

Validates incoming payloads against required fields.

**Request:**
```json
{
    "payload": {
        "username": "john",
        "email": "john@example.com"
    },
    "required_fields": ["username", "email", "password"]
}
```

**Response:**
```json
{
    "is_valid": false,
    "missing_fields": ["password"],
    "message": "Missing required fields: password"
}
```

---

### 5. Health Check
**GET** `/agent/health/`

Check if the service is running.

**Response:**
```json
{
    "status": "healthy",
    "service": "AI Agent Backend Operations",
    "version": "1.0.0",
    "endpoints": [
        "/agent/analyze-event/",
        "/agent/decide-action/",
        "/agent/execute-action/",
        "/agent/validate-payload/",
        "/agent/health/"
    ]
}
```

## Complete Workflow Example

### Python Client
```python
import requests

BASE_URL = "http://localhost:8000/agent"

# Step 1: Analyze the event
analyze_response = requests.post(
    f"{BASE_URL}/analyze-event/",
    json={
        "error_type": "DatabaseError",
        "message": "Connection timeout",
        "context": {"database": "postgres"}
    }
)
analysis = analyze_response.json()
print("Analysis:", analysis)

# Step 2: Decide action
decide_response = requests.post(
    f"{BASE_URL}/decide-action/",
    json={
        "event_type": "system_error",
        "severity": "high",
        "message": "Connection timeout",
        "context": {"database": "postgres"}
    }
)
decision = decide_response.json()
print("Decision:", decision)

# Step 3: Execute action
execute_response = requests.post(
    f"{BASE_URL}/execute-action/",
    json={
        "action": decision["action"],
        "priority": decision["priority"],
        "event_type": "system_error",
        "severity": "high",
        "message": "Connection timeout",
        "context": {"database": "postgres"},
        "metadata": decision["metadata"]
    }
)
result = execute_response.json()
print("Execution:", result)
```

### JavaScript/Fetch
```javascript
const BASE_URL = "http://localhost:8000/agent";

// Analyze event
const analyzeResponse = await fetch(`${BASE_URL}/analyze-event/`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        error_type: "ValidationError",
        message: "Invalid input",
        context: {field: "email"}
    })
});
const analysis = await analyzeResponse.json();
console.log("Analysis:", analysis);

// Decide action
const decideResponse = await fetch(`${BASE_URL}/decide-action/`, {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        event_type: "validation_error",
        severity: "low",
        message: "Invalid input",
        context: {field: "email"}
    })
});
const decision = await decideResponse.json();
console.log("Decision:", decision);
```

## Event Types

- `validation_error` - User input validation failures
- `system_error` - System-level errors (database, network, etc.)
- `security_issue` - Security-related events
- `performance_issue` - Performance degradation
- `ignorable` - Low-priority informational events

## Severity Levels

- `low` - Minor issues, informational
- `medium` - Moderate issues requiring attention
- `high` - Serious issues requiring prompt action
- `critical` - Critical issues requiring immediate response

## Actions

- `log_only` - Record event in logs
- `notify_admin` - Send notification to administrators
- `trigger_workflow` - Initiate automated workflow
- `escalate` - Critical escalation with multiple notifications

## Testing

### Test with cURL
```bash
# Health check
curl http://localhost:8000/agent/health/

# Analyze event
curl -X POST http://localhost:8000/agent/analyze-event/ \
  -H "Content-Type: application/json" \
  -d '{"error_type": "TestError", "message": "Test message"}'
```

### Test with Python
```python
import requests

response = requests.get("http://localhost:8000/agent/health/")
print(response.json())
```

## Troubleshooting

### Import Errors
Make sure all module files are in the same directory or in your Python path:
- `ai_agent_service.py`
- `event_router.py`
- `validation_module.py`

### Module Not Found
```bash
# Add current directory to Python path
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Port Already in Use
```bash
python manage.py runserver 8001
```

## Next Steps

1. ✅ Test endpoints with cURL or Postman
2. ✅ Integrate with your frontend
3. ✅ Add authentication (optional)
4. ✅ Deploy to production
5. ✅ Connect to IBM watsonx for AI-powered classification

## Demo Script

Run the included demo:
```bash
python demo.py
```

This shows the complete workflow with example events!
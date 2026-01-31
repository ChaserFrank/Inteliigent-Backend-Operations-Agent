# AI Agent API Setup Guide

## Overview
Production-ready Django REST API endpoint for executing AI agent decisions with security, rate limiting, and comprehensive action handling.

## Installation

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Django Settings Configuration

Add to your `settings.py`:

```python
# Installed Apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',  # For token authentication
]

# AI Agent API Settings
ADMIN_NOTIFICATION_EMAILS = [
    'admin@example.com',
    'ops@example.com',
]

# Email Configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'your-email@example.com'
EMAIL_HOST_PASSWORD = 'your-app-password'
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
    },
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
    ],
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
```

### 3. URL Configuration

Create or update `urls.py`:

```python
from django.contrib import admin
from django.urls import path
from agent_api import execute_agent_decision

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/agent/execute-decision/', execute_agent_decision, name='execute_agent_decision'),
]
```

### 4. Create Logs Directory
```bash
mkdir -p logs
```

### 5. Run Migrations
```bash
python manage.py migrate
```

### 6. Create Superuser (for authentication)
```bash
python manage.py createsuperuser
```

### 7. Generate API Token
```bash
python manage.py drf_create_token <username>
```

## API Usage

### Authentication
The API requires authentication. Use Token Authentication:

```bash
curl -X POST http://localhost:8000/api/agent/execute-decision/ \
  -H "Authorization: Token YOUR_TOKEN_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "action": "notify_admin",
    "priority": 2,
    "event_type": "security_issue",
    "severity": "high",
    "message": "Unauthorized access attempt detected",
    "context": {
      "ip": "192.168.1.100",
      "endpoint": "/admin/users"
    }
  }'
```

### Request Format

**Endpoint**: `POST /api/agent/execute-decision/`

**Headers**:
- `Authorization: Token <your-token>`
- `Content-Type: application/json`

**Body**:
```json
{
  "action": "notify_admin",
  "priority": 2,
  "event_type": "security_issue",
  "severity": "high",
  "message": "Event description",
  "context": {},
  "metadata": {}
}
```

**Fields**:
- `action` (required): One of `log_only`, `notify_admin`, `trigger_workflow`, `escalate`
- `priority` (required): Integer 1-5 (1=highest)
- `event_type` (required): String describing event type
- `severity` (required): One of `low`, `medium`, `high`, `critical`
- `message` (required): Event message
- `context` (optional): Additional context data
- `metadata` (optional): Decision metadata

### Response Format

**Success (200)**:
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

**Error (400)**:
```json
{
  "success": false,
  "message": "Invalid request data",
  "errors": {
    "action": ["This field is required."]
  }
}
```

## Actions

### 1. log_only
Records event in application logs for monitoring.

**Use Case**: Low-priority events, informational messages

### 2. notify_admin
Sends email notification to configured administrators.

**Use Case**: Events requiring admin attention

### 3. trigger_workflow
Initiates automated workflow for event handling.

**Use Case**: Events requiring automated response

### 4. escalate
Immediate critical response with multiple notifications.

**Use Case**: Critical security or system issues

## Security Features

1. **Authentication Required**: All requests must be authenticated
2. **Rate Limiting**: 100 requests per hour per user
3. **Input Validation**: Comprehensive serializer validation
4. **Secure Logging**: Sensitive data handling in logs
5. **HTTPS Recommended**: Use HTTPS in production

## Production Deployment

### Environment Variables
```bash
export DJANGO_SECRET_KEY='your-secret-key'
export DJANGO_DEBUG=False
export DATABASE_URL='postgresql://user:pass@localhost/dbname'
export EMAIL_HOST_PASSWORD='your-email-password'
```

### Using Gunicorn
```bash
gunicorn your_project.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### Using Docker
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["gunicorn", "your_project.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## Testing

### Using Python requests
```python
import requests

url = 'http://localhost:8000/api/agent/execute-decision/'
headers = {
    'Authorization': 'Token YOUR_TOKEN',
    'Content-Type': 'application/json'
}
data = {
    'action': 'log_only',
    'priority': 5,
    'event_type': 'test_event',
    'severity': 'low',
    'message': 'Test message'
}

response = requests.post(url, json=data, headers=headers)
print(response.json())
```

### Integration with AI Agent Service
```python
from ai_agent_service import AIAgentService
import requests

# Initialize AI agent
agent = AIAgentService()

# Process event
payload = {
    'error_type': 'ValidationError',
    'message': 'Invalid input',
    'context': {'field': 'email'}
}
decision = agent.process(payload)

# Send to API
response = requests.post(
    'http://localhost:8000/api/agent/execute-decision/',
    json={
        'action': decision['action'],
        'priority': decision['priority'],
        'event_type': payload['error_type'],
        'severity': 'medium',
        'message': payload['message'],
        'context': payload['context'],
        'metadata': decision['metadata']
    },
    headers={'Authorization': 'Token YOUR_TOKEN'}
)
```

## Monitoring

Check logs:
```bash
tail -f logs/agent_decisions.log
```

## Troubleshooting

### Email not sending
- Verify EMAIL_HOST_USER and EMAIL_HOST_PASSWORD
- Check ADMIN_NOTIFICATION_EMAILS is configured
- Ensure email provider allows SMTP access

### Rate limit errors
- Adjust REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] in settings
- Use different authentication tokens for different services

### Authentication errors
- Verify token is valid: `python manage.py drf_create_token <username>`
- Check Authorization header format: `Token <your-token>`
# Django AI Agent Exception Middleware - Setup Guide

## Overview

This middleware captures all unhandled exceptions in your Django application and sends them to an external AI agent service for analysis. It's production-safe and works with `DEBUG = False`.

## Installation

### 1. Place the Middleware File

Copy `exception_middleware.py` to your Django project:

```
your_django_project/
├── config/                          # or your project name
│   ├── settings.py
│   ├── urls.py
│   └── middleware/                  # Create this directory
│       ├── __init__.py             # Empty file
│       └── exception_middleware.py # Place the middleware here
```

**Alternative locations:**
- `your_project/middleware/exception_middleware.py`
- `apps/core/middleware/exception_middleware.py`
- Any app directory: `apps/monitoring/middleware/exception_middleware.py`

### 2. Install Required Dependencies

Add to your `requirements.txt`:

```txt
Django>=4.2
requests>=2.31.0
```

Install:
```bash
pip install -r requirements.txt
```

### 3. Configure Django Settings

Add to your `settings.py`:

```python
# settings.py

# ============================================================================
# MIDDLEWARE CONFIGURATION
# ============================================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    
    # Add AI Agent Exception Middleware LAST
    # This ensures it catches exceptions from all other middleware
    'config.middleware.exception_middleware.AIAgentExceptionMiddleware',
    # OR for async version (recommended for production):
    # 'config.middleware.exception_middleware.AsyncAIAgentExceptionMiddleware',
]

# ============================================================================
# AI AGENT SERVICE CONFIGURATION
# ============================================================================

# Enable/disable the AI agent integration
AI_AGENT_ENABLED = True  # Set to False to disable without removing middleware

# AI agent service endpoint (REQUIRED if enabled)
AI_AGENT_ENDPOINT = os.environ.get(
    'AI_AGENT_ENDPOINT',
    'http://localhost:8001/api/v1/analyze-error'  # Default for local development
)

# API key for authenticating with the AI agent service (optional)
AI_AGENT_API_KEY = os.environ.get('AI_AGENT_API_KEY', None)

# Timeout for requests to AI agent service (seconds)
AI_AGENT_TIMEOUT = int(os.environ.get('AI_AGENT_TIMEOUT', 5))

# Maximum request body size to send (bytes)
AI_AGENT_MAX_BODY_SIZE = 10000  # 10KB

# Server identification (optional, for multi-server deployments)
HOSTNAME = os.environ.get('HOSTNAME', 'unknown')
VERSION = os.environ.get('APP_VERSION', '1.0.0')

# ============================================================================
# LOGGING CONFIGURATION (Optional but recommended)
# ============================================================================

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
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': 'logs/exceptions.log',
            'maxBytes': 1024 * 1024 * 10,  # 10MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'config.middleware.exception_middleware': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### 4. Environment Variables

Create a `.env` file in your project root:

```bash
# .env

# AI Agent Service Configuration
AI_AGENT_ENABLED=true
AI_AGENT_ENDPOINT=https://your-ai-agent-service.com/api/v1/analyze-error
AI_AGENT_API_KEY=your-secret-api-key-here
AI_AGENT_TIMEOUT=5

# Server Identification
HOSTNAME=web-server-01
APP_VERSION=1.0.0
```

Load environment variables in `settings.py`:

```python
# settings.py
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ... rest of settings
```

Install python-dotenv:
```bash
pip install python-dotenv
```

## Usage

### Basic Usage

Once configured, the middleware automatically captures all unhandled exceptions. No additional code is required.

```python
# views.py
from django.http import JsonResponse

def my_view(request):
    # This exception will be caught and sent to the AI agent
    result = 1 / 0  # ZeroDivisionError
    return JsonResponse({'result': result})
```

### Testing the Middleware

Create a test view to trigger an exception:

```python
# urls.py
from django.urls import path

def test_exception(request):
    """Test endpoint to trigger an exception"""
    raise ValueError("This is a test exception for AI agent analysis")

urlpatterns = [
    path('test-exception/', test_exception, name='test_exception'),
    # ... other urls
]
```

Visit `http://localhost:8000/test-exception/` to trigger the exception.

### Expected AI Agent Service Payload

The middleware sends a JSON payload like this:

```json
{
  "timestamp": "2024-01-31T12:00:00.000000",
  "environment": "production",
  "request": {
    "path": "/api/v1/users/",
    "method": "POST",
    "content_type": "application/json",
    "query_params": {},
    "remote_addr": "192.168.1.100",
    "user_agent": "Mozilla/5.0..."
  },
  "request_body": "{\"username\": \"john\"}",
  "user": {
    "authenticated": true,
    "id": 123,
    "username": "john_doe",
    "email": "john@example.com"
  },
  "exception": {
    "type": "ValueError",
    "message": "Invalid user data",
    "module": "builtins",
    "traceback": "Traceback (most recent call last):\n...",
    "traceback_list": ["  File ...", "  File ..."]
  },
  "server": {
    "hostname": "web-server-01",
    "version": "1.0.0"
  }
}
```

## AI Agent Service Implementation

Your AI agent service should accept POST requests at the configured endpoint:

```python
# Example AI agent service endpoint (FastAPI)
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class ExceptionData(BaseModel):
    timestamp: str
    environment: str
    request: dict
    user: dict
    exception: dict
    server: dict

@app.post("/api/v1/analyze-error")
async def analyze_error(data: ExceptionData):
    """
    Receive exception data from Django middleware and analyze with AI.
    """
    # Send to Claude/OpenAI for analysis
    analysis = await analyze_with_ai(data)
    
    # Store in database
    await store_exception(data, analysis)
    
    # Trigger alerts if critical
    if analysis.get('severity') == 'critical':
        await send_alert(data, analysis)
    
    return {
        "status": "received",
        "analysis": analysis
    }
```

## Production Considerations

### 1. Use Async Version

For production, use `AsyncAIAgentExceptionMiddleware` to avoid blocking:

```python
MIDDLEWARE = [
    # ... other middleware
    'config.middleware.exception_middleware.AsyncAIAgentExceptionMiddleware',
]
```

### 2. Set Appropriate Timeout

```python
AI_AGENT_TIMEOUT = 3  # Don't wait too long for AI service
```

### 3. Monitor Middleware Performance

```python
# Add monitoring
import time

class MonitoredAIAgentExceptionMiddleware(AsyncAIAgentExceptionMiddleware):
    def process_exception(self, request, exception):
        start_time = time.time()
        result = super().process_exception(request, exception)
        duration = time.time() - start_time
        
        if duration > 1.0:
            logger.warning(f"Middleware took {duration:.2f}s to process exception")
        
        return result
```

### 4. Handle AI Service Downtime

The middleware is designed to fail gracefully:
- If AI service is down, exceptions are still logged locally
- Django's default error handling continues normally
- No user-facing errors from middleware failures

### 5. Security Considerations

- **Sensitive Data**: The middleware captures request bodies. Ensure sensitive data (passwords, tokens) is not logged.
- **API Keys**: Store `AI_AGENT_API_KEY` in environment variables, never in code.
- **Rate Limiting**: Consider rate limiting on the AI agent service to prevent abuse.

## Troubleshooting

### Middleware Not Capturing Exceptions

1. Check middleware is in `MIDDLEWARE` list
2. Ensure it's placed LAST in the middleware list
3. Verify `AI_AGENT_ENABLED = True`
4. Check logs for middleware initialization messages

### AI Service Not Receiving Data

1. Verify `AI_AGENT_ENDPOINT` is correct
2. Check network connectivity: `curl -X POST $AI_AGENT_ENDPOINT`
3. Verify API key if required
4. Check AI service logs for incoming requests
5. Increase `AI_AGENT_TIMEOUT` if service is slow

### Performance Issues

1. Switch to `AsyncAIAgentExceptionMiddleware`
2. Reduce `AI_AGENT_TIMEOUT`
3. Consider using a message queue (Celery) instead of direct HTTP calls
4. Monitor middleware execution time

## Advanced: Using with Celery

For high-traffic applications, send exception data via Celery:

```python
# tasks.py
from celery import shared_task
import requests

@shared_task
def send_exception_to_agent(exception_data):
    """Send exception data to AI agent service asynchronously"""
    response = requests.post(
        settings.AI_AGENT_ENDPOINT,
        json=exception_data,
        headers={'Authorization': f'Bearer {settings.AI_AGENT_API_KEY}'},
        timeout=settings.AI_AGENT_TIMEOUT
    )
    return response.status_code

# Modified middleware
class CeleryAIAgentExceptionMiddleware(AIAgentExceptionMiddleware):
    def _send_to_agent_service(self, exception_data):
        """Queue exception data for async processing"""
        from .tasks import send_exception_to_agent
        send_exception_to_agent.delay(exception_data)
```

## Testing

### Unit Tests

```python
# tests/test_middleware.py
from django.test import TestCase, RequestFactory
from config.middleware.exception_middleware import AIAgentExceptionMiddleware

class ExceptionMiddlewareTestCase(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = AIAgentExceptionMiddleware(lambda r: None)
    
    def test_captures_exception_context(self):
        request = self.factory.get('/test/')
        exception = ValueError("Test error")
        
        context = self.middleware._collect_exception_context(request, exception)
        
        self.assertEqual(context['request']['path'], '/test/')
        self.assertEqual(context['exception']['type'], 'ValueError')
        self.assertEqual(context['exception']['message'], 'Test error')
```

### Integration Tests

```python
# tests/test_integration.py
from django.test import TestCase, override_settings
from unittest.mock import patch, Mock

class MiddlewareIntegrationTestCase(TestCase):
    @override_settings(AI_AGENT_ENABLED=True)
    @patch('requests.post')
    def test_sends_to_agent_service(self, mock_post):
        mock_post.return_value = Mock(status_code=200)
        
        # Trigger an exception
        response = self.client.get('/test-exception/')
        
        # Verify request was made to AI service
        self.assertTrue(mock_post.called)
        call_args = mock_post.call_args
        self.assertIn('exception', call_args[1]['json'])
```

## Support

For issues or questions:
1. Check Django logs: `logs/exceptions.log`
2. Verify middleware configuration in `settings.py`
3. Test AI agent endpoint manually with curl
4. Review middleware source code for debugging

## License

This middleware is provided as-is for use in your Django projects.
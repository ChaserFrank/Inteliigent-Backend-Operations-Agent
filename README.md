# IBOA - Intelligent Backend Operations Agent

A Django REST API service that provides AI-powered backend operations for analyzing events, making intelligent decisions, and executing automated actions. Built for integration with IBM watsonx AI models.

## 🎯 Overview

IBOA is an intelligent agent system that processes backend events (errors, exceptions, system events) and automatically determines appropriate actions through AI-powered analysis. The system uses two specialized agents:

- **Analysis Agent**: Classifies events and determines severity levels
- **Orchestrator Agent**: Coordinates event processing and decides on actions

## ✨ Features

✅ **Event Analysis** - Intelligent classification of errors and events  
✅ **Automated Decision Making** - AI-powered action recommendations  
✅ **Action Execution** - Automated backend operations based on decisions  
✅ **Payload Validation** - Schema-based validation for incoming data  
✅ **IBM watsonx Integration** - Ready for watsonx.ai model integration  
✅ **RESTful API** - Clean, documented endpoints with OpenAPI/Swagger  
✅ **Production Ready** - Rate limiting, error handling, and logging  

## 🚀 Quick Start

### 1. Prerequisites

- Python 3.8+
- pip
- Virtual environment (recommended)

### 2. Installation

```bash
# Clone the repository
git clone <repository-url>
cd IBOA

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment variables
cp .env.example .env
# Edit .env with your configuration

# Run migrations
python manage.py migrate

# Start the development server
python manage.py runserver
```

### 3. Verify Installation

Visit `http://localhost:8000/agent/health/` to check if the service is running.

## 📚 API Endpoints

### Core Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/agent/analyze-event/` | POST | Analyze an event and get classification |
| `/agent/decide-action/` | POST | Decide what action to take for an event |
| `/agent/execute-action/` | POST | Execute a backend action |
| `/agent/validate-payload/` | POST | Validate incoming payload against schema |
| `/agent/health/` | GET | Health check endpoint |

### API Documentation

- **Swagger UI**: `http://localhost:8000/api/schema/swagger-ui/`
- **OpenAPI Schema**: `http://localhost:8000/api/schema/`

## 🔧 Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database (optional - defaults to SQLite)
DB_NAME=iboa_db
DB_USER=postgres
DB_PASSWORD=your-password
DB_HOST=localhost
DB_PORT=5432

# IBM watsonx Configuration (optional)
WATSONX_API_KEY=your-watsonx-api-key
WATSONX_PROJECT_ID=your-project-id
WATSONX_URL=https://us-south.ml.cloud.ibm.com
WATSONX_MODEL_ID=ibm/granite-13b-chat-v2
```

### Django Settings

Key settings in [`iboa_server/settings.py`](iboa_server/settings.py):

```python
INSTALLED_APPS = [
    # ...
    'rest_framework',
    'agents',
    'drf_spectacular',  # OpenAPI documentation
]

REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}
```

## 📖 Usage Examples

### 1. Analyze an Event

```bash
curl -X POST http://localhost:8000/agent/analyze-event/ \
  -H "Content-Type: application/json" \
  -d '{
    "error_type": "ValidationError",
    "message": "Invalid email format",
    "stack_trace": "",
    "context": {"field": "email"}
  }'
```

**Response:**
```json
{
  "category": "validation_error",
  "severity": "low",
  "action": "return_validation_error",
  "priority": 4,
  "metadata": {
    "user_facing": true,
    "severity": "low",
    "analysis": "Detected validation-related keywords"
  }
}
```

### 2. Decide Action

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

### 3. Execute Action

```bash
curl -X POST http://localhost:8000/agent/execute-action/ \
  -H "Content-Type: application/json" \
  -d '{
    "action": "notify_admin",
    "priority": 2,
    "event_type": "system_error",
    "severity": "medium",
    "message": "Database connection timeout",
    "context": {"database": "postgres"}
  }'
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

### 4. Validate Payload

```bash
curl -X POST http://localhost:8000/agent/validate-payload/ \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {"username": "john", "email": "john@example.com"},
    "required_fields": ["username", "email", "password"]
  }'
```

**Response:**
```json
{
  "is_valid": false,
  "missing_fields": ["password"],
  "message": "Missing required fields: password"
}
```

## 🏗️ Architecture

```
IBOA/
├── agents/                      # Main application
│   ├── services/               # Core agent services
│   │   ├── ai_agent_service.py    # Analysis & Orchestrator agents
│   │   ├── event_router.py        # Event routing logic
│   │   ├── validation_module.py   # Payload validation
│   │   └── exception_middleware.py # Exception handling
│   ├── views.py                # API endpoints
│   ├── serializers.py          # Request/response serializers
│   └── urls.py                 # URL routing
├── iboa_server/                # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── manage.py
├── requirements.txt
├── openapi.yaml                # OpenAPI specification
└── .env.example                # Environment template
```

## 🤖 Agent System

### Analysis Agent

Classifies events into categories:
- `validation_error` - Input validation issues
- `system_error` - System-level errors
- `security_issue` - Security-related events
- `ignorable` - Low-priority events

Severity levels: `low`, `medium`, `high`

### Orchestrator Agent

Determines actions based on analysis:
- `log_only` - Simple logging (priority 5)
- `return_validation_error` - User-facing validation errors (priority 4)
- `log_and_monitor` - System monitoring (priority 2-3)
- `alert_security_team` - Security alerts (priority 1)

## 🔌 IBM watsonx Integration

The system is designed for easy integration with IBM watsonx.ai models. Update [`agents/services/ai_agent_service.py`](agents/services/ai_agent_service.py) to enable AI-powered classification:

```python
# Initialize with watsonx config
watsonx_config = {
    'api_key': 'your-api-key',
    'project_id': 'your-project-id',
    'url': 'https://us-south.ml.cloud.ibm.com',
    'model_id': 'ibm/granite-13b-chat-v2'
}

service = AIAgentService(watsonx_config)
```

Currently uses rule-based classification as fallback. See code comments for watsonx integration points.

## 🧪 Testing

```bash
# Run Django tests
python manage.py test

# Test specific app
python manage.py test agents

# Test with coverage
pip install coverage
coverage run --source='.' manage.py test
coverage report
```

## 📦 Deployment

### Production Checklist

- [ ] Set `DEBUG=False` in settings
- [ ] Configure proper `SECRET_KEY`
- [ ] Set up PostgreSQL database
- [ ] Configure `ALLOWED_HOSTS`
- [ ] Set up Redis for caching
- [ ] Enable rate limiting
- [ ] Configure CORS if needed
- [ ] Set up logging
- [ ] Use gunicorn for WSGI server
- [ ] Set up reverse proxy (nginx)
- [ ] Configure SSL/TLS

### Using Gunicorn

```bash
# Install gunicorn
pip install gunicorn

# Run with gunicorn
gunicorn iboa_server.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN python manage.py collectstatic --noinput

CMD ["gunicorn", "iboa_server.wsgi:application", "--bind", "0.0.0.0:8000"]
```

## 🔒 Security Considerations

⚠️ **Important Security Notes:**
- Always use environment variables for sensitive data
- Never commit `.env` file to version control
- Use strong `SECRET_KEY` in production
- Enable HTTPS in production
- Implement rate limiting for public endpoints
- Validate and sanitize all inputs
- Review payload data for sensitive information

## 📊 Event Categories & Actions

| Category | Severity | Default Action | Priority |
|----------|----------|----------------|----------|
| Security Issue | High | Alert Security Team | 1 |
| System Error | Medium/High | Log and Monitor | 2-3 |
| Validation Error | Low | Return to User | 4 |
| Ignorable | Low | Log Only | 5 |

## 🛠️ Development

### Adding New Endpoints

1. Define serializer in [`agents/serializers.py`](agents/serializers.py)
2. Create view in [`agents/views.py`](agents/views.py)
3. Add URL pattern in [`agents/urls.py`](agents/urls.py)
4. Update OpenAPI schema if needed

### Extending Agent Logic

Modify [`agents/services/ai_agent_service.py`](agents/services/ai_agent_service.py):
- Add new event categories to `EventCategory` enum
- Extend classification logic in `AnalysisAgent`
- Add action types in `OrchestratorAgent`

## 📝 Requirements

See [`requirements.txt`](requirements.txt) for full dependency list:

- Django 4.2+
- Django REST Framework 3.14+
- drf-spectacular (OpenAPI documentation)
- django-ratelimit (rate limiting)
- gunicorn (production server)
- psycopg2-binary (PostgreSQL)
- redis (caching)
- celery (async tasks)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is provided as-is for use in your applications.

## 🆘 Support

For issues and questions:
- Check the API documentation at `/api/schema/swagger-ui/`
- Review the code documentation in source files
- Test endpoints using the health check endpoint

## 🎉 Acknowledgments

Built for hackathons, ready for production. Designed for easy integration with IBM watsonx.ai.

---

**IBOA - Intelligent Backend Operations Agent** 🤖
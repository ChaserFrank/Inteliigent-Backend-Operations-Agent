"""
Django Custom Exception Middleware for AI Agent Integration

This middleware captures all unhandled exceptions, collects structured context,
and sends the data to an external AI agent service for analysis.

Production-safe and works with DEBUG = False.
"""

import json
import logging
import traceback
from typing import Optional, Dict, Any
from datetime import datetime

import requests
from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin
from django.core.exceptions import MiddlewareNotUsed

logger = logging.getLogger(__name__)


class AIAgentExceptionMiddleware(MiddlewareMixin):
    """
    Middleware that captures unhandled exceptions and sends them to an AI agent service.
    
    This middleware:
    - Catches all unhandled exceptions (500 errors)
    - Collects structured context about the request and exception
    - Sends data to external AI agent endpoint asynchronously
    - Does NOT interfere with Django's default error handling
    - Works in production (DEBUG = False)
    """
    
    def __init__(self, get_response):
        """Initialize the middleware with configuration validation."""
        super().__init__(get_response)
        
        # Get AI agent service configuration
        self.agent_endpoint = getattr(settings, 'AI_AGENT_ENDPOINT', None)
        self.agent_api_key = getattr(settings, 'AI_AGENT_API_KEY', None)
        self.agent_timeout = getattr(settings, 'AI_AGENT_TIMEOUT', 5)
        self.agent_enabled = getattr(settings, 'AI_AGENT_ENABLED', True)
        
        # Validate configuration
        if self.agent_enabled and not self.agent_endpoint:
            logger.warning(
                "AI_AGENT_ENDPOINT not configured. "
                "Exception data will be logged but not sent to agent service."
            )
            self.agent_enabled = False
        
        logger.info(
            f"AIAgentExceptionMiddleware initialized. "
            f"Enabled: {self.agent_enabled}, Endpoint: {self.agent_endpoint}"
        )
    
    def process_exception(self, request: HttpRequest, exception: Exception) -> Optional[HttpResponse]:
        """
        Process unhandled exceptions and send to AI agent service.
        
        Args:
            request: The Django HttpRequest object
            exception: The unhandled exception that was raised
            
        Returns:
            None - allows Django's default exception handling to continue
        """
        try:
            # Collect structured exception context
            exception_data = self._collect_exception_context(request, exception)
            
            # Log the exception locally
            logger.error(
                f"Unhandled exception: {exception_data['exception_type']}",
                extra={'exception_data': exception_data},
                exc_info=True
            )
            
            # Send to AI agent service if enabled
            if self.agent_enabled:
                self._send_to_agent_service(exception_data)
        
        except Exception as e:
            # Never let middleware errors break the application
            logger.error(
                f"Error in AIAgentExceptionMiddleware: {str(e)}",
                exc_info=True
            )
        
        # Return None to allow Django's default exception handling to proceed
        return None
    
    def _collect_exception_context(self, request: HttpRequest, exception: Exception) -> Dict[str, Any]:
        """
        Collect structured context about the exception and request.
        
        Args:
            request: The Django HttpRequest object
            exception: The exception that was raised
            
        Returns:
            Dictionary containing structured exception context
        """
        # Get authenticated user info
        user_info = self._get_user_info(request)
        
        # Get request metadata
        request_meta = {
            'path': request.path,
            'method': request.method,
            'content_type': request.content_type,
            'query_params': dict(request.GET),
            'remote_addr': self._get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', 'Unknown'),
        }
        
        # Safely get request body (if available)
        request_body = self._get_request_body(request)
        
        # Get exception details
        exception_info = {
            'type': type(exception).__name__,
            'message': str(exception),
            'module': type(exception).__module__,
            'traceback': traceback.format_exc(),
            'traceback_list': traceback.format_tb(exception.__traceback__),
        }
        
        # Construct complete context
        context = {
            'timestamp': datetime.utcnow().isoformat(),
            'environment': 'production' if not settings.DEBUG else 'development',
            'request': request_meta,
            'request_body': request_body,
            'user': user_info,
            'exception': exception_info,
            'server': {
                'hostname': getattr(settings, 'HOSTNAME', 'unknown'),
                'version': getattr(settings, 'VERSION', 'unknown'),
            }
        }
        
        return context
    
    def _get_user_info(self, request: HttpRequest) -> Dict[str, Any]:
        """
        Extract authenticated user information safely.
        
        Args:
            request: The Django HttpRequest object
            
        Returns:
            Dictionary containing user information
        """
        user_info = {
            'authenticated': False,
            'id': None,
            'username': None,
            'email': None,
        }
        
        try:
            if hasattr(request, 'user') and request.user.is_authenticated:
                user_info.update({
                    'authenticated': True,
                    'id': request.user.id,
                    'username': getattr(request.user, 'username', None),
                    'email': getattr(request.user, 'email', None),
                })
        except Exception as e:
            logger.warning(f"Error extracting user info: {str(e)}")
        
        return user_info
    
    def _get_client_ip(self, request: HttpRequest) -> str:
        """
        Get the client's IP address, handling proxies.
        
        Args:
            request: The Django HttpRequest object
            
        Returns:
            Client IP address as string
        """
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'Unknown')
    
    def _get_request_body(self, request: HttpRequest) -> Optional[str]:
        """
        Safely extract request body.
        
        Args:
            request: The Django HttpRequest object
            
        Returns:
            Request body as string or None
        """
        try:
            if request.method in ['POST', 'PUT', 'PATCH']:
                # Try to get body, but don't fail if already consumed
                if hasattr(request, 'body'):
                    body = request.body.decode('utf-8')
                    # Limit body size to prevent huge payloads
                    max_body_size = getattr(settings, 'AI_AGENT_MAX_BODY_SIZE', 10000)
                    if len(body) > max_body_size:
                        return f"[Body too large: {len(body)} bytes]"
                    return body
        except Exception as e:
            logger.debug(f"Could not extract request body: {str(e)}")
        
        return None
    
    def _send_to_agent_service(self, exception_data: Dict[str, Any]) -> None:
        """
        Send exception data to AI agent service asynchronously.
        
        Args:
            exception_data: Structured exception context
        """
        try:
            headers = {
                'Content-Type': 'application/json',
            }
            
            # Add API key if configured
            if self.agent_api_key:
                headers['Authorization'] = f'Bearer {self.agent_api_key}'
            
            # Send POST request to agent service
            response = requests.post(
                self.agent_endpoint,
                json=exception_data,
                headers=headers,
                timeout=self.agent_timeout,
            )
            
            if response.status_code == 200:
                logger.info(
                    f"Exception data sent to AI agent service successfully. "
                    f"Exception: {exception_data['exception']['type']}"
                )
            else:
                logger.warning(
                    f"AI agent service returned status {response.status_code}. "
                    f"Response: {response.text[:200]}"
                )
        
        except requests.exceptions.Timeout:
            logger.warning(
                f"Timeout sending exception to AI agent service "
                f"(timeout: {self.agent_timeout}s)"
            )
        
        except requests.exceptions.RequestException as e:
            logger.warning(
                f"Error sending exception to AI agent service: {str(e)}"
            )
        
        except Exception as e:
            logger.error(
                f"Unexpected error in _send_to_agent_service: {str(e)}",
                exc_info=True
            )


class AsyncAIAgentExceptionMiddleware(AIAgentExceptionMiddleware):
    """
    Async version of the middleware for better performance.
    
    Sends exception data to AI agent service in a background thread
    to avoid blocking the request/response cycle.
    """
    
    def _send_to_agent_service(self, exception_data: Dict[str, Any]) -> None:
        """
        Send exception data asynchronously using threading.
        
        Args:
            exception_data: Structured exception context
        """
        import threading
        
        def send_async():
            super(AsyncAIAgentExceptionMiddleware, self)._send_to_agent_service(
                exception_data
            )
        
        # Start background thread
        thread = threading.Thread(target=send_async, daemon=True)
        thread.start()
        
        logger.debug("Exception data queued for async sending to AI agent service")
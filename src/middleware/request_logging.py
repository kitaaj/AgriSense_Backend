from flask import request, g
import time
import logging
from functools import wraps

logger = logging.getLogger(__name__)

def setup_request_logging(app):
    """Setup request logging for the Flask app"""
    
    @app.before_request
    def before_request():
        print(f"*** BEFORE REQUEST: {request.method} {request.url} ***")
        """Log request start and set timing"""
        g.start_time = time.time()
        
        # Log request details (excluding sensitive data)
        log_data = {
            'method': request.method,
            'url': request.url,
            'remote_addr': request.remote_addr,
            'user_agent': request.headers.get('User-Agent', 'Unknown')
        }
        
        # Don't log sensitive endpoints in detail
        sensitive_endpoints = ['/api/auth/login', '/api/auth/register']
        if request.endpoint not in sensitive_endpoints:
            # ONLY try to get JSON if it's a POST, PUT, or PATCH request
            if request.method in ['POST', 'PUT', 'PATCH'] and request.is_json and request.data:
                try:
                    body = request.get_json()
                    if body and isinstance(body, dict):
                        safe_body = {k: v for k, v in body.items() if 'password' not in k.lower()}
                        log_data['body'] = safe_body
                except Exception as e:
                    # Log the error but don't re-raise, let the request continue
                    logger.warning(f"Failed to parse JSON body in before_request: {e}")
        
        logger.info(f"Request started: {log_data}")
    
    @app.after_request
    def after_request(response):

        print(f"*** AFTER REQUEST: {request.method} {request.url} Status: {response.status_code} ***")
        """Log request completion and timing"""
        if hasattr(g, 'start_time'):
            duration = time.time() - g.start_time
            
            log_data = {
                'method': request.method,
                'url': request.url,
                'status_code': response.status_code,
                'duration_ms': round(duration * 1000, 2)
            }
            
            # Log level based on status code
            if response.status_code >= 500:
                logger.error(f"Request completed: {log_data}")
            elif response.status_code >= 400:
                logger.warning(f"Request completed: {log_data}")
            else:
                logger.info(f"Request completed: {log_data}")
        
        return response

def log_api_call(endpoint_name):
    """Decorator to log specific API calls with additional context"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                logger.info(f"API call successful: {endpoint_name} - Duration: {duration:.3f}s")
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"API call failed: {endpoint_name} - Duration: {duration:.3f}s - Error: {str(e)}")
                raise
                
        return wrapper
    return decorator


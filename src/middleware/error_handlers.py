from flask import jsonify
from werkzeug.exceptions import HTTPException
from flask_jwt_extended.exceptions import JWTExtendedException
import logging

logger = logging.getLogger(__name__)

def register_error_handlers(app):
    """Register error handlers for the Flask app"""
    
    @app.errorhandler(400)
    def bad_request(error):
        """Handle 400 Bad Request errors"""
        return jsonify({
            'error': 'Bad Request',
            'message': 'The request could not be understood by the server',
            'status_code': 400
        }), 400
    
    @app.errorhandler(401)
    def unauthorized(error):
        """Handle 401 Unauthorized errors"""
        return jsonify({
            'error': 'Unauthorized',
            'message': 'Authentication is required to access this resource',
            'status_code': 401
        }), 401
    
    @app.errorhandler(403)
    def forbidden(error):
        """Handle 403 Forbidden errors"""
        return jsonify({
            'error': 'Forbidden',
            'message': 'You do not have permission to access this resource',
            'status_code': 403
        }), 403
    
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 Not Found errors"""
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found',
            'status_code': 404
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        """Handle 405 Method Not Allowed errors"""
        return jsonify({
            'error': 'Method Not Allowed',
            'message': 'The method is not allowed for the requested URL',
            'status_code': 405
        }), 405
    
    @app.errorhandler(409)
    def conflict(error):
        """Handle 409 Conflict errors"""
        return jsonify({
            'error': 'Conflict',
            'message': 'The request could not be completed due to a conflict',
            'status_code': 409
        }), 409
    
    @app.errorhandler(422)
    def unprocessable_entity(error):
        """Handle 422 Unprocessable Entity errors"""
        return jsonify({
            'error': 'Unprocessable Entity',
            'message': 'The request was well-formed but contains semantic errors',
            'status_code': 422
        }), 422
    
    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        """Handle 429 Too Many Requests errors"""
        return jsonify({
            'error': 'Rate Limit Exceeded',
            'message': 'Too many requests. Please try again later',
            'status_code': 429
        }), 429
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """Handle 500 Internal Server Error"""
        logger.error(f"Internal server error: {str(error)}")
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred on the server',
            'status_code': 500
        }), 500
    
    @app.errorhandler(502)
    def bad_gateway(error):
        """Handle 502 Bad Gateway errors"""
        return jsonify({
            'error': 'Bad Gateway',
            'message': 'The server received an invalid response from an upstream server',
            'status_code': 502
        }), 502
    
    @app.errorhandler(503)
    def service_unavailable(error):
        """Handle 503 Service Unavailable errors"""
        return jsonify({
            'error': 'Service Unavailable',
            'message': 'The service is temporarily unavailable. Please try again later',
            'status_code': 503
        }), 503
    
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        """Handle generic HTTP exceptions"""
        return jsonify({
            'error': error.name,
            'message': error.description,
            'status_code': error.code
        }), error.code
    
    @app.errorhandler(JWTExtendedException)
    def handle_jwt_exceptions(error):
        """Handle JWT-related exceptions"""
        logger.warning(f"JWT error: {str(error)}")
        return jsonify({
            'error': 'Authentication Error',
            'message': 'Invalid or expired authentication token',
            'status_code': 401
        }), 401
    
    @app.errorhandler(ValueError)
    def handle_value_error(error):
        """Handle ValueError exceptions"""
        logger.error(f"Value error: {str(error)}")
        return jsonify({
            'error': 'Invalid Value',
            'message': 'Invalid input value provided',
            'status_code': 400
        }), 400
    
    @app.errorhandler(KeyError)
    def handle_key_error(error):
        """Handle KeyError exceptions"""
        logger.error(f"Key error: {str(error)}")
        return jsonify({
            'error': 'Missing Required Field',
            'message': f'Required field is missing: {str(error)}',
            'status_code': 400
        }), 400
    
    @app.errorhandler(Exception)
    def handle_generic_exception(error):
        """Handle any unhandled exceptions"""
        logger.error(f"Unhandled exception: {str(error)}", exc_info=True)
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred',
            'status_code': 500
        }), 500


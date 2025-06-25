"""
CORS Handler Lambda for OPTIONS requests
This Lambda function handles all OPTIONS (CORS preflight) requests to maintain appropriate CORS headers.
"""

import json
import os
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Get allowed origins from environment variables
ALLOWED_ORIGINS = os.environ.get('ALLOWED_ORIGINS', '').split(',')

def is_origin_allowed(origin: str) -> bool:
    """Check if the provided origin is allowed"""
    if not origin:
        return False
    
    # Environment check for development mode
    env = os.environ.get('ENVIRONMENT', 'dev')
    
    # Always allow localhost origins in development environment
    if env.lower() in ('dev', 'development'):
        if 'localhost' in origin or '127.0.0.1' in origin:
            return True
        
    # Strip any trailing slash for comparison
    if origin.endswith('/'):
        origin = origin[:-1]
        
    # Direct match check
    if origin in ALLOWED_ORIGINS:
        return True
                
    return False

def lambda_handler(event, context):
    """
    Simple handler for OPTIONS requests that returns the necessary CORS headers.
    This enables preflight requests to succeed for all endpoints.
    """
    # Log the event for debugging
    logger.info(f"CORS Handler Event: {json.dumps(event)}")
    
    # Extract origin from headers if available
    headers = event.get('headers', {}) or {}
    if not headers:
        logger.warning("No headers found in event")
        
    # Convert header keys to lowercase for case-insensitive matching
    headers_lower = {k.lower(): v for k, v in headers.items()}
    
    # Get the origin with fallback to localhost
    origin = headers_lower.get('origin', headers_lower.get('Origin', 'http://localhost:5173'))
    
    # Log debugging info
    logger.info(f"Request origin: {origin}")
    logger.info(f"Request path: {event.get('path')}")
    logger.info(f"Request method: {event.get('httpMethod')}")
    
    # Check if the origin is one of our allowed origins
    allowed_origins = ['http://localhost:5173', 'http://localhost:3000']
    
    # Only allow specific origins when credentials are enabled
    if origin in allowed_origins or is_origin_allowed(origin):
        allowed_origin = origin  # Echo back the specific origin
    else:
        # Default to localhost:5173 if not recognized in development
        env = os.environ.get('ENVIRONMENT', 'dev')
        if env.lower() in ('dev', 'development'):
            allowed_origin = 'http://localhost:5173'
        else:
            allowed_origin = allowed_origins[0] if allowed_origins else 'https://myai4.co.uk'
        logger.warning(f"Unrecognized origin: {origin}, defaulting to {allowed_origin}")
    
    # Get any requested headers if provided
    requested_headers = headers_lower.get('access-control-request-headers', 
                                         'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-CSRF-Token,X-Requested-With')
    
    cors_headers = {
        "Access-Control-Allow-Origin": allowed_origin,
        "Access-Control-Allow-Headers": requested_headers,
        "Access-Control-Allow-Methods": "OPTIONS,GET,PUT,POST,DELETE",
        "Access-Control-Allow-Credentials": "true",
        # Cache preflight for 24 hours to improve performance
        "Access-Control-Max-Age": "86400",
        # Add cache control to prevent browsers from caching the CORS response
        "Cache-Control": "no-cache"
    }
    
    # Return a proper OPTIONS response
    response = {
        "statusCode": 200,
        "headers": cors_headers,
        "body": json.dumps({"message": "CORS preflight successful"})
    }
    
    logger.info(f"Returning CORS response: {json.dumps(response)}")
    return response

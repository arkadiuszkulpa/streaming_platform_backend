import json
import os
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

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
    
    # For development purposes, allow all origins
    cors_headers = {
        "Access-Control-Allow-Origin": origin,
        "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-CSRF-Token,X-Requested-With",
        "Access-Control-Allow-Methods": "OPTIONS,GET,PUT,POST,DELETE",
        "Access-Control-Allow-Credentials": "true",
        # Add cache control to prevent browsers from caching the CORS response
        "Cache-Control": "no-cache"
    }
    
    # Return a proper OPTIONS response
    return {
        "statusCode": 200,
        "headers": cors_headers,
        "body": json.dumps({})
    }

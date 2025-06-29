"""
CORS OPTIONS Handler for MyAI4 API Gateway
Handles all CORS preflight requests with dynamic origin validation
"""

import os
import json

def lambda_handler(event, context):
    """
    Handle CORS preflight OPTIONS requests
    Supports dynamic origin validation based on environment configuration
    """
    
    # Get environment and origin configuration
    environment = os.environ.get('ENVIRONMENT', 'dev')
    cloudfront_domain = os.environ.get('CLOUDFRONT_DOMAIN', '')
    local_origins_str = os.environ.get('LOCAL_ORIGINS', '')
    
    # Extract origin from request headers (case-insensitive)
    headers = {k.lower(): v for k, v in event.get('headers', {}).items()}
    origin = headers.get('origin', '')
    
    # Enhanced debugging
    print(f"=== CORS OPTIONS DEBUG ===")
    print(f"Environment: {environment}")
    print(f"CloudFront Domain Raw: '{cloudfront_domain}'")
    print(f"Local Origins Raw: '{local_origins_str}'")
    print(f"Request Origin: '{origin}'")
    print(f"Path: {event.get('path', 'unknown')}")
    print(f"Method: {event.get('httpMethod', 'unknown')}")
    
    # Build allowed origins list
    allowed_origins = []
    
    # Always add CloudFront domain if available
    if cloudfront_domain:
        # Ensure we have the full URL format - add https:// if not present
        if cloudfront_domain.startswith('http'):
            allowed_origins.append(cloudfront_domain)
        else:
            allowed_origins.append(f"https://{cloudfront_domain}")
    
    # Add localhost origins for dev environment or any environment (for debugging)
    if local_origins_str:
        local_origins = [o.strip() for o in local_origins_str.split(',') if o.strip()]
        allowed_origins.extend(local_origins)
    
    print(f"Allowed Origins: {allowed_origins}")
    
    # Determine which origin to use
    cors_origin = "*"  # fallback
    if origin and origin in allowed_origins:
        cors_origin = origin
        print(f"✅ CORS - Exact match for origin: {origin}")
    elif allowed_origins:
        cors_origin = allowed_origins[0]  # Use first allowed as fallback
        print(f"⚠️ CORS - Using fallback origin: {cors_origin} (requested: {origin})")
    else:
        print(f"❌ CORS - No allowed origins configured, using wildcard")
    
    # Build CORS headers
    cors_headers = {
        "Access-Control-Allow-Origin": cors_origin,
        "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token,X-CSRF-Token,X-Requested-With",
        "Access-Control-Allow-Credentials": "true"
    }
    
    print(f"Final CORS Headers: {cors_headers}")
    print(f"=== END CORS OPTIONS DEBUG ===")
    
    # Return successful OPTIONS response
    response = {
        "statusCode": 200,
        "headers": cors_headers
    }
    
    print(f"OPTIONS Response: {json.dumps(response, indent=2)}")
    
    return response

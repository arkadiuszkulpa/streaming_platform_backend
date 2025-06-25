import json

def lambda_handler(event, context):
    """
    Simple handler for OPTIONS requests that returns the necessary CORS headers.
    This enables preflight requests to succeed for all endpoints.
    """
    # Extract origin from headers if available
    headers = event.get('headers', {})
    origin = headers.get('origin') or headers.get('Origin') or 'http://localhost:5173'
    
    return {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,X-CSRF-Token",
            "Access-Control-Allow-Methods": "OPTIONS,GET,PUT,POST,DELETE",
            "Access-Control-Allow-Credentials": "true"
        },
        "body": json.dumps({})
    }

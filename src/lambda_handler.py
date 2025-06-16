"""
Enhanced handle_test function for lambda_handler.py
This provides more comprehensive diagnostic information for troubleshooting API connectivity.
The backend team should incorporate this into their lambda_handler.py file.

INTEGRATION INSTRUCTIONS:
1. Copy this function into lambda_handler.py
2. Remove the import statements if they're already present
3. Remove the mock implementations of variables
4. Add 'ENVIRONMENT': environment to the Lambda environment variables in template-backend.yaml
"""

# Required imports - remove these when integrating if already present in lambda_handler.py
import os
import json
import boto3
from datetime import datetime
from typing import Dict, Any
from botocore.exceptions import ClientError

# Mock implementations of variables and functions - remove when integrating into lambda_handler.py
# In the actual Lambda function, these would be defined elsewhere
dynamodb = boto3.resource('dynamodb')

# Mock environment variables - these are populated from CloudFormation in the actual Lambda
USER_PROFILES_TABLE = os.environ.get('USER_PROFILES_TABLE', 'myai4-user-profiles')
SUBSCRIPTIONS_TABLE = os.environ.get('SUBSCRIPTIONS_TABLE', 'myai4-subscriptions') 
SERVICE_PREFERENCES_TABLE = os.environ.get('SERVICE_PREFERENCES_TABLE', 'myai4-service-preferences')
USER_USAGE_TABLE = os.environ.get('USER_USAGE_TABLE', 'myai4-user-usage')
FAMILY_GROUPS_TABLE = os.environ.get('FAMILY_GROUPS_TABLE', 'myai4-family-groups')
MOVIES_TABLE = os.environ.get('MOVIES_TABLE', 'myai4-movies')
WATCHLISTS_TABLE = os.environ.get('WATCHLISTS_TABLE', 'myai4-watchlists')
WATCH_HISTORY_TABLE = os.environ.get('WATCH_HISTORY_TABLE', 'myai4-watch-history')
STREAMING_PROFILES_TABLE = os.environ.get('STREAMING_PROFILES_TABLE', 'myai4-streaming-profiles')

# Mock RapidAPI key function - remove when integrating
def get_rapidapi_key():
    """Mock implementation - in the real Lambda, this would get the key from Secrets Manager"""
    if not os.environ.get('RAPIDAPI_SECRET_NAME'):
        raise ValueError("RAPIDAPI_SECRET_NAME environment variable not set")
    return "mock-api-key"

def handle_test(data: Dict[str, Any]) -> Dict[str, Any]:
    """Test handler for API connectivity and diagnostics"""
    # Get the Lambda function name from the context
    function_name = os.environ.get('AWS_LAMBDA_FUNCTION_NAME', 'unknown')
    environment = os.environ.get('ENVIRONMENT', 'unknown')
    
    # Check if we can access DynamoDB tables
    table_status = {}
    warnings = []
    messages = []
    
    # Check for required environment variables
    for env_var in [
        'USER_PROFILES_TABLE', 'SUBSCRIPTIONS_TABLE', 'SERVICE_PREFERENCES_TABLE',
        'USER_USAGE_TABLE', 'FAMILY_GROUPS_TABLE', 'MOVIES_TABLE',
        'WATCHLISTS_TABLE', 'WATCH_HISTORY_TABLE', 'STREAMING_PROFILES_TABLE',
        'RAPIDAPI_SECRET_NAME'
    ]:
        if not os.environ.get(env_var):
            warnings.append(f"Environment variable {env_var} is not set")
    
    # Check all tables
    for table_name, table_var in {
        'USER_PROFILES_TABLE': USER_PROFILES_TABLE,
        'SUBSCRIPTIONS_TABLE': SUBSCRIPTIONS_TABLE,
        'SERVICE_PREFERENCES_TABLE': SERVICE_PREFERENCES_TABLE,
        'USER_USAGE_TABLE': USER_USAGE_TABLE,
        'FAMILY_GROUPS_TABLE': FAMILY_GROUPS_TABLE,
        'MOVIES_TABLE': MOVIES_TABLE,
        'WATCHLISTS_TABLE': WATCHLISTS_TABLE,
        'WATCH_HISTORY_TABLE': WATCH_HISTORY_TABLE,
        'STREAMING_PROFILES_TABLE': STREAMING_PROFILES_TABLE,
    }.items():
        if table_var:
            try:
                table = dynamodb.Table(table_var)
                # Get more detailed table information
                table_details = table.meta.client.describe_table(TableName=table_var)
                
                table_status[table_name] = {
                    'status': 'accessible',
                    'name': table_var,
                    'details': {
                        'item_count': table_details['Table'].get('ItemCount', 'unknown'),
                        'table_status': table_details['Table'].get('TableStatus', 'unknown'),
                        'size_bytes': table_details['Table'].get('TableSizeBytes', 'unknown')
                    }
                }
            except Exception as e:
                table_status[table_name] = {
                    'status': 'error',
                    'message': str(e),
                    'name': table_var
                }
                warnings.append(f"Cannot access table {table_var}: {str(e)}")
        else:
            table_status[table_name] = {
                'status': 'not_configured',
                'name': None
            }
            messages.append(f"Table {table_name} is not configured")
    
    # Check for RapidAPI key
    try:
        _ = get_rapidapi_key()
        messages.append("RapidAPI key is accessible")
    except Exception as e:
        warnings.append(f"Cannot access RapidAPI key: {str(e)}")
    
    # Get Lambda execution environment
    execution_env = os.environ.get('AWS_EXECUTION_ENV', 'unknown')
    
    return {
        'message': 'MyAI4 Centralized API is operational',
        'timestamp': datetime.utcnow().isoformat(),
        'request_time': datetime.utcnow().isoformat(),
        'data_received': data,
        'function': function_name,
        'lambda_name': function_name,
        'region': os.environ.get('AWS_REGION', 'unknown'),
        'version': os.environ.get('AWS_LAMBDA_FUNCTION_VERSION', 'unknown'),
        'memory': os.environ.get('AWS_LAMBDA_FUNCTION_MEMORY_SIZE', 'unknown'),
        'execution_environment': execution_env,
        'environment': environment,
        'tables': table_status,
        'api_version': '1.0.0',
        'warnings': warnings,
        'messages': messages
    }

"""
MyAI4 Subscription Lambda Handler
This Lambda function handles subscription-related operations for the myAI4 platform.
It provides functionality to manage user subscriptions across all myAI4 services.
"""
import json
import os
import boto3
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from botocore.exceptions import ClientError

# Initialize AWS resources
dynamodb = boto3.resource('dynamodb')

# Environment variables - only those needed for subscription operations
ACCOUNT_TABLE = os.environ.get('ACCOUNT_TABLE')  # For account verification
SUBSCRIPTION_TABLE = os.environ.get('SUBSCRIPTION_TABLE')  # Core table for this Lambda
USER_USAGE_TABLE = os.environ.get('USER_USAGE_TABLE')  # For optional usage tracking

# Authentication-related environment variables
USER_POOL_ID = os.environ.get('USER_POOL_ID')  # For verifying JWT tokens if handling auth directly
IDENTITY_POOL_ID = os.environ.get('IDENTITY_POOL_ID')  # For client-side authentication


def get_rapidapi_key():
    """Get RapidAPI key from AWS Secrets Manager"""
    secret_name = os.environ.get('RAPIDAPI_SECRET_NAME')
    if not secret_name:
        raise ValueError("RAPIDAPI_SECRET_NAME environment variable not set")
    
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name='secretsmanager')
    
    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
    except ClientError as error:
        print(f"Error retrieving secret {secret_name}: {str(error)}")
        raise error
    
    # Depending on whether the secret is a string or binary, one of these fields will be populated
    if 'SecretString' in get_secret_value_response:
        secret = get_secret_value_response['SecretString']
        # Parse the JSON string
        secret_dict = json.loads(secret)
        # Return the specific key value
        return secret_dict.get('rapidapikey')
    else:
        raise ValueError("Secret value is not in string format")


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
        'ACCOUNT_TABLE', 'SUBSCRIPTION_TABLE',
        'USER_USAGE_TABLE', 'RAPIDAPI_SECRET_NAME', 'ENVIRONMENT',
        'USER_POOL_ID', 'IDENTITY_POOL_ID'
    ]:
        if not os.environ.get(env_var):
            warnings.append(f"Environment variable {env_var} not configured")
    
    # Check all tables
    for table_name, table_var in {
        'ACCOUNT_TABLE': ACCOUNT_TABLE,
        'SUBSCRIPTION_TABLE': SUBSCRIPTION_TABLE,
        'USER_USAGE_TABLE': USER_USAGE_TABLE,
    }.items():
        if table_var:
            try:
                table = dynamodb.Table(table_var)
                item_count = table.scan(Select='COUNT')['Count']
                table_status[table_name] = {
                    'status': 'accessible',
                    'name': table_var,
                    'item_count': item_count
                }
                messages.append(f"Table {table_var} contains {item_count} items")
            except ClientError as e:
                table_status[table_name] = {
                    'status': 'error',
                    'name': table_var,
                    'error': str(e)
                }
                warnings.append(f"Error accessing table {table_var}: {str(e)}")
        else:
            table_status[table_name] = {
                'status': 'not_configured',
                'error': 'Environment variable not set'
            }
            warnings.append(f"Table {table_name} not configured (missing env variable)")
    
    # Check infrastructure resources
    parameter_status = {}
    if IDENTITY_POOL_ID:
        parameter_status['IDENTITY_POOL_ID'] = {
            'status': 'accessible',
            'value': IDENTITY_POOL_ID
        }
    else:
        parameter_status['IDENTITY_POOL_ID'] = {
            'status': 'missing',
            'error': 'Environment variable not set'
        }
    
    # Check for RapidAPI key
    try:
        _ = get_rapidapi_key()
        messages.append("RapidAPI key is accessible")
    except Exception as e:
        warnings.append(f"Cannot access RapidAPI key: {str(e)}")
    
    # Get Lambda execution environment
    execution_env = os.environ.get('AWS_EXECUTION_ENV', 'unknown')
    
    return {
        'message': 'MyAI4 Subscription API is operational',
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
        'parameters': parameter_status,
        'api_version': '1.0.0',
        'warnings': warnings,
        'messages': messages
    }


def create_response(status_code: int, body: Dict[str, Any]) -> Dict[str, Any]:
    """Create an API Gateway response object"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',  # For CORS support
            'Access-Control-Allow-Headers': 'Content-Type,Authorization',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS'
        },
        'body': json.dumps(body)
    }


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Subscription Lambda handler for myAI4 platform
    Handles operations related to user subscriptions across myAI4 services
    """
    try:
        # Check for OPTIONS request (CORS preflight)
        if event.get('httpMethod') == 'OPTIONS':
            return create_response(200, {'message': 'CORS preflight successful'})
        
        # Parse the operation from query parameters or request body
        http_method = event.get('httpMethod', 'GET')
        
        if http_method == 'GET':
            # For GET requests, look for operation in query parameters
            query_params = event.get('queryStringParameters', {}) or {}
            operation = query_params.get('operation')
            data = query_params
        else:
            # For other HTTP methods, look for operation in body
            body = event.get('body', '{}')
            if isinstance(body, str):
                body_json = json.loads(body)
            else:
                body_json = body
                
            operation = body_json.get('operation')
            data = body_json
            
        if not operation:
            return create_response(400, {'error': 'Missing operation parameter'})
            
        # Route to appropriate handler
        if operation == 'test':
            result = handle_test(data)
        elif operation == 'getSubscriptions':
            result = handle_get_subscriptions(data)
        elif operation == 'getSubscription':
            result = handle_get_subscription(data)
        elif operation == 'createSubscription':
            result = handle_create_subscription(data)
        elif operation == 'updateSubscription':
            result = handle_update_subscription(data)
        elif operation == 'cancelSubscription':
            result = handle_cancel_subscription(data)
        else:
            result = {'error': f"Unknown operation: {operation}"}
            return create_response(400, result)
        
        if result.get('statusCode'):
            # If result already has a statusCode, use it
            status_code = result.pop('statusCode')
            return create_response(status_code, result)
        else:
            # Default to 200 OK
            return create_response(200, result)
            
    except Exception as e:
        error_message = str(e)
        print(f"Error in lambda_handler: {error_message}")
        return create_response(500, {
            'error': 'Internal server error',
            'details': error_message
        })


def handle_get_subscriptions(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for getSubscriptions operation
    Retrieves all subscriptions for a user account
    
    Expected data:
    - accountId (required): The account ID of the user
    - serviceType (optional): Filter by service type
    """
    # Validate required parameters
    if not data.get('accountId'):
        return {'error': 'Missing required parameter: accountId', 'statusCode': 400}
    
    accountId = data['accountId']
    service_type = data.get('serviceType')
    
    if not SUBSCRIPTION_TABLE:
        return {'error': 'Subscription table not configured', 'statusCode': 500}
    
    try:
        # Check if account exists
        if ACCOUNT_TABLE:
            account_table = dynamodb.Table(ACCOUNT_TABLE)
            account_response = account_table.get_item(
                Key={'userId': accountId}  # Using userId as key per your account table structure
            )
            if 'Item' not in account_response:
                return {'error': 'Account not found', 'statusCode': 404}
        
        # Query subscriptions for this account
        subscription_table = dynamodb.Table(SUBSCRIPTION_TABLE)
        
        if service_type:
            # Use Global Secondary Index to query by accountId and serviceType
            response = subscription_table.query(
                IndexName='ServiceTypeIndex',
                KeyConditionExpression='accountId = :accountId AND serviceType = :serviceType',
                ExpressionAttributeValues={
                    ':accountId': accountId,
                    ':serviceType': service_type
                }
            )
        else:
            # Query by accountId only
            response = subscription_table.query(
                KeyConditionExpression='accountId = :accountId',
                ExpressionAttributeValues={
                    ':accountId': accountId
                }
            )
        
        subscriptions = response.get('Items', [])
        
        return {
            'subscriptions': subscriptions,
            'count': len(subscriptions),
            'accountId': accountId,
            'serviceType': service_type if service_type else 'all'
        }
    except ClientError as e:
        print(f"DynamoDB error in getSubscriptions: {str(e)}")
        return {
            'error': 'Database error',
            'details': str(e),
            'statusCode': 500
        }
    except Exception as e:
        print(f"Unexpected error in getSubscriptions: {str(e)}")
        return {
            'error': 'An unexpected error occurred',
            'details': str(e),
            'statusCode': 500
        }


def handle_get_subscription(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for getSubscription operation
    Retrieves details for a specific subscription
    
    Expected data:
    - accountId (required): The account ID of the user
    - subscriptionId (required): The ID of the subscription to retrieve
    """
    # Validate required parameters
    if not data.get('accountId'):
        return {'error': 'Missing required parameter: accountId', 'statusCode': 400}
    if not data.get('subscriptionId'):
        return {'error': 'Missing required parameter: subscriptionId', 'statusCode': 400}
    
    accountId = data['accountId']
    subscriptionId = data['subscriptionId']
    
    if not SUBSCRIPTION_TABLE:
        return {'error': 'Subscription table not configured', 'statusCode': 500}
    
    try:
        subscription_table = dynamodb.Table(SUBSCRIPTION_TABLE)
        
        response = subscription_table.get_item(
            Key={
                'accountId': accountId,
                'subscriptionId': subscriptionId
            }
        )
        
        if 'Item' not in response:
            return {'error': 'Subscription not found', 'statusCode': 404}
        
        return {
            'subscription': response['Item'],
            'message': 'Subscription retrieved successfully'
        }
    except ClientError as e:
        print(f"DynamoDB error in getSubscription: {str(e)}")
        return {
            'error': 'Database error',
            'details': str(e),
            'statusCode': 500
        }
    except Exception as e:
        print(f"Unexpected error in getSubscription: {str(e)}")
        return {
            'error': 'An unexpected error occurred',
            'details': str(e),
            'statusCode': 500
        }


def handle_create_subscription(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for createSubscription operation
    Creates a new subscription for a user account
    
    Expected data:
    - accountId (required): The account ID of the user
    - serviceType (required): The type of service (e.g., 'streaming', 'shopping', 'gaming')
    - planId (required): The ID of the subscription plan
    - startDate (optional): The start date of the subscription (default: now)
    - paymentMethod (required): The payment method details
    """
    # Validate required parameters
    if not data.get('accountId'):
        return {'error': 'Missing required parameter: accountId', 'statusCode': 400}
    if not data.get('serviceType'):
        return {'error': 'Missing required parameter: serviceType', 'statusCode': 400}
    if not data.get('planId'):
        return {'error': 'Missing required parameter: planId', 'statusCode': 400}
    if not data.get('paymentMethod'):
        return {'error': 'Missing required parameter: paymentMethod', 'statusCode': 400}
    
    accountId = data['accountId']
    service_type = data['serviceType']
    plan_id = data['planId']
    payment_method = data['paymentMethod']
    
    # Optional fields with defaults
    start_date = data.get('startDate', datetime.utcnow().isoformat())
    
    if not SUBSCRIPTION_TABLE:
        return {'error': 'Subscription table not configured', 'statusCode': 500}
    
    try:
        # Check if account exists
        if ACCOUNTS_TABLE:
            account_table = dynamodb.Table(ACCOUNTS_TABLE)
            account_response = account_table.get_item(
                Key={'userId': accountId}  # Using userId as key per your account table structure
            )
            if 'Item' not in account_response:
                return {'error': 'Account not found', 'statusCode': 404}
        
        # Generate a unique subscription ID
        subscription_id = str(uuid.uuid4())
        
        # In a real system, we would validate the payment method and process payment here
        
        # Define subscription plan details (normally this would come from a plans table)
        plan_details = get_plan_details(plan_id, service_type)
        
        # Calculate end date based on billing cycle
        end_date = calculate_end_date(start_date, plan_details['billingCycle'])
        
        # Create the subscription record
        subscription_item = {
            'accountId': accountId,
            'subscriptionId': subscription_id,
            'serviceType': service_type,
            'planId': plan_id,
            'planName': plan_details['name'],
            'planDetails': plan_details,
            'status': 'active',
            'startDate': start_date,
            'endDate': end_date,
            'lastBillingDate': start_date,
            'nextBillingDate': end_date,
            'paymentMethod': payment_method,
            'createdAt': datetime.utcnow().isoformat(),
            'updatedAt': datetime.utcnow().isoformat()
        }
        
        # Save to DynamoDB
        subscription_table = dynamodb.Table(SUBSCRIPTION_TABLE)
        subscription_table.put_item(Item=subscription_item)
        
        return {
            'message': 'Subscription created successfully',
            'subscription': subscription_item
        }
    except ClientError as e:
        print(f"DynamoDB error in createSubscription: {str(e)}")
        return {
            'error': 'Database error',
            'details': str(e),
            'statusCode': 500
        }
    except Exception as e:
        print(f"Unexpected error in createSubscription: {str(e)}")
        return {
            'error': 'An unexpected error occurred',
            'details': str(e),
            'statusCode': 500
        }


def handle_update_subscription(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for updateSubscription operation
    Updates an existing subscription
    
    Expected data:
    - accountId (required): The account ID of the user
    - subscriptionId (required): The ID of the subscription to update
    - updates (required): Object containing subscription updates
    """
    # Validate required parameters
    if not data.get('accountId'):
        return {'error': 'Missing required parameter: accountId', 'statusCode': 400}
    if not data.get('subscriptionId'):
        return {'error': 'Missing required parameter: subscriptionId', 'statusCode': 400}
    if not data.get('updates'):
        return {'error': 'Missing required parameter: updates', 'statusCode': 400}
    
    accountId = data['accountId']
    subscriptionId = data['subscriptionId']
    updates = data['updates']
    
    if not SUBSCRIPTION_TABLE:
        return {'error': 'Subscription table not configured', 'statusCode': 500}
    
    try:
        subscription_table = dynamodb.Table(SUBSCRIPTION_TABLE)
        
        # Get current subscription
        response = subscription_table.get_item(
            Key={
                'accountId': accountId,
                'subscriptionId': subscriptionId
            }
        )
        
        if 'Item' not in response:
            return {'error': 'Subscription not found', 'statusCode': 404}
        
        current_subscription = response['Item']
        
        # Don't allow direct updates to critical fields for security
        protected_fields = ['accountId', 'subscriptionId', 'createdAt']
        for field in protected_fields:
            if field in updates:
                del updates[field]
        
        # Handle plan change if needed
        if 'planId' in updates:
            new_plan_id = updates['planId']
            service_type = current_subscription['serviceType']
            
            # Get details for the new plan
            new_plan_details = get_plan_details(new_plan_id, service_type)
            
            updates['planName'] = new_plan_details['name']
            updates['planDetails'] = new_plan_details
            
            # In a real system, we might handle prorated billing here
        
        # Add timestamp
        updates['updatedAt'] = datetime.utcnow().isoformat()
        
        # Build update expression for DynamoDB
        update_expression = "set "
        expression_attribute_values = {}
        
        for key, value in updates.items():
            update_expression += f"#{key} = :{key}, "
            expression_attribute_values[f":{key}"] = value
        
        # Remove trailing comma and space
        update_expression = update_expression[:-2]
        
        # Build expression attribute names (to handle reserved words)
        expression_attribute_names = {f"#{key}": key for key in updates.keys()}
        
        # Update the item in DynamoDB
        response = subscription_table.update_item(
            Key={
                'accountId': accountId,
                'subscriptionId': subscriptionId
            },
            UpdateExpression=update_expression,
            ExpressionAttributeValues=expression_attribute_values,
            ExpressionAttributeNames=expression_attribute_names,
            ReturnValues="ALL_NEW"
        )
        
        updated_subscription = response.get('Attributes', {})
        
        return {
            'message': 'Subscription updated successfully',
            'subscription': updated_subscription
        }
    except ClientError as e:
        print(f"DynamoDB error in updateSubscription: {str(e)}")
        return {
            'error': 'Database error',
            'details': str(e),
            'statusCode': 500
        }
    except Exception as e:
        print(f"Unexpected error in updateSubscription: {str(e)}")
        return {
            'error': 'An unexpected error occurred',
            'details': str(e),
            'statusCode': 500
        }


def handle_cancel_subscription(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handler for cancelSubscription operation
    Cancels an active subscription
    
    Expected data:
    - accountId (required): The account ID of the user
    - subscriptionId (required): The ID of the subscription to cancel
    - cancellationReason (optional): Reason for cancellation
    - immediateEffect (optional): Whether to cancel immediately or at the end of the billing cycle
    """
    # Validate required parameters
    if not data.get('accountId'):
        return {'error': 'Missing required parameter: accountId', 'statusCode': 400}
    if not data.get('subscriptionId'):
        return {'error': 'Missing required parameter: subscriptionId', 'statusCode': 400}
    
    accountId = data['accountId']
    subscriptionId = data['subscriptionId']
    cancellation_reason = data.get('cancellationReason', 'User requested cancellation')
    immediate_effect = data.get('immediateEffect', False)
    
    if not SUBSCRIPTION_TABLE:
        return {'error': 'Subscription table not configured', 'statusCode': 500}
    
    try:
        subscription_table = dynamodb.Table(SUBSCRIPTION_TABLE)
        
        # Get current subscription
        response = subscription_table.get_item(
            Key={
                'accountId': accountId,
                'subscriptionId': subscriptionId
            }
        )
        
        if 'Item' not in response:
            return {'error': 'Subscription not found', 'statusCode': 404}
        
        current_subscription = response['Item']
        
        # Check if already cancelled
        if current_subscription['status'] == 'cancelled':
            return {'error': 'Subscription is already cancelled', 'statusCode': 400}
        
        # Determine new status based on immediate_effect
        new_status = 'cancelled' if immediate_effect else 'pending_cancellation'
        
        # Update the subscription
        response = subscription_table.update_item(
            Key={
                'accountId': accountId,
                'subscriptionId': subscriptionId
            },
            UpdateExpression="set #status = :status, #cancellationReason = :reason, #cancellationDate = :date, #updatedAt = :updatedAt",
            ExpressionAttributeNames={
                "#status": "status",
                "#cancellationReason": "cancellationReason",
                "#cancellationDate": "cancellationDate",
                "#updatedAt": "updatedAt"
            },
            ExpressionAttributeValues={
                ":status": new_status,
                ":reason": cancellation_reason,
                ":date": datetime.utcnow().isoformat(),
                ":updatedAt": datetime.utcnow().isoformat()
            },
            ReturnValues="ALL_NEW"
        )
        
        updated_subscription = response.get('Attributes', {})
        
        return {
            'message': f"Subscription {new_status}",
            'subscription': updated_subscription,
            'immediateEffect': immediate_effect
        }
    except ClientError as e:
        print(f"DynamoDB error in cancelSubscription: {str(e)}")
        return {
            'error': 'Database error',
            'details': str(e),
            'statusCode': 500
        }
    except Exception as e:
        print(f"Unexpected error in cancelSubscription: {str(e)}")
        return {
            'error': 'An unexpected error occurred',
            'details': str(e),
            'statusCode': 500
        }


# Helper functions

def get_plan_details(plan_id: str, service_type: str) -> Dict[str, Any]:
    """Get details for a subscription plan (mock implementation)"""
    # In a real implementation, this would fetch from a plans table or service
    plans = {
        'streaming': {
            'basic': {
                'name': 'Basic Streaming',
                'price': 8.99,
                'currency': 'USD',
                'billingCycle': 'monthly',
                'features': ['HD streaming', 'Single device', 'Limited catalog'],
                'maxProfiles': 1
            },
            'standard': {
                'name': 'Standard Streaming',
                'price': 13.99,
                'currency': 'USD',
                'billingCycle': 'monthly',
                'features': ['HD streaming', 'Two devices', 'Full catalog'],
                'maxProfiles': 3
            },
            'premium': {
                'name': 'Premium Streaming',
                'price': 17.99,
                'currency': 'USD',
                'billingCycle': 'monthly',
                'features': ['4K Ultra HD', 'Four devices', 'Full catalog', 'Offline downloads'],
                'maxProfiles': 5
            },
            'annual': {
                'name': 'Annual Streaming',
                'price': 149.99,
                'currency': 'USD',
                'billingCycle': 'annual',
                'features': ['4K Ultra HD', 'Four devices', 'Full catalog', 'Offline downloads', '15% discount'],
                'maxProfiles': 5
            }
        },
        'shopping': {
            'prime': {
                'name': 'Shopping Prime',
                'price': 9.99,
                'currency': 'USD',
                'billingCycle': 'monthly',
                'features': ['Free shipping', 'Special deals', 'Early access']
            }
        }
    }
    
    try:
        return plans.get(service_type, {}).get(plan_id, {
            'name': f'Unknown Plan ({plan_id})',
            'price': 0.00,
            'currency': 'USD',
            'billingCycle': 'monthly',
            'features': []
        })
    except Exception as e:
        print(f"Error getting plan details: {str(e)}")
        return {
            'name': f'Error Plan ({plan_id})',
            'price': 0.00,
            'currency': 'USD',
            'billingCycle': 'monthly',
            'features': []
        }


def calculate_end_date(start_date_str: str, billing_cycle: str) -> str:
    """Calculate the end date based on billing cycle"""
    try:
        start_date = datetime.fromisoformat(start_date_str.replace('Z', '+00:00'))
    except ValueError:
        # Handle potential format issues
        start_date = datetime.utcnow()
    
    if billing_cycle == 'monthly':
        end_date = start_date + timedelta(days=30)
    elif billing_cycle == 'annual':
        end_date = start_date + timedelta(days=365)
    elif billing_cycle == 'weekly':
        end_date = start_date + timedelta(days=7)
    else:
        # Default to monthly
        end_date = start_date + timedelta(days=30)
    
    return end_date.isoformat()

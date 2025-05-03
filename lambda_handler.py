import requests
import os
import json

RAPIDAPI_KEY = os.environ['RAPIDAPI_KEY']
RAPIDAPI_HOST = 'advanced-movie-search.p.rapidapi.com'

def lambda_handler(event, context):
    try:
        path = event['rawPath']
        method = event['requestContext']['http']['method']
        if path == "/api" and method == "POST":
            # Parse the request body
            body = json.loads(event.get('body', '{}'))
            action = body.get('action')

            # Route the action to the appropriate function
            if action == "get_movie_info":
                return get_movie_info(body)
            elif action == "search_movies":
                return search_movies(body)
            elif action == "update_user_settings":
                return update_user_settings(body)
            elif action == "get_homepage_data":
                return get_homepage_data(body)
            else:
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": "Invalid action"})
                }
        else:
            return {
                "statusCode": 404,
                "body": json.dumps({"error": "Not Found"})
            }
    except Exception as e:
        return {
            "statusCode": 500,
            "body": json.dumps({"error": str(e)})
        }

def get_movie_info(body):
    # Extract movie_id from the body
    movie_id = body.get('movie_id')

    if not movie_id:
        return {
            "statusCode": 400,
            "body": json.dumps({"error": "movie_id is required"})
        }

    # Make the API request
    url = f"https://{RAPIDAPI_HOST}/movies/getdetails"

    querystring = {"movie_id": movie_id}

    headers = {
	    "x-rapidapi-key": "c25b0c052amshd0a4b0025e57806p184f7bjsne9803d030862",
	    "x-rapidapi-host": RAPIDAPI_HOST
    }he

    print(f"Request URL: {url}")
    print(f"Querystring: {querystring}")
    print(f"Headers: {headers}")

    try:
        response = requests.get(url, headers=headers, params=querystring)
        response.raise_for_status()  # Raise an error for bad responses

        movie_data = response.json()

        return {
            "statusCode": 200,
            "body": json.dumps({"message": "Movie info retrieved successfully", "data": movie_data})
        }
    except requests.exceptions.HTTPError as http_err:
        return {
            "statusCode": response.status_code,
            "body": json.dumps({"error": f"HTTP error occurred: {http_err}"})
        }

def search_movies(body):
    # Logic for searching movies
    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Movies searched successfully"})
    }

def update_user_settings(body):
    # Logic for updating user settings
    return {
        "statusCode": 200,
        "body": json.dumps({"message": "User settings updated successfully"})
    }

def get_homepage_data(body):
    # Logic for fetching homepage data
    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Homepage data fetched successfully"})
    }

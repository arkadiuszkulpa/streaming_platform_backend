import requests

url = "https://advanced-movie-search.p.rapidapi.com/movies/getdetails"
querystring = {"movie_id": "399566"}
headers = {
    "x-rapidapi-key": "c25b0c052amshd0a4b0025e57806p184f7bjsne9803d030862",
    "x-rapidapi-host": "advanced-movie-search.p.rapidapi.com"
}

response = requests.get(url, headers=headers, params=querystring)
print(response.status_code, response.json())
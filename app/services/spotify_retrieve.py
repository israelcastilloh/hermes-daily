import requests
import json

def get_song_url(prompt, secrets):

    prompt = prompt.replace("```json", '').replace("```", "")

    # Set your Spotify client ID and client secret
    client_id = secrets['spotify_clientid']
    client_secret = secrets['spotify_clientsecret']

    # Spotify API token endpoint
    token_url = "https://accounts.spotify.com/api/token"

    # Data to be sent in the POST request
    data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    }

    # Make the POST request to get the access token
    token_response = requests.post(token_url, data=data)
    token_data = token_response.json()

    access_token = token_data.get('access_token')

    # Original text
    prompt = json.loads(prompt)

    # Extract the song and artist
    try:
        #print("Song:", prompt['title'])
        #print("Artist:", prompt['artist'])

        # Spotify search endpoint
        search_url = f"https://api.spotify.com/v1/search?q={prompt['title']}&type=track&limit=1"

        # Set the headers for the search request
        headers = {
            'Authorization': 'Bearer ' + access_token
        }

        # Make the GET request to the search endpoint
        search_response = requests.get(search_url, headers=headers)

        # Parse the response JSON
        response_json = search_response.json()

        # Extract the external URL for the track
        external_url = response_json['tracks']['items'][0]['external_urls']['spotify']

        # Print the external URL
        #print("Listen to this song: {external_url}")

        return_text = prompt['title'] + ' by ' + prompt['artist'] + f"\nListen to this song: {external_url}"
    except:
        return_text = prompt['title'] + ' by ' + prompt['artist']+ "\nURL not available."

    return return_text

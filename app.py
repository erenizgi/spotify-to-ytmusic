import spotipy
import json
from flask import request, jsonify
from spotipy.oauth2 import SpotifyOAuth
from tqdm import tqdm
import requests
import time
from dotenv import load_dotenv
import os
from google_auth_oauthlib.flow import InstalledAppFlow
load_dotenv() 

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
YTMUSIC_TARGET_PLAYLIST_ID = os.getenv("YTMUSIC_TARGET_PLAYLIST_ID")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
YOUTUBE_SEARCH_URL = os.getenv("YOUTUBE_SEARCH_URL")
YOUTUBE_PLAYLIST_URL = os.getenv("YOUTUBE_PLAYLIST_URL")
SCOPES = [os.getenv("SCOPES")]
scope = 'playlist-read-private'
PLAYLIST_ADD_URL = os.getenv("PLAYLIST_ADD_URL")
CLIENT_SECRET_FILE="client_secret_392151383048-9....json"
flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
credentials = flow.run_local_server(port=0)
print("TOKEN: ", credentials.token)


def youtube_search(query):
    if not query:
        return 
    params = {
        'key': YOUTUBE_API_KEY,
        'part': 'snippet',
        'q': query,
        'maxResults': 10,
        'type': 'video'
    }
    resp = requests.get(YOUTUBE_SEARCH_URL, params=params)
    data = resp.json()
    results = [
        {
            'title': item['snippet']['title'],
            'videoId': item['id']['videoId'],
            'url': f"https://www.youtube.com/watch?v={item['id']['videoId']}"
        }
        for item in data.get('items', [])
    ]
    return results

sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope=scope
))

print("Spotify side connecting...")
tracks = []
SPOTIFY_PLAYLIST_ID = input("Enter Spotify Playlist ID:")
results = sp.playlist_tracks(SPOTIFY_PLAYLIST_ID)
playlistName = sp.playlist(SPOTIFY_PLAYLIST_ID)['name']
tracks.extend(results['items'])
while results['next']:
    results = sp.next(results)
    tracks.extend(results['items'])

track_tuples = []
for item in tracks:
    track = item['track']
    name = track['name']
    artists = ', '.join([artist['name'] for artist in track['artists']])
    track_tuples.append((name, artists))

print(f"Found {len(track_tuples)} tracks.")

print("Converting to YouTube Music...")
headers = {
    "Authorization": f"Bearer {credentials.token}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

data = {
    "snippet": {
        "title": playlistName,
        "description": ""
    },
    "status": {
        "privacyStatus": "private"
    }
}

resp = requests.post(YOUTUBE_PLAYLIST_URL, headers=headers, json=data)
if resp.ok:
    result = resp.json()
    playlist_id = result["id"]
    print("Playlist id:", playlist_id)
else:
    print("Error:", resp.status_code, resp.text)
    print("Playlist not found. Exiting...")
    exit(1)
    
videoHeaders = {
    "Authorization": f"Bearer {credentials.token}",
    "Accept": "application/json",
    "Content-Type": "application/json"
}

not_found = []

for name, artists in tqdm(track_tuples):
    query = f"{name} {artists}"
    search = youtube_search(query)
    if search:
        search = search[0]
        song = search['videoId']
        video_id = song
        videoData = {
                "snippet": {
                    "playlistId": playlist_id,
                    "resourceId": {
                        "kind": "youtube#video",
                        "videoId": video_id
                    }
                }
            }
        try:
            print(search["title"])
            resp = requests.post(PLAYLIST_ADD_URL, headers=videoHeaders, json=videoData)
            time.sleep(1) 
        except Exception as e:
            print(f"Hata oluştu: {name} ({e})")
            not_found.append((name, artists))
    else:
        not_found.append((name, artists))

print("\nConversion Complete! Not Found:")
for name, artist in not_found:
    print(f"{name} - {artist}")

print("\nIt's done! 🎧")
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from ytmusicapi import YTMusic
from tqdm import tqdm
import time
from dotenv import load_dotenv
import os

load_dotenv() 

SPOTIFY_CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.getenv("SPOTIFY_CLIENT_SECRET")
SPOTIFY_REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
SPOTIFY_PLAYLIST_ID = os.getenv("SPOTIFY_PLAYLIST_ID")
YTMUSIC_HEADERS_PATH = os.getenv("YTMUSIC_HEADERS_PATH")
YTMUSIC_TARGET_PLAYLIST_ID = os.getenv("YTMUSIC_TARGET_PLAYLIST_ID")


scope = 'playlist-read-private'
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    redirect_uri=SPOTIFY_REDIRECT_URI,
    scope=scope
))

print("Spotify'dan playlist çekiliyor...")
tracks = []
results = sp.playlist_tracks(SPOTIFY_PLAYLIST_ID)
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

print(f"Toplam {len(track_tuples)} şarkı bulundu.")

ytmusic = YTMusic(YTMUSIC_HEADERS_PATH)
print("YouTube Music'e aktarılıyor...")

not_found = []

for name, artists in tqdm(track_tuples):
    query = f"{name} {artists}"
    search_results = ytmusic.search(query, filter="songs")
    if search_results:
        song = search_results[0]
        video_id = song['videoId']
        try:
            ytmusic.add_song_to_playlist(YTMUSIC_TARGET_PLAYLIST_ID, video_id)
            time.sleep(1) 
        except Exception as e:
            print(f"Hata oluştu: {name} ({e})")
            not_found.append((name, artists))
    else:
        not_found.append((name, artists))

print("\nAktarma tamam! Bulunamayanlar:")
for name, artist in not_found:
    print(f"{name} - {artist}")

print("\nBitti bro! Loop'u aç dinle. 🎧")
import base64
import requests

class SimilarSongs:

    def __init__(self, client_id:str, secret:str):
        """
        Initialize the SimilarSongs class with the provided API key and secret.
        
        Args:
            client_id (str): Spotify API client ID
            secret (str): Spotify API client secret
            
        Raises:
            ConnectionError: If unable to obtain access token
            ValueError: If credentials are invalid
        """
        if not client_id or not secret:
            raise ValueError("Client ID and secret must be provided")

        try:
            auth_str = f"{client_id}:{secret}"  # Fixed: Using secret param instead of self.client_secret
            b64_auth_str = base64.b64encode(auth_str.encode()).decode()
        except Exception as e:
            raise ValueError(f"Error encoding credentials: {str(e)}")

        headers = {
            'Authorization': f'Basic {b64_auth_str}'
        }

        data = {
            'grant_type': 'client_credentials'
        }

        try:
            response = requests.post('https://accounts.spotify.com/api/token', headers=headers, data=data)
            
            if response.status_code == 200:
                self.token = response.json()['access_token']
                print("Access Token:", self.token)
            else:
                error_msg = f"Failed to get access token. Status: {response.status_code}, Response: {response.text}"
                print(error_msg)
                raise ConnectionError(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error during authentication: {str(e)}"
            print(error_msg)
            raise ConnectionError(error_msg)



    def get_similar_tracks(self, song:str, artist:str, limit=3, market="US"):
        """
        Retrieve similar tracks using Spotify's Recommendations API.
        
        Parameters:
            song (str): The name of the song
            artist (str): The name of the artist
            limit (int): Number of tracks to return (default is 3).
            market (str): ISO 3166-1 alpha-2 country code (default is "US").
            
        Returns:
            list: A list of tuples containing (track_name, artist_name) for similar tracks
        """
        try:
            print(f"Finding similar tracks for '{song}' by '{artist}'...")
            
            # Get the track ID first
            seed_track_id = self.get_track_id(track_name=song, artist_name=artist)
            
            if not seed_track_id:
                print(f"Could not find track ID for {song} by {artist}")
                return []

            print(f"Using seed track ID: {seed_track_id}")

            # Create headers with the token
            headers = {
                "Authorization": f"Bearer {self.token}"
            }

            # THIS IS THE CORRECTION - use seed_tracks instead of id parameter
            endpoint = "https://api.spotify.com/v1/recommendations"
            params = {
                "seed_tracks": seed_track_id,  # Changed from "id" to "seed_tracks"
                "limit": limit,  # Uncommented limit
                "market": market
            }
            
            print(f"Sending request to {endpoint} with params: {params}")
            response = requests.get(endpoint, headers=headers, params=params)
            print(f"Response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Error in get_similar_tracks(): {response.status_code}, {response.text}")
                return []
            
            data = response.json()
            tracks = data.get("tracks", [])
            print(f"Received {len(tracks)} tracks in response")
            
            # Extract track names and artists
            similar_tracks = []
            for track in tracks:
                track_name = track.get("name")
                artist_name = track.get("artists", [{}])[0].get("name") if track.get("artists") else "Unknown Artist"
                similar_tracks.append((track_name, artist_name))
                print(f"Found similar track: '{track_name}' by '{artist_name}'")
            
            return similar_tracks
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"Error getting similar tracks: {e}")
            return []
        
    def check_recommendations_endpoint(token):
        url = "https://api.spotify.com/v1/recommendations"
        params = {
            "seed_artists": "4NHQUGzhtTLFvgF5SZesLK",
            "seed_genres": "classical,country",
            "seed_tracks": "0c6xIDDpzE81m2q797ordA"
        }
        headers = {
            "Authorization": f"Bearer {token}"
        }

        response = requests.get(url, headers=headers, params=params)
        print("Status code:", response.status_code)
        print("Response:", response.json())

    def get_track_id(self, track_name, artist_name):
        """
        Search for a track by name and artist using Spotify's Search for Item endpoint,
        and return the Spotify track ID of the first result.

        Parameters:
            access_token (str): A valid OAuth 2.0 access token.
            track_name (str): The name of the song.
            artist_name (str): The name of the artist.
        
        Returns:
            str or None: The Spotify track ID if found, otherwise None.
        """
        endpoint = "https://api.spotify.com/v1/search"
        headers = {
            "Authorization": f"Bearer {self.token}"
        }
        # Construct a query that specifies both the track and artist.
        query = f"track:{track_name} artist:{artist_name}"
        params = {
            "q": query,
            "type": "track",
            "limit": 1
        }
        
        response = requests.get(endpoint, headers=headers, params=params)
        if response.status_code != 200:
            print("Error in get_track_id():", response.status_code, response.text)
            return None

        data = response.json()
        tracks = data.get("tracks", {}).get("items", [])
        if tracks:
            return tracks[0]["id"]
        else:
            print("No matching track found.")
            return None


    

SPOTIFY_CLIENT_ID="5140ff5873f94fbc8093c66960b3ec8c"
SPOTIFY_CLIENT_SECRET="7848e32fe1c04d24bf12821b6da3d4af"

song_finder = SimilarSongs(SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET)
similar_songs = song_finder.get_similar_tracks(song="Blinding Lights", artist="The Weeknd")
print(similar_songs)

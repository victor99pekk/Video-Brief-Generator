import requests
import base64
import json
import os
import time

class SimilarSongs:
    """
    A class for finding similar songs using the TIDAL API with client credentials flow.
    """

    def __init__(self, client_id, client_secret):
        """
        Initialize the SimilarSongs class with TIDAL API credentials.
        
        Args:
            client_id (str): TIDAL API client ID
            client_secret (str): TIDAL API client secret
        """
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None
        self.token_type = "Bearer"
        self.token_expiry = 0
        self.token_server = "https://auth.tidal.com/v1/oauth2/token"
        self.api_base_url = "https://api.tidal.com/v1"
        
        # Authenticate immediately upon initialization
        self.authenticate()
    
    def authenticate(self):
        """
        Authenticate using the client credentials flow.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            print("Authenticating with TIDAL API...")
            
            # Create base64 encoded credentials as specified in the documentation
            credentials = f"{self.client_id}:{self.client_secret}"
            b64_credentials = base64.b64encode(credentials.encode()).decode()
            
            oauth_headers = {
                "Content-Type": "application/x-www-form-urlencoded",
                "Authorization": f"Basic {b64_credentials}"
            }
            
            data = {
                "grant_type": "client_credentials"
            }
            
            response = requests.post(self.token_server, headers=oauth_headers, data=data)
            
            if response.status_code == 200:
                token_info = response.json()
                self.token = token_info.get("access_token")
                self.token_type = token_info.get("token_type", "Bearer")
                expires_in = token_info.get("expires_in", 3600)
                
                # Set expiry time (current time + expires_in - 300 second buffer)
                self.token_expiry = time.time() + expires_in - 300
                
                print(f"Authentication successful!")
                print(f"Access token: {self.token[:10]}... (expires in {expires_in} seconds)")
                return True
            else:
                print(f"Authentication failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
        except Exception as e:
            print(f"Authentication error: {str(e)}")
            return False
    
    def ensure_valid_token(self):
        """
        Ensure we have a valid token, refreshing if necessary.
        
        Returns:
            bool: True if a valid token is available, False otherwise
        """
        # If token doesn't exist or is about to expire, get a new one
        if not self.token or time.time() >= self.token_expiry:
            return self.authenticate()
        return True
            
    def search_track(self, name, artist=None, limit=5):
        """
        Search for a track by name and optionally artist.
        
        Args:
            name (str): The track name to search for
            artist (str, optional): The artist name to filter by
            limit (int): Maximum number of results to return
            
        Returns:
            dict or None: The first matching track information or None if not found
        """
        # Ensure we have a valid token
        if not self.ensure_valid_token():
            print("Failed to obtain valid token")
            return None
        
        try:
            headers = {
                "Authorization": f"{self.token_type} {self.token}",
                "Content-Type": "application/json"
            }
            
            # Construct search query
            query = name
            if artist:
                query = f"{name} {artist}"
                
            params = {
                "query": query,
                "limit": limit,
                "countryCode": "US",
                "types": "TRACKS"  # Note: The TIDAL API might use "types" instead of "type"
            }
            
            endpoint = f"{self.api_base_url}/search"
            print(f"Searching for track: '{query}'")
            response = requests.get(endpoint, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                tracks = data.get("items", [])
                
                if tracks:
                    # If artist is specified, try to find an exact match
                    if artist:
                        for track in tracks:
                            track_artist = track.get("artist", {}).get("name", "")
                            if artist.lower() in track_artist.lower():
                                return track
                    
                    # Otherwise return the first result
                    return tracks[0]
                    
                print("No tracks found matching the search criteria.")
                return None
                
            elif response.status_code == 401:
                print("Access token expired. Attempting to refresh...")
                if self.authenticate():
                    # Try again with the new token
                    return self.search_track(name, artist, limit)
                else:
                    print("Failed to refresh token.")
                    return None
            else:
                print(f"Error searching for track: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            print(f"Error searching for track: {str(e)}")
            return None
            
    def get_similar_tracks(self, track_id=None, limit=10):
        """
        Get tracks similar to the provided track.
        
        Args:
            track_id (str): TIDAL track ID to find similar tracks
            limit (int): Maximum number of tracks to return
            
        Returns:
            list: List of similar track information as (track_name, artist_name) tuples
        """
        # Ensure we have a valid token
        if not self.ensure_valid_token():
            print("Failed to obtain valid token")
            return []
        
        if not track_id:
            print("Track ID is required")
            return []
        
        similar_tracks = []
        
        try:
            headers = {
                "Authorization": f"{self.token_type} {self.token}",
                "Content-Type": "application/json"
            }
            
            # Get similar tracks based on a track ID
            endpoint = f"{self.api_base_url}/tracks/{track_id}/similar"
            params = {"limit": limit, "countryCode": "US"}
            
            print(f"Getting similar tracks for track ID: {track_id}")
            response = requests.get(endpoint, headers=headers, params=params)
            
            if response.status_code == 200:
                data = response.json()
                tracks = data.get("items", [])
                
                for track in tracks:
                    track_name = track.get("title")
                    artist_name = track.get("artist", {}).get("name", "Unknown Artist")
                    similar_tracks.append((track_name, artist_name))
                    print(f"Found similar track: '{track_name}' by '{artist_name}'")
                    
            elif response.status_code == 401:
                print("Access token expired. Attempting to refresh...")
                if self.authenticate():
                    # Try again with the new token
                    return self.get_similar_tracks(track_id, limit)
                else:
                    print("Failed to refresh token.")
            else:
                print(f"Error getting similar tracks: {response.status_code} - {response.text}")
                print(f"Response body: {response.text}")
                
        except Exception as e:
            print(f"Error getting similar tracks: {str(e)}")
            
        return similar_tracks


# Test the implementation when file is run directly
if __name__ == "__main__":
    # Get credentials from environment or input
    client_id = "k5n8xFv6twrVblnZ"
    client_secret = "NO8CX3IFyvHVg98KnsZliw4GcppMykme9Rpk0tiOxSE="
    # Initialize the API
    finder = SimilarSongs(client_id, client_secret)
    
    while True:
        try:
            # Get search query from user
            query = "hello"
            if query.lower() == 'q':
                break
                
            artist = "adele"
            
            # Search for the track
            track = finder.search_track(query, artist=artist if artist else None)
            if track:
                track_id = track.get('id')
                title = track.get('title')
                artist = track.get('artist', {}).get('name')
                
                print(f"\nFound track: {title} by {artist} (ID: {track_id})")
                
                # Get similar tracks
                similar = finder.get_similar_tracks(track_id=track_id)
                if similar:
                    print("\nSimilar tracks:")
                    for i, (name, artist) in enumerate(similar, 1):
                        print(f"{i}. {name} - {artist}")
                else:
                    print("No similar tracks found.")
            else:
                print("No tracks found matching your search.")
                
        except KeyboardInterrupt:
            print("\nExiting...")
            break
            
    print("\nThank you for using the TIDAL API demo!")
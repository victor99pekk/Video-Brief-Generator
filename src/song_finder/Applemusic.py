import requests
from dotenv import load_dotenv
import os
import random

# Import the LLM recommender from your project
from .LLM_SongRecommender import *

class AppleMusicAPI:
    """
    A wrapper class for the Apple Music API that provides methods to access music data,
    including top charts, album information, and track genres.

    Optionally integrates an LLM-based recommender to provide similar track recommendations.
    The LLM's influence is determined by its familiarity with the queried song.

    Attributes:
        developer_token (str): The Apple Music API developer token for authentication.
        storefront (str): The storefront code (e.g., "us").
    """
    BASE_URL = "https://api.music.apple.com/v1/catalog"
    
    def __init__(self, developer_token, storefront="us", llm_api_key=None):
        """
        Initialize the Apple Music API wrapper with the provided developer token, storefront,
        and optional LLM API key.

        Args:
            developer_token (str): Your Apple Music API developer token.
            storefront (str): The storefront code (default "us").
            llm_api_key (str, optional): API key for the LLM recommender (e.g. OpenAI API key).
        """
        self.developer_token = developer_token
        self.storefront = storefront
        self.headers = {
            "Authorization": f"Bearer {self.developer_token}"
        }
        
        # Initialize LLM recommender if API key is provided
        if llm_api_key:
            self.llm_recommender = LLM_SongRecommender({"gpt-3.5-turbo": llm_api_key})
        else:
            self.llm_recommender = None

    def _request(self, endpoint, params=None):
        """Helper method to make GET requests to the Apple Music API."""
        url = f"{self.BASE_URL}/{self.storefront}/{endpoint}"
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def search(self, term, types="songs,albums,artists", limit=5):
        """
        Searches the Apple Music catalog for the given term.
        
        Args:
            term (str): The search term.
            types (str): Comma-separated types to search (default "songs,albums,artists").
            limit (int): Maximum number of results per type.
            
        Returns:
            dict: The JSON response from the API.
        """
        url = f"{self.BASE_URL}/{self.storefront}/search"
        params = {
            "term": term,
            "types": types,
            "limit": limit
        }
        response = requests.get(url, headers=self.headers, params=params)
        response.raise_for_status()
        return response.json()
    
    def get_top_tracks(self, limit=5):
        """
        Retrieves the top trending songs from the Apple Music charts.
        
        Args:
            limit (int): Maximum number of songs to retrieve.
            
        Returns:
            list: A list of tuples containing (track name, artist name).
        """
        endpoint = "charts"
        params = {
            "types": "songs",
            "limit": limit
        }
        data = self._request(endpoint, params=params)
        songs = []
        charts = data.get("results", {}).get("songs", [])
        for chart in charts:
            for song in chart.get("data", []):
                attributes = song.get("attributes", {})
                track_name = attributes.get("name")
                artist_name = attributes.get("artistName")
                songs.append((track_name, artist_name))
        return songs
    
    def get_album_info(self, artist, album):
        """
        Retrieves album information by searching for the album with the given artist and album name.
        
        Args:
            artist (str): The artist name.
            album (str): The album title.
            
        Returns:
            dict: A dictionary with album information (name, artist, release date, genre names, URL),
                  or an empty dictionary if not found.
        """
        term = f"{album} {artist}"
        result = self.search(term, types="albums", limit=1)
        albums = result.get("results", {}).get("albums", {}).get("data", [])
        if not albums:
            return {}
        album_data = albums[0].get("attributes", {})
        info = {
            "Name": album_data.get("name"),
            "Artist": album_data.get("artistName"),
            "Release Date": album_data.get("releaseDate", "Unknown"),
            "Genre Names": album_data.get("genreNames", []),
            "URL": album_data.get("url")
        }
        return info
    
    def get_track_genres(self, song, artist):
        """
        Retrieves the genre information for a track by searching for the track.
        
        Args:
            song (str): The track name.
            artist (str): The artist name.
            
        Returns:
            list: A list of genre names associated with the track.
        """
        term = f"{song} {artist}"
        result = self.search(term, types="songs", limit=1)
        songs = result.get("results", {}).get("songs", {}).get("data", [])
        if not songs:
            return []
        attributes = songs[0].get("attributes", {})
        return attributes.get("genreNames", [])
    
    def get_global_trending_tracks(self, limit=5):
        """
        Retrieves the top trending tracks globally from Apple Music charts.
        
        Args:
            limit (int): Maximum number of tracks to retrieve.
            
        Returns:
            list: A list of tuples containing (track name, artist name).
        """
        return self.get_top_tracks(limit=limit)
    
    def get_similar_tracks(self, song, artist, limit=5):
        """
        Finds similar tracks by combining recommendations from the Apple Music catalog (using genre and vibe
        descriptors) and, if available, an LLM-based recommender. If the LLM's familiarity score for the song
        is above 85, only LLM recommendations are used; otherwise, the final results are a blend of both sources.

        Args:
            song (str): The track name.
            artist (str): The artist name.
            limit (int): Maximum number of similar tracks to retrieve.

        Returns:
            list: A list of tuples containing (track name, artist name).
        """
        # Get genres for the track
        genres = self.get_track_genres(song, artist)
        if not genres:
            print("No genres found for the track; cannot fetch similar tracks from Apple Music.")
            apple_results = []
        else:
            # Collect candidate tracks from multiple queries
            candidates = []
            original_artist = artist.lower()
            vibe_keywords = ["chill", "energetic", "upbeat", "smooth"]

            for genre in genres:
                search_queries = [f"{genre} {vk}" for vk in vibe_keywords] + [genre]
                for query in search_queries:
                    result = self.search(query, types="songs", limit=limit * 2)
                    songs_data = result.get("results", {}).get("songs", {}).get("data", [])
                    for s in songs_data:
                        attr = s.get("attributes", {})
                        track_name = attr.get("name")
                        artist_name = attr.get("artistName")
                        if artist_name and artist_name.lower() == original_artist:
                            continue
                        track_genres = attr.get("genreNames", [])
                        if not any(genre.lower() in tg.lower() for tg in track_genres):
                            continue
                        candidates.append((track_name, artist_name))
            
            # Deduplicate candidates by artist
            unique_candidates = {}
            for track_name, artist_name in candidates:
                if artist_name and artist_name.lower() not in unique_candidates:
                    unique_candidates[artist_name.lower()] = (track_name, artist_name)
            apple_results = list(unique_candidates.values())
            random.shuffle(apple_results)
            apple_results = apple_results[:limit]
        
        # Initialize LLM recommendations to empty list by default
        llm_results = []
        use_llm_only = False
        
        # If the LLM recommender is available, use it to get recommendations
        if self.llm_recommender:
            try:
                # Get a familiarity score for the song from the LLM
                familiarity_score = self.llm_recommender.familiar_score(song, artist)
                print(f"Familiarity score for '{song}' by {artist}: {familiarity_score}")
                # If the score is above 85, use only LLM recommendations.
                if familiarity_score > 85:
                    use_llm_only = True
                    llm_count = limit
                else:
                    llm_count = round((familiarity_score / 100) * limit)
                # Fetch LLM recommendations if needed
                if llm_count > 0:
                    llm_results = self.llm_recommender.get_song_recommendations(song, artist, vibe=None, count=llm_count)
            except Exception as e:
                print(f"Error using LLM recommender: {e}")
        
        if use_llm_only:
            combined = llm_results
        else:
            # Determine how many Apple Music recommendations to use if mixing both sources.
            apple_count = limit - len(llm_results)
            combined = apple_results[:apple_count] + llm_results
        
        # Deduplicate combined results based on track name and artist
        unique = {}
        for track_name, artist_name in combined:
            key = (track_name.lower(), artist_name.lower())
            if key not in unique:
                unique[key] = (track_name, artist_name)
        final_results = list(unique.values())
        random.shuffle(final_results)
        return final_results[:limit]

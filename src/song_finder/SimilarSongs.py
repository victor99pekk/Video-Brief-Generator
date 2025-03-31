from .Applemusic import *
from .LLM_SongRecommender import *

class SimilarSongs:
    """
    A class that uses the ApplemusicAPI and the LLM_songrecommendations to find a good song recommendation
    """

    def __init__(self, music_token:str, LLM_key:str, model: str = "gpt-3.5-turbo", LLM_count=3):
        """
        Initialize the SimilarSongs class with TIDAL API credentials.
        
        Args:
            music_token: token for the apple music api
            LLM_key: key for the LLM api
            mode: LLM model being used
        """
        self.applemusic = AppleMusicAPI(music_token)
        self.LLM = LLM_SongRecommender({model:LLM_key})
        self.LLM_count = LLM_count
        
    
    def get_similar_tracks(self, song:str, artist:str, vibe:str=None, limit=5):
        """
        Finds similar tracks by combining recommendations from the Apple Music catalog (using genre and vibe
        descriptors) and, if available, an LLM-based recommender. If the LLM's familiarity score for the song
        is above 70, only LLM recommendations are used, if it is below 20 only the apple music api is used; 
        otherwise, the final results are a blend of both sources.

        Args:
            song (str): The track name.
            artist (str): The artist name.
            limit (int): Maximum number of similar tracks to retrieve.

        Returns:
            list: A list of tuples containing (track name, artist name).
        """
        familiar_score = self.LLM.familiar_score(song, artist)
        print("familiar score: ", familiar_score)
        if familiar_score >= 70:
            return self.LLM.get_song_recommendations(song, artist, vibe)
        elif familiar_score < 20:
            return self.applemusic.get_similar_tracks(song, artist)
        else:
            result = self.LLM.get_song_recommendations(song, artist, vibe)[:self.LLM_count+1]
            const = 5
            apple_result = self.applemusic.get_similar_tracks(song, artist, const)
            rand_index = random.randint(0, const)
            result.append(apple_result[rand_index])
            del apple_result[rand_index]
            result.append(self.LLM.find_most_similar(apple_result, tuple([song, artist]), 1))
            return result
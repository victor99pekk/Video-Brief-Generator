from collections import Counter
from typing import List, Tuple
from openai import OpenAI
import heapq
import re


class LLM_SongRecommender:
    """
    A class that uses a number of different LLM models to find similar songs
    """
    def __init__(self, model_to_key: dict[str, str]):
        self.models = {
            "gpt-3.5-turbo": OpenAI(api_key=model_to_key["gpt-3.5-turbo"])
        }
    
    def familiar_score(self, song: str, artist: str) -> int:
        """
        Scores how familiar the LLM is with this song [0, 100].
        This decides how much the output of the LLM should be involved in deciding the recommendations.
        Args:
            song: A song to find similar songs for.
            artist: The artist of the song.
        :return: An int in the range of 0 to 100.
        """
        prompt = f"How well known is the song '{song}' by '{artist}' on a scale of 0 to 100? Provide only the number."
        try:
            response = self.models["gpt-3.5-turbo"].chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a music expert."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=10
            )
            score = int(response.choices[0].message.content.strip())
            return min(max(score, 0), 100)
        except Exception as e:
            print(f"Error fetching familiar score: {e}")
            return 0
    
    def similarity_score(self, song1: str, artist1: str, song2: str, artist2: str) -> float:
        """
        Computes a similarity score between two songs using an LLM.
        """
        prompt = (f"On a scale of 0 to 100, how similar is '{song1}' by '{artist1}' to '{song2}' by '{artist2}'? "
                  "Provide only the number.")
        try:
            response = self.models["gpt-3.5-turbo"].chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a music expert analyzing song similarities."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0,
                max_tokens=10
            )
            score = float(response.choices[0].message.content.strip())
            return min(max(score, 0), 100)  # Ensure score is in range [0, 100]
        except Exception as e:
            print(f"Error fetching similarity score: {e}")
            return 0.0

    def find_most_similar(self, song_list: List[Tuple[str, str]], target_song: Tuple[str, str], n: int) -> List[Tuple[str, str]]:
        """
        Finds the n most similar songs from a given list, ensuring no more than 35% come from the same artist.
        """
        song, artist = target_song
        similarity_heap = []
        
        for s, a in song_list:
            if (s, a) == (song, artist):
                continue  # Skip comparing the song with itself
            score = self.similarity_score(song, artist, s, a)
            heapq.heappush(similarity_heap, (-score, (s, a)))  # Use negative score for max-heap behavior
        
        max_per_artist = max(1, int(n * 0.35))  # Ensure at most 35% of recommendations come from the same artist
        artist_counts = Counter()
        most_similar = []
        
        while similarity_heap and len(most_similar) < n:
            _, (s, a) = heapq.heappop(similarity_heap)
            if artist_counts[a] < max_per_artist:
                most_similar.append((s, a))
                artist_counts[a] += 1
        
        return most_similar
    
    def get_song_recommendations(self, song: str, artist: str, vibe: str = None, count: int = 5) -> list[tuple]:
        """
        Finds similar song recommendations based on the input song, and optionally, a specified vibe.
        """
        prompt = self.build_prompt(song, artist, vibe, count)

        try:
            response = self.models["gpt-3.5-turbo"].chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a music expert recommending songs based on similarities in melody, lyrics, chord progression, beat and rhythm, structure, harmony, and genre/style."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=200
            )
            recommendations = response.choices[0].message.content.strip().split("\n")

            # Remove leading numbers (e.g., "1. Song - Artist") before splitting
            cleaned_recommendations = [
                re.sub(r"^\d+\.\s*", "", song).strip() for song in recommendations
            ]

            return [
                tuple(song.rsplit(" - ", 1)) for song in cleaned_recommendations if " - " in song
            ]
        except Exception as e:
            print(f"Error generating song recommendations: {e}")
            return []

    def build_prompt(self, song: str, artist: str, vibe: str = None, count: int = 5) -> str:
        """
        Builds a prompt to query the LLM for song recommendations.
        Args:
            song: A song to find similar songs for.
            artist: The artist of the song.
            vibe: The vibe of the recommended songs.
            count: The number of recommendations.
        :return: A formatted prompt string.
        """
        prompt = f"Give me {count} songs similar to '{song}' by '{artist}', based on melody, lyrics, chord progression, beat and rhythm, structure, harmony, and genre/style."
        if vibe:
            prompt += f" The songs should match the vibe: {vibe}. and at most {(count//2)} of your recommendations can be songs by the same artist"
        prompt += " Provide only the song names and artists in the format 'Song - Artist', separated by new lines."
        return prompt

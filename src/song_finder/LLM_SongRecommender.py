from openai import OpenAI


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
    
    def get_song_recommendations(self, song: str, artist: str, vibe: str = None, count: int = 10) -> list[tuple]:
        """
        Finds similar song recommendations based on the input song, and optionally, a specified vibe.
        Args:
            song: A song to find similar songs for.
            artist: The artist of the song.
            vibe: The vibe or mood of the recommended songs.
            count: The number of song recommendations to return.
        :return: A list of tuples where each tuple contains (song, artist).
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
            return [tuple(song.strip().rsplit(" - ", 1)) for song in recommendations if " - " in song]
        except Exception as e:
            print(f"Error generating song recommendations: {e}")
            return []
    
    def build_prompt(self, song: str, artist: str, vibe: str = None, count: int = 10) -> str:
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
            prompt += f" The songs should match the vibe: {vibe}."
        prompt += " Provide only the song names and artists in the format 'Song - Artist', separated by new lines."
        return prompt

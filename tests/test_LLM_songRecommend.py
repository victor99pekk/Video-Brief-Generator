import os
import sys
from dotenv import load_dotenv

# Add the parent directory to the sys path for importing from the src directory
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from src.song_finder.LLM_SongRecommender import LLM_SongRecommender


# Load environment variables from .env file
load_dotenv()

# Retrieve the OpenAI API key from environment variables
api_key = os.getenv("OPENAI_KEY")
if not api_key:
    raise ValueError("API key not found. Make sure to set OPENAI_KEY in your .env file.")

# Initialize the song recommender with the API key
recommender = LLM_SongRecommender({"gpt-3.5-turbo": api_key})

# Set up song details and recommendation parameters
song = "Bohemian Rhapsody"
artist = "Queen"  # Add artist to match the recommendation logic
vibe = "epic and dramatic"
count = 5

# Get song recommendations
print(f"Finding {count} songs similar to '{song}' by {artist} with a '{vibe}' vibe...")

try:
    recommendations = recommender.get_song_recommendations(song, artist, vibe, count)
    print(f"Type of return: {type(recommendations)}\n")

    print("Recommended Songs:")
    if recommendations:
        for idx, (rec_song, rec_artist) in enumerate(recommendations, start=1):
            print(f"{idx}. {rec_song} - {rec_artist}")
    else:
        print("No recommendations found.")
except Exception as e:
    print(f"Error fetching song recommendations: {e}")

# Fetch and print the familiarity score for the song
try:
    familiar_score = recommender.familiar_score(song, artist)
    print(f"\nFamiliarity score for '{song}' by {artist}: {familiar_score}")
except Exception as e:
    print(f"Error fetching familiarity score: {e}")

from dotenv import load_dotenv
import os
import sys
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Import from the src directory
from src import AppleMusicAPI

def main():
    # Load environment variables
    load_dotenv()
    developer_token = os.getenv("apple_developer_token")
    
    # Initialize Apple Music API instance
    am_api = AppleMusicAPI(developer_token)

    # Test Apple Music search suggestions for 'Shape of You'
    print("\nApple Music Search Suggestions for 'Shape of You':")
    suggestions = am_api.get_apple_music_suggestions("Shape of You")
    print(suggestions)
    print()
    print()

    # print(am_api.get_track_attributes("shape of you", "ed sheeran"))
    # print(type(am_api.get_track_attributes("shape of you", "ed sheeran")))
    for i in am_api.get_track_attributes("shape of you", "ed sheeran").keys():
        print(i)

    

    # Test similar tracks functionality
    # print("\nSimulated Similar Tracks to 'Shape of You' by 'Ed Sheeran':")
    # print(am_api.get_similar_tracks("Shape of You", "Ed Sheeran", limit=5))


if __name__ == "__main__":
    main()

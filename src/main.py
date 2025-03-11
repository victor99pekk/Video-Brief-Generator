import re
from TikAPI import TikAPIWrapper
from GoogleCloud import GCSVideoUploader
from GoogleVideoAnalyzer import GoogleVideoAnalyzer
import os
import yaml
from dotenv import load_dotenv


def load_config():
    """Load configuration from config.yaml with environment variables."""
    load_dotenv()  # Load environment variables from .env file
    
    # Try multiple paths to find the config file
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    potential_paths = [
        os.path.join(base_dir, 'config', 'config.yaml'),
        os.path.join(base_dir, 'config.yaml'),
        'config/config.yaml',
        'config.yaml'
    ]
    
    for config_path in potential_paths:
        if os.path.exists(config_path):
            print(f"Loading config from: {config_path}")
            
            # Read the file content
            with open(config_path, 'r') as file:
                content = file.read()
                
            # Replace environment variables using regex
            def replace_env_var(match):
                env_var = match.group(1)
                return os.environ.get(env_var, '')
                
            content = re.sub(r'\$\{([^}]+)\}', replace_env_var, content)
            
            # Parse the modified content
            config = yaml.safe_load(content)
            
            # Print the resolved values for debugging
            if 'services' in config and 'google' in config['services']:
                print(f"Resolved credentials path: {config['services']['google'].get('google_json')}")
                
            return config
    
    raise FileNotFoundError(f"Config file not found. Tried: {', '.join(potential_paths)}")

def analyze_and_process_videos(tikapi, uploader, analyzer, videos, n=3):
    """
    Process the top `n` videos: upload them to GCS, then run analysis.
    """
    if not videos:
        print("No videos found for analysis.")
        return

    for i, video in enumerate(videos[:n], start=1):
        video_id = video.get("id")
        if not video_id:
            continue

        print(f"\nProcessing Video {i}/{n} (ID: {video_id})")

        video_json = tikapi.get_video_metadata(video_id)
        if not video_json:
            continue

        gcs_url = uploader.upload_tiktok_video_direct(video_json)
        if not gcs_url:
            continue

        # labels = analyzer.analyze_video_labels(gcs_url)
        # print(f"Labels for video {video_id}: {labels}")


def main():
    config = load_config()
    tikapi_key = config['services']['tikapi']['key']
    tikapi = TikAPIWrapper(key=tikapi_key)

    # Google Cloud Storage setup
    bucket_name = config['services']['google']['bucket_name']
    google_json = config['services']['google']['google_json']
    uploader = GCSVideoUploader(GoogleJson_file=google_json, bucket_name=bucket_name)  
    analyzer = GoogleVideoAnalyzer()

    user_title = input("Enter song title: ")
    user_artist = input("Enter artist name: ")

    print("\nSearching for matching music on TikTok...")
    music_list = tikapi.search_music(user_title, user_artist)

    if not music_list:
        print("No songs found.")
        return

    if len(music_list) == 1:
        matched_song = music_list[0]
        print(f"Quick match: Music ID {matched_song}")
    else:
        matched_song = tikapi.find_matching_song(user_title, user_artist, music_list)
        if not matched_song:
            print("No close match found among multiple IDs.")
            return

    print(f"\nFetching videos for Music ID {matched_song}")
    music_videos = tikapi.fetch_music_videos(matched_song, limit=3)

    print("\nUploading & analyzing top videos...")
    analyze_and_process_videos(tikapi, uploader, analyzer, music_videos, n=3)


if __name__ == "__main__":
    main()

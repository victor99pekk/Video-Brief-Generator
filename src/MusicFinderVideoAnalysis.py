import os
import yaml
import sys
import re
import concurrent.futures
from dotenv import load_dotenv

from song_finder.SimilarSongs import SimilarSongs
from TikAPI import TikAPIWrapper
from GoogleCloud import GCSVideoUploader
# Import the updated GoogleVideoAnalyzer2, but let's call it the same:
from GoogleVideoAnalyzer2 import GoogleVideoAnalyzer2
# Keep your CompareFeatures if you want (the user said not to remove variables).
from CompareFeatures import CompareFeatures
# Now we use the updated OpenAITrend with new methods:
from OpenAITrend import OpenAITrendSummarizer


class MusicFinderVideoAnalysis:
    """
    A class that:
     - Finds similar songs via SimilarSongs
     - Searches TikTok for videos related to these songs
     - Uploads videos to Google Cloud
     - Analyzes each video with GoogleVideoAnalyzer2
     - Compares videos at the song level to find trends
     - Compares songs at the multi-song level
     - Finally uses OpenAITrendSummarizer to produce a big final production brief
    """

    def __init__(self, music_token: str, tiktok_key: str, google_json: str, bucket_name: str, LLM_key: str):
        """
        Initialize with all necessary credentials and clients.
        """
        self.music_token = music_token
        self.tiktok_key = tiktok_key
        self.google_json = google_json
        self.bucket_name = bucket_name

        # Keep your original references
        self.tiktok_api = TikAPIWrapper(key=self.tiktok_key)
        self.music_api = SimilarSongs(music_token=music_token, LLM_key=LLM_key)
        self.Uploader = GCSVideoUploader(self.google_json, bucket_name=self.bucket_name)
        self.Analyzer = GoogleVideoAnalyzer2()
        self.Comparator = CompareFeatures(threshold=0.5)  # not removing
        self.Summarizer = OpenAITrendSummarizer(api_key=LLM_key, model="gpt-3.5-turbo")

    def find_tiktoks_for_song(self, song: str, artist: str, limit_similar=2, limit_videos=2):
        """
        1) Finds similar tracks for a given (song, artist).
        2) For each track, fetch & analyze multiple TikTok videos.
        3) Summarize the trends for that track.
        4) Summarize across all tracks (similar songs).
        """
        similar_tracks = self.music_api.get_similar_tracks(song=song, artist=artist, limit=limit_similar)
        if not similar_tracks:
            print(f"No similar tracks found for '{song}' by '{artist}'.")
            return

        print("Similar tracks:", similar_tracks)

        # We'll store the results for each track here.
        # Example structure:
        # {
        #   (track_name, track_artist): {
        #       "video_features": [ { "video_uri": ..., "labels": [...], "objects": [...], "texts": [...], ...}, ... ],
        #       "trend_explanation": "..."
        #   },
        #   ...
        # }
        all_songs_data = {}

        # Process each similar track concurrently
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(similar_tracks)) as executor:
            future_to_track = {
                executor.submit(self._process_single_track, track_song, track_artist, limit_videos): (track_song, track_artist)
                for track_song, track_artist in similar_tracks
            }
            for future in concurrent.futures.as_completed(future_to_track):
                track_info = future_to_track[future]
                try:
                    result = future.result()
                    if result:
                        all_songs_data[(track_info[0], track_info[1])] = result
                except Exception as exc:
                    print(f"Track {track_info} generated an exception: {exc}")

        # Now we have data for each track, including a list of video feature dicts.
        # We'll ask the summarizer for each track's trends explanation
        # and store them in the same structure.
        song_level_trends = []
        for (trk_song, trk_artist), data_dict in all_songs_data.items():
            video_features = data_dict["video_features"]
            if video_features:
                explanation = self.Summarizer.generate_song_trends_explanation(video_features)
                data_dict["trend_explanation"] = explanation
                print(f"\n=== Trend Explanation for '{trk_song}' by '{trk_artist}' ===\n")
                print(explanation)
                song_level_trends.append(explanation)
            else:
                data_dict["trend_explanation"] = "No videos to analyze."

        # Finally, we generate an overall cross-song trend & final brief
        if song_level_trends:
            big_final_brief = self.Summarizer.generate_overall_trends_and_brief(song_level_trends)
            print("\n=== Overall Multi-Song Trend & Final Brief ===\n")
            print(big_final_brief)
        else:
            print("No videos found across all similar songs, cannot produce overall brief.")

    def _process_single_track(self, song: str, artist: str, limit_videos=2):
        """
        For a single track, fetch multiple TikTok videos, upload, analyze, gather feature sets.
        Return a dict: { "video_features": [...] }
        """
        print(f"\nProcessing track: '{song}' by '{artist}'")
        track_data = {
            "video_features": []
        }

        # A) Search music on TikTok
        music_list = self.tiktok_api.search_music(song, artist)
        matched_song = self.tiktok_api.find_matching_song(song, artist, music_list)
        if not matched_song:
            print(f"No matching song found on TikTok for '{song}' by '{artist}'.")
            return track_data  # empty

        # B) Fetch top TikTok videos
        music_videos = self.tiktok_api.fetch_music_videos(matched_song, limit=limit_videos)
        if not music_videos:
            print(f"No videos found on TikTok for '{song}' by '{artist}'.")
            return track_data  # empty

        # C) Upload & analyze
        gcs_uris = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(music_videos)) as executor:
            future_to_vid = {
                executor.submit(self._upload_video_and_analyze, vid): vid for vid in music_videos
            }
            for future in concurrent.futures.as_completed(future_to_vid):
                analysis_result = future.result()
                if analysis_result:
                    track_data["video_features"].append(analysis_result)

        return track_data

    def _upload_video_and_analyze(self, video: dict):
        """
        Upload a single video to GCS, then analyze it, print scene details,
        build a minimal 'video_features' dict (labels, objects, texts, etc.).
        """
        video_id = video.get("id")
        if not video_id:
            return None

        print(f"Uploading Video (ID: {video_id})...")
        video_json = self.tiktok_api.get_video_metadata(video_id)
        if not video_json:
            print(f"No metadata for video {video_id}.")
            return None

        gcs_url = self.Uploader.upload_tiktok_video_direct(video_json)
        if not gcs_url:
            print(f"Upload failed for {video_id}.")
            return None

        # Analyze
        batch_results = self.Analyzer.analyze_videos_in_batch([gcs_url], timeout=600)
        if not batch_results:
            print(f"No analysis for {video_id}.")
            return None

        # We'll just have 1 result
        result = batch_results[0]
        video_uri = result["video_uri"]
        analysis = result["analysis"]

        # Print the structured scene info
        print("\n=== Analysis Results ===")
        print(f"Video URI: {video_uri}")
        shots = analysis.get("shots", [])
        for shot in shots:
            print(f"  Shot #{shot['shot_number']}: {shot['start_time']}s → {shot['end_time']}s")
            print("    Segment Labels:", shot.get("segment_labels"))
            print("    Shot Labels:", shot.get("shot_labels"))
            print("    Frame Labels:", shot.get("frame_labels"))
            print("    Objects:", [obj["object_description"] for obj in shot.get("objects", [])])
            print("    Texts:", [t["text"] for t in shot.get("texts", [])])
            print("    Logos:", [l["logo_description"] for l in shot.get("logos", [])])
            print("    Persons:", shot.get("persons", []))
            print("    Speech Transcriptions:", shot.get("speech_transcriptions", []))
            print("    Explicit Frames:", shot.get("explicit_frames", []))
            print()

        # Now produce a scene-by-scene description
        if shots:
            scene_desc = self.Summarizer.describe_video_scenes(shots)
            print("\nScene-by-scene description:")
            print(scene_desc)
        print("=================================\n")

        # Build a simplified "video_features" dict for trend analysis
        combined_labels = set()
        combined_objects = set()
        combined_texts = set()

        # We can gather all segment/shot/frame labels into one set
        for shot in shots:
            for lbl in shot.get("segment_labels", []):
                combined_labels.add(lbl)
            for lbl in shot.get("shot_labels", []):
                combined_labels.add(lbl)
            for lbl in shot.get("frame_labels", []):
                combined_labels.add(lbl)
            for obj in shot.get("objects", []):
                combined_objects.add(obj["object_description"])
            for txt in shot.get("texts", []):
                combined_texts.add(txt["text"])

        return {
            "video_uri": video_uri,
            "labels": list(combined_labels),
            "objects": list(combined_objects),
            "texts": list(combined_texts)
        }


def load_config_and_initialize():
    """
    Load configuration from YAML file and initialize the MusicFinderVideoAnalysis.
    """
    load_dotenv()
    config_path = "config/config.yaml"

    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found at: {config_path}")

    with open(config_path, 'r') as file:
        config = yaml.safe_load(file)

    services = config.get('services', {})
    applemusic = services.get('applemusic', {})
    tikapi = services.get('tikapi', {})
    google = services.get('google', {})
    openai = services.get('openai', {})

    applemusic_token = applemusic.get('developer_token')
    tikapi_key = tikapi.get('key')
    google_json = google.get('google_json')
    bucket_name = google.get('bucket_name')
    openai_key = openai.get('api_key')  # LLM_key

    missing = []
    if not applemusic_token: missing.append("applemusic_token")
    if not tikapi_key: missing.append("tikapi_key")
    if not google_json: missing.append("google_json")
    if not bucket_name: missing.append("bucket_name")
    if not openai_key: missing.append("openai_key")

    if missing:
        raise ValueError(f"Missing required configuration: {', '.join(missing)}")

    finder = MusicFinderVideoAnalysis(
        music_token=applemusic_token,
        tiktok_key=tikapi_key,
        google_json=google_json,
        bucket_name=bucket_name,
        LLM_key=openai_key
    )
    return finder


if __name__ == "__main__":
    try:
        music_finder = load_config_and_initialize()
        song = input("Enter a song name: ")
        artist = input("Enter the artist name: ")
        # e.g. limit_similar=2 means we find 2 similar tracks, each track we analyze 2 videos
        music_finder.find_tiktoks_for_song(song=song, artist=artist, limit_similar=2, limit_videos=2)
    except Exception as e:
        print(f"Error: {e}")
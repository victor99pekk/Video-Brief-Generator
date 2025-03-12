from GoogleVideoAnalyzer import GoogleVideoAnalyzer
from LastfmAPI import LastfmAPI
from TikAPI import TikAPIWrapper
from GoogleCloud import GCSVideoUploader
from CompareFeatures import CompareFeatures
from OpenAITrend import OpenAITrendSummarizer
import concurrent.futures


class ViralMusicFinder:
    def __init__(self, API_KEY:str, API_SECRET:str, OPENAI_API_KEY:str):

        self.API_KEY = API_KEY
        self.API_SECRET = API_SECRET
        self.OPENAI_API_KEY = OPENAI_API_KEY

        self.music_api = LastfmAPI(API_KEY, API_SECRET)
        self.tiktok_api = TikAPIWrapper()
        self.Uploader = GCSVideoUploader()
        self.Analyzer = GoogleVideoAnalyzer()  # multi-threaded analysis
        self.Comparator = CompareFeatures(threshold=0.5)
        self.Summarizer = OpenAITrendSummarizer(api_key=OPENAI_API_KEY, model="gpt-3.5-turbo")

    def find_tiktoks(self, song: str = None, artist: str = None) -> None:
        # 1. Get similar tracks from Last.fm
        similar_tracks = self.music_api.get_similar_tracks(song=song, artist=artist, limit=3)
        if not similar_tracks:
            print("No similar tracks found.")
            return

        # Process each similar track concurrently
        print(f"Found {len(similar_tracks)} similar tracks.")
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(similar_tracks)) as executor:
            future_to_track = {
                executor.submit(self.process_similar_track, track_song, track_artist): (track_song, track_artist)
                for track_song, track_artist in similar_tracks
            }
            for future in concurrent.futures.as_completed(future_to_track):
                track_info = future_to_track[future]
                try:
                    result = future.result()
                    if result:
                        results.append(result)
                except Exception as exc:
                    print(f"Track {track_info} generated an exception: {exc}")

        # Print individual track summaries
        for res in results:
            print(f"\n=== Summary for '{res['song']}' by {res['artist']} ===")
            print(res['summary'])

        # Aggregate trends from all similar tracks
        aggregated_trends = {}
        for res in results:
            trends = res.get("trends")
            if trends:
                for key, items in trends.items():
                    aggregated_trends.setdefault(key, []).extend(items)

        if aggregated_trends:
            overall_summary = self.Summarizer.summarize_trends(aggregated_trends)
            print(overall_summary)
        else:
            print("No trends available")

    def process_similar_track(self, song: str, artist: str, video_limit=4):
        """
         Search for the song on TikTok.
         Fetch its videos.
         Analyze and compare video features.
         Generate a trend summary for the track.
        """
        print(f"\nProcessing similar track: '{song}' by {artist}")
        # 1. Search music on TikTok & find a matching track
        music_list = self.tiktok_api.search_music(song, artist)
        matched_song = self.tiktok_api.find_matching_song(song, artist, music_list)
        if not matched_song:
            print(f"No matching song found on TikTok for '{song}' by {artist}.")
            return None

        # 2. Fetch top TikTok videos for this track
        music_videos = self.tiktok_api.fetch_music_videos(matched_song, limit=3)
        if not music_videos:
            print(f"No videos found for '{song}' by {artist}.")
            return None

        # 3. Analyze and process the videos for this track
        trends, summary = self.analyze_and_process_videos_for_track(music_videos, n=video_limit)
        if not trends:
            print(f"Could not detect trends for '{song}' by {artist}.")
            return None

        return {
            "song": song,
            "artist": artist,
            "trends": trends,
            "summary": summary
        }

    def analyze_and_process_videos_for_track(self, videos, n=4):
        """
        Multithread the upload of up to `n` TikTok videos.
        Collect GCS URIs.
        Analyze the videos
        Process the analysis into feature dictionaries.
        Compare features to detect trends and summarize with OpenAI.
        Returns tuple (trends, summary).
        """
        if not videos:
            print("No videos found for analysis.")
            return None, None

        gcs_uris = []

        def process_video_upload(video):
            video_id = video.get("id")
            if not video_id:
                print("Video missing ID, skipping.")
                return None
            print(f"Uploading Video (ID: {video_id})")
            video_json = self.tiktok_api.get_video_metadata(video_id)
            if not video_json:
                print(f"No metadata found for video {video_id}.")
                return None
            gcs_url = self.Uploader.upload_tiktok_video_direct(video_json)
            if not gcs_url:
                print(f"Unable to upload video {video_id} to GCS.")
                return None
            return gcs_url

        with concurrent.futures.ThreadPoolExecutor(max_workers=n) as executor:
            future_to_video = {
                executor.submit(process_video_upload, video): video for video in videos[:n]
            }
            for future in concurrent.futures.as_completed(future_to_video):
                gcs_url = future.result()
                if gcs_url:
                    gcs_uris.append(gcs_url)

        if not gcs_uris:
            print("No GCS URIs to analyze.")
            return None, None


        batch_results = self.Analyzer.analyze_videos_in_batch(video_uris=gcs_uris, timeout=600)

        video_features = []
        for result_obj in batch_results:
            video_analysis = result_obj["analysis"]
            combined_labels = set(video_analysis.get("segment_labels", [])) | set(video_analysis.get("shot_labels", []))
            objects_list = [obj["object_description"] for obj in video_analysis.get("objects", [])] if "objects" in video_analysis else []
            texts_list = [txt["text"] for txt in video_analysis.get("texts", [])] if "texts" in video_analysis else []
            feature_dict = {
                "labels": list(combined_labels),
                "objects": objects_list,
                "texts": texts_list
            }
            video_features.append(feature_dict)

        if len(video_features) > 1:
            trends = self.Comparator.detect_trends(video_features)
            print("\nDetected Trends for this track:")
            for category, items in trends.items():
                print(f" - {category}: {items}")
            summary = self.Summarizer.summarize_trends(trends)
            return trends, summary
        else:
            print("Only 1 or0 videos processed; skipping trend comparison.")
            return None, None

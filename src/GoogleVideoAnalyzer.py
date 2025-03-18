import os
import concurrent.futures
from google.cloud import videointelligence
from google.cloud.videointelligence_v1.types import (
    AnnotateVideoRequest,
    VideoContext,
    LabelDetectionConfig,
    LabelDetectionMode
)
# os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(
#     os.path.dirname(__file__), "GoogleKey.json"
# )

class GoogleVideoAnalyzer:
    """
    A class that leverages Google Cloud's Video Intelligence API to analyze video content.
    
    This class provides methods to extract detailed metadata from videos, including scene 
    detection, object tracking, label detection, text recognition, and explicit content 
    analysis. It supports batch processing with concurrent execution for improved performance.
    
    Attributes:
        client (videointelligence.VideoIntelligenceServiceClient): The Google Video Intelligence API client
    """
    def __init__(self, credentials_path:str=None):
        """
        Initialize the Google Video Analyzer with a Video Intelligence client.
        
        The initialization automatically uses the Google credentials from the environment
        variables or from the GoogleKey.json file in the same directory.
        
        Raises:
            google.auth.exceptions.DefaultCredentialsError: If no valid credentials are found
        """
        # Set credentials path if provided
        # if credentials_path:
        #     # Store original value to restore later if needed
        #     original_credentials = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS")
        #     os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = credentials_path
        #     self._temp_credentials_set = True
        #     self._original_credentials = original_credentials
        # else:
        #     self._temp_credentials_set = False
        self.client = videointelligence.VideoIntelligenceServiceClient()

    def process_single_video(self, uri, timeout, features, video_context):
        """
        Process a single video and extract metadata using Google's Video Intelligence API.
        
        Args:
            uri (str): The Cloud Storage URI of the video to be analyzed
            timeout (int): Maximum time to wait for the analysis to complete, in seconds
            features (list): List of video intelligence features to analyze
            video_context (VideoContext): Configuration for the video analysis
            
        Returns:
            dict: A dictionary containing the video URI and its analysis results
            
        Raises:
            google.api_core.exceptions.GoogleAPIError: If the API request fails
            concurrent.futures.TimeoutError: If the analysis times out
        """
        print(f"Processing video: {uri}")
        request = AnnotateVideoRequest(
            input_uri=uri,
            features=features,
            video_context=video_context
        )
        operation = self.client.annotate_video(request=request)
        response = operation.result(timeout=timeout)
        annotation_result = response.annotation_results[0]
        video_info = self._parse_annotation_result(annotation_result)
        return {"video_uri": uri, "analysis": video_info}

    def analyze_videos_in_batch(self, video_uris, timeout=600):
        """
        Analyze multiple videos concurrently for improved performance.
        
        Args:
            video_uris (list): List of Cloud Storage URIs for videos to analyze
            timeout (int, optional): Maximum time to wait for each video analysis, in seconds.
                                     Defaults to 600 seconds (10 minutes).
            
        Returns:
            list: A list of dictionaries containing analysis results for each video
            
        Notes:
            This method processes videos in parallel threads to improve performance.
            The number of concurrent workers is equal to the number of videos being processed.
        """
        if not video_uris:
            return []

        features = [
            videointelligence.Feature.LABEL_DETECTION,
            videointelligence.Feature.SHOT_CHANGE_DETECTION,
            videointelligence.Feature.OBJECT_TRACKING,
            videointelligence.Feature.TEXT_DETECTION,
            videointelligence.Feature.EXPLICIT_CONTENT_DETECTION,
        ]

        video_context = VideoContext(
            label_detection_config=LabelDetectionConfig(
                label_detection_mode=LabelDetectionMode.SHOT_AND_FRAME_MODE,
                stationary_camera=False
            )
        )

        print(f"Analyzing {len(video_uris)} videos concurrently...")
        batch_results = []

        with concurrent.futures.ThreadPoolExecutor(max_workers=len(video_uris)) as executor:
            future_to_uri = {
                executor.submit(self.process_single_video, uri, timeout, features, video_context): uri
                for uri in video_uris
            }
            for future in concurrent.futures.as_completed(future_to_uri):
                uri = future_to_uri[future]
                try:
                    result = future.result()
                    batch_results.append(result)
                except Exception as exc:
                    print(f"Video {uri} generated an exception: {exc}")

        return batch_results

    def _parse_annotation_result(self, annotation_result):
        """
        Parse and organize the raw annotation results from the Video Intelligence API.
        
        Args:
            annotation_result (videointelligence.AnnotationResult): The raw annotation result
                                                                   from the API
            
        Returns:
            dict: A structured dictionary containing organized video metadata including:
                  - Shot boundaries
                  - Labels (segment, shot, frame, and category)
                  - Tracked objects with bounding boxes
                  - Detected text
                  - Explicit content markers
                  - Environment type inference (indoor/outdoor)
        
        Note:
            This is an internal method used to transform the complex API response
            into a more accessible data structure.
        """
        data = {}

        # 1) Shot Annotations
        shots_info = []
        if annotation_result.shot_annotations:
            for i, shot in enumerate(annotation_result.shot_annotations):
                start_sec = shot.start_time_offset.total_seconds()
                end_sec = shot.end_time_offset.total_seconds()
                shots_info.append({
                    "shot_number": i + 1,
                    "start_time": start_sec,
                    "end_time": end_sec
                })
        data["shots"] = shots_info

        # 2) Label Annotations
        segment_labels = []
        shot_labels = []
        frame_labels = []
        category_labels = []

        if annotation_result.segment_label_annotations:
            for seg_label in annotation_result.segment_label_annotations:
                segment_labels.append(seg_label.entity.description)
                for category in seg_label.category_entities:
                    category_labels.append(category.description)
        if annotation_result.shot_label_annotations:
            for s_label in annotation_result.shot_label_annotations:
                shot_labels.append(s_label.entity.description)
                for category in s_label.category_entities:
                    category_labels.append(category.description)
        if annotation_result.frame_label_annotations:
            for f_label in annotation_result.frame_label_annotations:
                frame_labels.append(f_label.entity.description)
                for category in f_label.category_entities:
                    category_labels.append(category.description)

        data["segment_labels"] = list(set(segment_labels))
        data["shot_labels"] = list(set(shot_labels))
        data["frame_labels"] = list(set(frame_labels))
        data["category_labels"] = list(set(category_labels))

        # 3) Object Tracking
        objects_info = []
        if annotation_result.object_annotations:
            for obj_annotation in annotation_result.object_annotations:
                obj_desc = obj_annotation.entity.description
                seg_start = obj_annotation.segment.start_time_offset.total_seconds()
                seg_end = obj_annotation.segment.end_time_offset.total_seconds()
                frames_data = []
                for frame in obj_annotation.frames:
                    box = frame.normalized_bounding_box
                    frames_data.append({
                        "time_offset_sec": frame.time_offset.total_seconds(),
                        "bounding_box": {
                            "left": box.left,
                            "top": box.top,
                            "right": box.right,
                            "bottom": box.bottom
                        }
                    })
                objects_info.append({
                    "object_description": obj_desc,
                    "segment_start": seg_start,
                    "segment_end": seg_end,
                    "frames": frames_data
                })
        data["objects"] = objects_info

        # 4) Text Detection
        texts_info = []
        if annotation_result.text_annotations:
            for text_anno in annotation_result.text_annotations:
                recognized_text = text_anno.text
                text_segments = []
                for seg in text_anno.segments:
                    seg_start = seg.segment.start_time_offset.total_seconds()
                    seg_end = seg.segment.end_time_offset.total_seconds()
                    confidence = getattr(seg, "confidence", None)
                    frames_data = []
                    for f in seg.frames:
                        box = f.rotated_bounding_box
                        poly = []
                        if box:
                            poly = [{"x": v.x, "y": v.y} for v in box.vertices]
                        frames_data.append({
                            "time_offset_sec": f.time_offset.total_seconds(),
                            "bounding_polygon": poly
                        })
                    text_segments.append({
                        "segment_start": seg_start,
                        "segment_end": seg_end,
                        "confidence": confidence,
                        "frames": frames_data
                    })
                texts_info.append({
                    "text": recognized_text,
                    "text_segments": text_segments
                })
        data["texts"] = texts_info

        # 5) Explicit Content
        explicit_info = []
        if annotation_result.explicit_annotation:
            for frame in annotation_result.explicit_annotation.frames:
                offset_sec = frame.time_offset.total_seconds()
                likelihood_str = frame.pornography_likelihood.name
                explicit_info.append({
                    "time_offset_sec": offset_sec,
                    "pornography_likelihood": likelihood_str
                })
        data["explicit_content"] = explicit_info

        # 6) Environment Guess
        all_label_strings = (
            data["segment_labels"] +
            data["shot_labels"] +
            data["frame_labels"] +
            data["category_labels"]
        )
        label_set = {lbl.lower() for lbl in all_label_strings}
        if "outdoor" in label_set:
            data["environment_guess"] = "outdoors"
        elif "indoor" in label_set or "indoors" in label_set:
            data["environment_guess"] = "indoors"
        else:
            data["environment_guess"] = None

        return data
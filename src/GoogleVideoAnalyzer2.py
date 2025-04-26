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

class GoogleVideoAnalyzer2:
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
        #     ...
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
        """
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
        """
        if not video_uris:
            return []

        # Added speech, logo, person as requested in a prior step
        features = [
            videointelligence.Feature.LABEL_DETECTION,
            videointelligence.Feature.SHOT_CHANGE_DETECTION,
            videointelligence.Feature.OBJECT_TRACKING,
            videointelligence.Feature.TEXT_DETECTION,
            videointelligence.Feature.EXPLICIT_CONTENT_DETECTION,
            videointelligence.Feature.SPEECH_TRANSCRIPTION,
            videointelligence.Feature.LOGO_RECOGNITION,
            videointelligence.Feature.PERSON_DETECTION,
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
        Parse and organize the raw annotation results from the Video Intelligence API
        into a scene-by-scene (shot-by-shot) structure with labels, objects, text, etc.
        
        Returns:
            dict: Data with a "shots" key, listing each shot's metadata:
                  - segment_labels, shot_labels, frame_labels, objects, texts, logos, persons, speech, etc.
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
                    "end_time": end_sec,
                    "segment_labels": [],
                    "shot_labels": [],
                    "frame_labels": [],
                    "objects": [],
                    "logos": [],
                    "persons": [],
                    "texts": [],
                    "speech_transcriptions": [],
                    "explicit_frames": []
                })
        data["shots"] = shots_info

        # Overlap helper
        def do_overlap(range1, range2):
            return not (range2[1] < range1[0] or range2[0] > range1[1])

        # 2) Segment Label Annotations
        if annotation_result.segment_label_annotations:
            for seg_label in annotation_result.segment_label_annotations:
                label_desc = seg_label.entity.description
                for seg in seg_label.segments:
                    seg_start = seg.segment.start_time_offset.total_seconds()
                    seg_end = seg.segment.end_time_offset.total_seconds()
                    for shot_dict in shots_info:
                        shot_range = (shot_dict["start_time"], shot_dict["end_time"])
                        if do_overlap(shot_range, (seg_start, seg_end)):
                            shot_dict["segment_labels"].append(label_desc)

        # 3) Shot Label Annotations
        if annotation_result.shot_label_annotations:
            for s_label in annotation_result.shot_label_annotations:
                label_desc = s_label.entity.description
                for seg in s_label.segments:
                    seg_start = seg.segment.start_time_offset.total_seconds()
                    seg_end = seg.segment.end_time_offset.total_seconds()
                    for shot_dict in shots_info:
                        shot_range = (shot_dict["start_time"], shot_dict["end_time"])
                        if do_overlap(shot_range, (seg_start, seg_end)):
                            shot_dict["shot_labels"].append(label_desc)

        # 4) Frame Label Annotations
        if annotation_result.frame_label_annotations:
            for f_label in annotation_result.frame_label_annotations:
                label_desc = f_label.entity.description
                for f_segment in f_label.segments:
                    for frame in f_segment.frames:
                        frame_offset = frame.time_offset.total_seconds()
                        for shot_dict in shots_info:
                            if shot_dict["start_time"] <= frame_offset <= shot_dict["end_time"]:
                                shot_dict["frame_labels"].append(label_desc)

        # 5) Object Tracking Annotations
        if annotation_result.object_annotations:
            for obj_annotation in annotation_result.object_annotations:
                obj_desc = obj_annotation.entity.description
                seg_start = obj_annotation.segment.start_time_offset.total_seconds()
                seg_end = obj_annotation.segment.end_time_offset.total_seconds()
                for shot_dict in shots_info:
                    shot_range = (shot_dict["start_time"], shot_dict["end_time"])
                    if do_overlap(shot_range, (seg_start, seg_end)):
                        frames_data = []
                        for frame in obj_annotation.frames:
                            frame_time = frame.time_offset.total_seconds()
                            if shot_dict["start_time"] <= frame_time <= shot_dict["end_time"]:
                                box = frame.normalized_bounding_box
                                frames_data.append({
                                    "time_offset_sec": frame_time,
                                    "bounding_box": {
                                        "left": box.left,
                                        "top": box.top,
                                        "right": box.right,
                                        "bottom": box.bottom
                                    }
                                })
                        shot_dict["objects"].append({
                            "object_description": obj_desc,
                            "object_segment_start": seg_start,
                            "object_segment_end": seg_end,
                            "frames": frames_data
                        })

        # 6) Text Annotations
        if annotation_result.text_annotations:
            for text_anno in annotation_result.text_annotations:
                recognized_text = text_anno.text
                for seg in text_anno.segments:
                    seg_start = seg.segment.start_time_offset.total_seconds()
                    seg_end = seg.segment.end_time_offset.total_seconds()
                    confidence = getattr(seg, "confidence", None)
                    for shot_dict in shots_info:
                        if do_overlap((shot_dict["start_time"], shot_dict["end_time"]),
                                      (seg_start, seg_end)):
                            frames_data = []
                            for f in seg.frames:
                                frame_time = f.time_offset.total_seconds()
                                if shot_dict["start_time"] <= frame_time <= shot_dict["end_time"]:
                                    box = f.rotated_bounding_box
                                    poly = []
                                    if box:
                                        poly = [{"x": v.x, "y": v.y} for v in box.vertices]
                                    frames_data.append({
                                        "time_offset_sec": frame_time,
                                        "bounding_polygon": poly
                                    })
                            shot_dict["texts"].append({
                                "text": recognized_text,
                                "text_segment_start": seg_start,
                                "text_segment_end": seg_end,
                                "confidence": confidence,
                                "frames": frames_data
                            })

        # 7) Explicit Content
        if annotation_result.explicit_annotation:
            for frame in annotation_result.explicit_annotation.frames:
                offset_sec = frame.time_offset.total_seconds()
                likelihood_str = frame.pornography_likelihood.name
                for shot_dict in shots_info:
                    if shot_dict["start_time"] <= offset_sec <= shot_dict["end_time"]:
                        shot_dict["explicit_frames"].append({
                            "time_offset_sec": offset_sec,
                            "pornography_likelihood": likelihood_str
                        })

        # 8) Speech Transcriptions
        if annotation_result.speech_transcriptions:
            for transcription in annotation_result.speech_transcriptions:
                for alternative in transcription.alternatives:
                    for word_info in alternative.words:
                        start_sec = word_info.start_time.total_seconds()
                        end_sec = word_info.end_time.total_seconds()
                        text_word = word_info.word
                        confidence = word_info.confidence
                        for shot_dict in shots_info:
                            # If this word overlaps the shot range
                            if do_overlap((shot_dict["start_time"], shot_dict["end_time"]),
                                          (start_sec, end_sec)):
                                shot_dict["speech_transcriptions"].append({
                                    "word": text_word,
                                    "start_time": start_sec,
                                    "end_time": end_sec,
                                    "confidence": confidence
                                })

        # 9) Logo Recognition
        if annotation_result.logo_recognition_annotations:
            for logo_anno in annotation_result.logo_recognition_annotations:
                logo_desc = logo_anno.entity.description
                for seg in logo_anno.segments:
                    seg_start = seg.segment.start_time_offset.total_seconds()
                    seg_end = seg.segment.end_time_offset.total_seconds()
                    for shot_dict in shots_info:
                        if do_overlap((shot_dict["start_time"], shot_dict["end_time"]),
                                      (seg_start, seg_end)):
                            shot_dict["logos"].append({
                                "logo_description": logo_desc,
                                "segment_start": seg_start,
                                "segment_end": seg_end
                            })

        return data
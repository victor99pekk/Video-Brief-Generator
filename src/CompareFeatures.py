from collections import Counter
from typing import List, Dict

class CompareFeatures:
    """
    Class to compare extracted features (labels, objects, texts, etc.)
    from multiple videos and identify trends or similarities.
    
    This class analyzes video metadata extracted by GoogleVideoAnalyzer to detect
    common elements across multiple videos, which can indicate trending content
    characteristics or important visual/textual patterns.
    
    Attributes:
        threshold (float): The minimum proportion of videos that must contain a feature
                           for it to be considered a trend (between 0.0 and 1.0)
    """

    def __init__(self, threshold: float = 0.5):
        """
        Initialize the feature comparison engine with a specified threshold.
        
        Args:
            threshold (float, optional): The minimum proportion of videos that must 
                                         contain a feature for it to be considered a trend.
                                         Defaults to 0.5 (50% of videos).
        
        Note:
            Setting threshold=1.0 would only return features present in all videos.
            Setting threshold=0.0 would return all features from any video.
        """
        self.threshold = threshold

    def detect_trends(self, video_features: List[Dict]) -> Dict:
        """
        Analyze a collection of video features to detect common trends across videos.
        
        Args:
            video_features (List[Dict]): A list of dictionaries where each dictionary 
                                        contains features extracted from a single video.
                                        Each dictionary should have keys 'labels', 'objects', 
                                        and 'texts' with lists of corresponding features.
        
        Returns:
            Dict: A dictionary containing identified trends organized by feature type:
                  - label_trends: Common video labels/categories
                  - object_trends: Common objects detected in videos
                  - text_trends: Common text elements appearing in videos
        
        """
        total_videos = len(video_features)
        if total_videos == 0:
            return {}

        label_trends = self._compare_category(video_features, "labels", total_videos)
        object_trends = self._compare_category(video_features, "objects", total_videos)
        text_trends = self._compare_category(video_features, "texts", total_videos)
        return {
            "label_trends": label_trends,
            "object_trends": object_trends,
            "text_trends": text_trends,
        }

    def _compare_category(self, video_features: List[Dict], key: str, total_videos: int) -> List[str]:
        """
        Compare a specific category of features across all videos to find trends.
        
        Args:
            video_features (List[Dict]): List of video feature dictionaries
            key (str): The feature category to compare ('labels', 'objects', or 'texts')
            total_videos (int): Total number of videos being analyzed
        
        Returns:
            List[str]: A list of trending features in the specified category
        
        Note:
            This is an internal helper method used by detect_trends().
        """
        all_items = []
        for vf in video_features:
            items = vf.get(key, [])
            all_items.extend(items)

        frequency = Counter(all_items)

        min_count = int(self.threshold * total_videos)
        if min_count < 1 and total_videos > 0:
            min_count = 1

        trending_features = [item for item, freq in frequency.items() if freq >= min_count]
        return trending_features

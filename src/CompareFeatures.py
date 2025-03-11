from collections import Counter
from typing import List, Dict

class CompareFeatures:
    """
    Class to compare extracted features (labels, objects, texts, etc.)
    from multiple videos and identify trends or similarities.
    """

    def __init__(self, threshold: float = 0.5):
        self.threshold = threshold

    def detect_trends(self, video_features: List[Dict]) -> Dict:
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

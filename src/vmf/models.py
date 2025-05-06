from pydantic import BaseModel
from typing import List, Dict

class TrackTrend(BaseModel):
    song: str
    artist: str
    summary: str
    trends: Dict[str, List[str]]

class TrendReport(BaseModel):
    brief: str
    tracks: List[TrackTrend]

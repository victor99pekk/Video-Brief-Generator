"""
Core wrapper around the old ViralMusicFinder class,
refactored to return Pydantic models instead of raw dicts.
"""
from __future__ import annotations
import logging, os
from typing import Optional, List
from dotenv import load_dotenv
import pathlib

load_dotenv(pathlib.Path(__file__).resolve().parents[2] / ".env")

from ViralMusicFinder import ViralMusicFinder as _OldFinder
from .models import TrendReport, TrackTrend

log = logging.getLogger(__name__)


class ViralMusicFinder(_OldFinder):
    """Subclass the original implementation so we don’t break any internals."""

    @classmethod
    def from_env(cls) -> "ViralMusicFinder":
        """Pull secrets from environment variables—keeps FastAPI config simple."""
        return cls(
            music_token=os.environ["APPLE_DEVELOPER_TOKEN"],
            LLM_key=os.environ["OPENAI_API_KEY"],
            tiktok_key=os.environ["TIKTOK_API_KEY"],
            google_json=os.environ["GOOGLE_APPLICATION_CREDENTIALS"],
            bucket_name=os.environ["GCS_BUCKET"],
        )

    # ----------  NEW PUBLIC ENTRY POINT  ----------
    def generate_trend_report(
        self, *, song: Optional[str] = None, artist: Optional[str] = None
    ) -> TrendReport:
        raw = self.find_tiktoks(song=song, artist=artist)
        # If the old code returns a str on error, raise:
        if not isinstance(raw, dict):
            raise RuntimeError(raw)  # fast fail for HTTP 400

        tracks: List[TrackTrend] = [
            TrackTrend(**item) for item in raw.get("track_details", [])
        ]
        return TrendReport(brief=raw["overall_summary"], tracks=tracks)


# Convenience function (used by FastAPI)
def generate_trend_report(
    song: Optional[str] = None, artist: Optional[str] = None
) -> TrendReport:
    finder = ViralMusicFinder.from_env()
    return finder.generate_trend_report(song=song, artist=artist)

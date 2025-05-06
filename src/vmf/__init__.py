"""
vmf – Viral Music Finder public interface
Adds the project’s src/ folder to PYTHONPATH so legacy helpers
(GoogleVideoAnalyzer2.py, TikAPI.py, …) can be imported unchanged.
"""

from __future__ import annotations
import sys, pathlib

# ── Patch PYTHONPATH ──────────────────────────────────────────────
_src_root = pathlib.Path(__file__).resolve().parent.parent  # …/Video-Brief-Generator/src
if str(_src_root) not in sys.path:
    sys.path.insert(0, str(_src_root))  # put it first so it wins

# ── Re-export high-level helpers ─────────────────────────────────
from .core import generate_trend_report, ViralMusicFinder  # noqa: E402  (after path patch)

__all__ = ["generate_trend_report", "ViralMusicFinder"]

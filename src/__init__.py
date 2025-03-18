"""
Parasition Music Analysis Tools - Discover viral music trends and content opportunities.
"""

# Explicitly import each module
from .ViralMusicFinder import ViralMusicFinder, load_config_and_initialize
from .LastfmAPI import LastfmAPI
from .TikAPI import TikAPIWrapper
from .GoogleCloud import GCSVideoUploader
from .GoogleVideoAnalyzer import GoogleVideoAnalyzer
from .OpenAITrend import OpenAITrendSummarizer
from .CompareFeatures import CompareFeatures

# Make specific classes and functions available directly
# from .ViralMusicFinder import ViralMusicFinder, load_config_and_initialize
# from .LastfmAPI import LastfmAPI
# from .TikAPI import TikAPIWrapper
# from .GoogleCloud import GCSVideoUploader
# from .GoogleVideoAnalyzer import GoogleVideoAnalyzer
# from .OpenAITrend import OpenAITrendSummarizer
# from .CompareFeatures import CompareFeatures

# Define what's available with "from src import *"
# __all__ = [
#     # Classes
#     'ViralMusicFinder',
#     'LastfmAPI', 
#     'TikAPIWrapper', 
#     'GCSVideoUploader', 
#     'GoogleVideoAnalyzer', 
#     'OpenAITrendSummarizer', 
#     'CompareFeatures',
    
#     # Functions
#     'load_config_and_initialize',
    
#     # Modules
#     'ViralMusicFinder',
#     'LastfmAPI',
#     'TikAPI',
#     'GoogleCloud',
#     'GoogleVideoAnalyzer',
#     'OpenAITrend',
#     'CompareFeatures'
# ]
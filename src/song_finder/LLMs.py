from openai import OpenAI


class LLM_SongRecommender:
    """
    A class that uses a number of different LLM models to find similar songs
    """
    def __init__(self, model_to_key:dict()):
        
        

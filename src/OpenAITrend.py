from openai import OpenAI
from openai import OpenAI

class OpenAITrendSummarizer:
    """
    Uses OpenAI's Chat API to generate natural language summaries of detected video trends.
    """
    def __init__(self, api_key:str, model: str = "gpt-3.5-turbo"):
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def summarize_trends(self, trends: dict) -> str:
        """
        Summarizes the detected trends into a human-readable format.
        :param trends: A dictionary with keys like "labels", "objects", "texts".
        :return: A string containing the generated summary.
        """
        prompt = self._build_prompt(trends)
        try:
            print("Using OpenAI client with model:", self.model)
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert social media marketing AI. "
                            "You analyze repeated elements found in TikTok videos and provide insights. "
                            "You then give a brief for social media creators, specifying video concepts, backgrounds, number of people, text (size, position), etc. "
                            "Here is an example brief: Slideshow med on screen captions som består av tre bilder. De två första visar nostalgi från det förflutna, och den sista visar hur det ser ut idag."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.7,
                max_tokens=300
            )
            summary = response.choices[0].message.content.strip()
            return summary

        except Exception as e:
            print(f"OpenAI API error: {e}")
            return "Error generating summary."

    def _build_prompt(self, trends: dict) -> str:
        """
        Builds a user-friendly prompt listing the repeated features.
        """
        lines = [
            "We have identified the following recurring features from multiple TikTok videos:\n"
        ]
        for category, items in trends.items():
            readable_cat = category.replace("_", " ").title()
            if items:
                line = f"{readable_cat}: {', '.join(items)}"
            else:
                line = f"{readable_cat}: (No items found)"
            lines.append(line)
        lines.append(
            "\nPlease provide a concise summary of these repeated features, focusing on any themes, "
            "ideas, or potential video concepts they might represent. Then, be specific and provide a detailed brief on how a creator should make the TikTok, including background, number of people, text size/position, and overall style."
        )
        return "\n".join(lines)

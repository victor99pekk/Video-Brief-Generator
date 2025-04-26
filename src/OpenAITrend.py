from openai import OpenAI

class OpenAITrendSummarizer:
    """
    Uses OpenAI's Chat API to generate natural language summaries and briefs 
    from detected video data (trends, scenes, objects, etc.).
    """
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
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

    # ─────────────────────────────────────────────────────────────
    # SCENE-BY-SCENE DESCRIPTOR (existing or previously added)
    # ─────────────────────────────────────────────────────────────
    def describe_video_scenes(self, shots: list[dict]) -> str:
        """
        Produce a natural‑language description of an entire video, scene‑by‑scene.
        Args:
            shots (list[dict]): The list produced by GoogleVideoAnalyzer, 
                                each scene has keys for labels/objects/etc.
        Returns:
            str: A textual narration that mentions every detail we received.
        """
        prompt = self._build_scene_prompt(shots)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a professional video‑description AI. "
                            "Given raw scene metadata (labels, objects, text, speech, etc.) "
                            "you produce a concise but exhaustive narrative so that someone "
                            "who has not seen the video can visualize each scene perfectly."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.4,
                max_tokens=800
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return "Error generating scene description."

    def _build_scene_prompt(self, shots: list[dict]) -> str:
        """
        Build a prompt that enumerates *every* detail for each scene.
        """
        lines = ["Below is structured metadata for each scene in a TikTok video.\n"
                 "For every scene, write 1–2 sentences that include ALL the details.\n"]
        for shot in shots:
            lines.append(f"Scene {shot.get('shot_number')} "
                         f"({shot.get('start_time', 0):.2f}s–{shot.get('end_time', 0):.2f}s):")

            def _join(key):
                items = shot.get(key, [])
                return ", ".join(items) if isinstance(items, list) else str(items)

            lines.append(f"  • Segment labels: {_join('segment_labels')}")
            lines.append(f"  • Shot labels: {_join('shot_labels')}")
            lines.append(f"  • Frame labels: {_join('frame_labels')}")

            obj_descs = [o['object_description'] for o in shot.get('objects', [])]
            lines.append(f"  • Objects: {', '.join(obj_descs) if obj_descs else 'none'}")

            text_descs = [t['text'] for t in shot.get('texts', [])]
            lines.append(f"  • On‑screen text: {', '.join(text_descs) if text_descs else 'none'}")

            logo_descs = [l['logo_description'] for l in shot.get('logos', [])]
            lines.append(f"  • Logos: {', '.join(logo_descs) if logo_descs else 'none'}")

            person_count = len(shot.get('persons', []))
            lines.append(f"  • Persons detected: {person_count if person_count else 'none'}")

            speech_words = [w['word'] for w in shot.get('speech_transcriptions', [])]
            lines.append(f"  • Speech words: {', '.join(speech_words) if speech_words else 'none'}")

            explicit_frames = shot.get("explicit_frames", [])
            if explicit_frames:
                likelihoods = {f['pornography_likelihood'] for f in explicit_frames}
                lines.append(f"  • Explicit-content likelihoods: {', '.join(likelihoods)}")
            else:
                lines.append("  • Explicit-content likelihoods: none")

            lines.append("")  # blank line

        lines.append(
            "Using the information above, write a cohesive scene‑by‑scene description. "
            "Do not omit any detail, but keep each scene to one or two sentences."
        )
        return "\n".join(lines)

    # ─────────────────────────────────────────────────────────────────
    # NEW: MULTI-VIDEO (PER-SONG) TRENDS + EXPLANATION
    # ─────────────────────────────────────────────────────────────────
    def generate_song_trends_explanation(self, all_video_features: list[dict]) -> str:
        """
        Given a list of video features (labels, objects, etc.) for a single song,
        produce a step-by-step explanation of recurring patterns and environment 
        selection. Return an extended textual explanation plus a production brief.
        
        all_video_features: [
          {
            'video_uri': 'gs://...',
            'labels': [...],
            'objects': [...],
            'texts': [...],
            ...
          },
          ...
        ]
        """
        prompt = self._build_song_trends_prompt(all_video_features)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are a marketing strategist AI specialized in analyzing multiple videos "
                            "of the same song on TikTok. You're given structured video features and must "
                            "explain how you identify the trending elements, the environment, text usage, "
                            "objects, etc. Then you must provide a step-by-step rationale and a final "
                            "proposal for how to produce an ideal TikTok for this particular song."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.5,
                max_tokens=1000
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return "Error generating song-level trends explanation."

    def _build_song_trends_prompt(self, all_video_features: list[dict]) -> str:
        """
        Construct a prompt describing all videos for a single song, listing 
        the features so the AI can detect recurring patterns, explain them, 
        and produce a final recommended video concept.
        """
        lines = ["Below is a set of analyzed features for multiple TikTok videos related to one song.\n"]
        for i, vid_data in enumerate(all_video_features, start=1):
            lines.append(f"Video #{i}: {vid_data.get('video_uri', '(unknown)')}")
            lines.append(f"  - Labels: {', '.join(vid_data.get('labels', []))}")
            lines.append(f"  - Objects: {', '.join(vid_data.get('objects', []))}")
            lines.append(f"  - Text segments: {', '.join(vid_data.get('texts', []))}")
            # You can expand if you have more categories like "logos" or "speech"
            lines.append("")
        lines.append(
            "Please analyze these videos to find recurring patterns (e.g. environment, objects, text usage, camera style). "
            "Explain step by step how you decide on the best environment, text style, number of cuts, etc. Finally, "
            "provide a comprehensive creative brief for how a new creator should produce an ideal TikTok for this song, "
            "incorporating all discovered trends."
        )
        return "\n".join(lines)

    # ─────────────────────────────────────────────────────────────────────
    # NEW: MULTI-SONG AGGREGATED TRENDS
    # ─────────────────────────────────────────────────────────────────────
    def generate_overall_trends_and_brief(self, song_trends_list: list[str]) -> str:
        """
        Takes a list of textual trend summaries (one per song) and synthesizes them 
        into a final, extremely detailed production brief that spans all similar songs.
        
        For example, if there are 3 songs, each has a big explanation from 
        `generate_song_trends_explanation()`. We pass those into this method 
        to find the bigger cross-song patterns and produce a final mega-brief.
        """
        prompt = self._build_overall_trends_prompt(song_trends_list)
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an advanced creative AI who merges separate trend analyses "
                            "across multiple songs into a single, cohesive strategy. Provide a "
                            "unified step-by-step explanation for how you found cross-song patterns "
                            "and then deliver a final, extremely detailed video production brief "
                            "covering environment, objects, text, length, transitions, lighting, etc."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.6,
                max_tokens=1500
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"OpenAI API error: {e}")
            return "Error generating overall trends and final brief."

    def _build_overall_trends_prompt(self, song_trends_list: list[str]) -> str:
        """
        Construct a prompt that merges multiple song-level trend explanations.
        """
        lines = ["We have multiple songs, each with its own trend analysis:\n"]
        for i, text in enumerate(song_trends_list, start=1):
            lines.append(f"Song {i} Trend Explanation:\n{text}\n---\n")
        lines.append(
            "Please synthesize the above analyses into a single, comprehensive discussion of cross-song trends.  "
            "Walk through the patterns step by step. Then provide one final, extremely detailed TikTok video brief "
            "that applies to all these songs, discussing everything from environment to text usage. It should be step by step, scene by scene, exactly all information. "
        )
        return "\n".join(lines)
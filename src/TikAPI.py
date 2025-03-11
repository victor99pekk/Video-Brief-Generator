# TikAPI.py

import requests
from difflib import SequenceMatcher
from tikapi import TikAPI, ValidationException, ResponseException



class TikAPIWrapper:
    def __init__(self, key:str):
        self.api_key = key
        self.api = TikAPI(self.api_key)

    def _similarity(self, a, b):
        """Helper method for fuzzy matching."""
        return SequenceMatcher(None, a.lower(), b.lower()).ratio()

    def search_music(self, user_title, user_artist, max_results=50, early_stop=True):
        """
        Searches TikTok for the user_title (in the 'general' category).
        Returns either:
          - [best_match_id] if an early-stop match is found,
          - OR up to max_results music IDs.
        """
        try:
            response = self.api.public.search(category="general", query=user_title)
            music_ids = set()
            best_match_id = None

            while response and len(music_ids) < max_results:
                data = response.json()

                # 'data' should be a list of search results
                if not isinstance(data.get("data"), list):
                    print("No valid data found in search response.")
                    break

                for entry in data["data"]:
                    item = entry.get("item", {})
                    music = item.get("music", {})

                    found_music_id = music.get("id")
                    found_title = music.get("title", "")
                    found_author = music.get("authorName", "")

                    if not found_music_id:
                        continue

                    music_ids.add(found_music_id)

                    # If early_stop=True, try an on-the-fly match
                    if early_stop:
                        if self._is_good_enough(user_title, user_artist, found_title, found_author):
                            best_match_id = found_music_id
                            print(f"[EARLY STOP] Found good enough match: {found_title} by {found_author}")
                            break  # out of for loop

                if best_match_id or len(music_ids) >= max_results:
                    break

                next_cursor = data.get('nextCursor')
                if next_cursor:
                    response = response.next_items()
                else:
                    break

            # Return either the single match or the whole set
            if best_match_id:
                return [best_match_id]
            return list(music_ids)

        except (ValidationException, ResponseException) as e:
            print(f"API Error searching music: {e}")
            return []

    def _is_good_enough(self, user_title, user_artist, found_title, found_author):
        """
        Check if the found title & author are 'good enough' to stop searching.
        Adjust logic as needed (exact, substring, similarity).
        """
        user_artist_lc = user_artist.strip().lower()
        found_author_lc = found_author.strip().lower()

        user_title_lc = user_title.strip().lower()
        found_title_lc = found_title.strip().lower()

        # 1) exact match on author
        if user_artist_lc != found_author_lc:
            return False

        # 2) substring check or fuzzy ratio for title
        if user_title_lc in found_title_lc or found_title_lc in user_title_lc:
            return True
        return False

    def find_matching_song(self, user_title, user_artist, music_ids, similarity_threshold=0.7):
        """
        If multiple IDs came back, check each one's 'title'/'author'
        by fetching some videos for that music ID.
        """
        for music_id in music_ids:
            videos = self.fetch_music_videos(music_id, limit=5)
            for video in videos:
                song = video.get("music", {})
                title = song.get("title", "")
                author = song.get("authorName", "")

                # If both the title & author are fairly similar to user inputs
                if (self._similarity(user_title, title) > similarity_threshold and
                    self._similarity(user_artist, author) > similarity_threshold):
                    print(f"Match found: {title} by {author}, Music ID: {music_id}")
                    return music_id

        print("No exact match found among multiple IDs.")
        return None

    def fetch_music_videos(self, music_id, limit=10):
        """
        Retrieves up to 'limit' videos that use the given music_id.
        """
        try:
            response = self.api.public.music(id=music_id, count=limit)
            if response.status_code == 200:
                return response.json().get("itemList", [])
            else:
                print(f"Music fetch error: HTTP {response.status_code}")
        except (ValidationException, ResponseException) as e:
            print(f"Error fetching videos for music {music_id}: {e}")
        return []

    def get_video_metadata(self, video_id):
        """
        Return the JSON for a single TikTok video, including
        the downloadAddr and headers needed to request it
        """
        try:
            response = self.api.public.video(id=video_id)
            print(response.json())
            return response.json()
        except (ValidationException, ResponseException) as e:
            print(f"Error fetching video {video_id} metadata: {e}")
        return {}

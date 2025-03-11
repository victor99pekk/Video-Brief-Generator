import pylast

class LastfmAPI:
    def __init__(self, API_KEY, API_SECRET):
        self.API_KEY = API_KEY
        self.API_SECRET = API_SECRET
        self.network = pylast.LastFMNetwork(api_key=API_KEY, api_secret=API_SECRET)

    def get_similar_tracks(self, song, artist, limit=5) -> tuple[str, str]:
        """Returns similar tracks based on Last.fm recommendations."""
        track = self.network.get_track(artist, song)
        similar_tracks = track.get_similar(limit=limit)
        return [(t.item.title, t.item.artist.name) for t in similar_tracks]

    def get_top_tracks(self, artist_name, limit=5):
        """Returns the top tracks of a given artist."""
        artist = self.network.get_artist(artist_name)
        top_tracks = artist.get_top_tracks(limit=limit)
        return [(track.item.title, track.weight) for track in top_tracks]


    def get_album_info(self, artist, album):
        """Returns information about an album (listeners, play count, release date)."""
        album_obj = self.network.get_album(artist, album)
        return {
            "Title": album_obj.get_title(),
            "Listeners": album_obj.get_listener_count(),
            "Play Count": album_obj.get_playcount(),
            "Release Date": album_obj.get_wiki_published_date() or "Unknown"
        }

    def get_global_trending_tracks(self, limit=5):
        """Returns the top trending tracks globally on Last.fm."""
        trending_tracks = self.network.get_top_tracks(limit=limit)
        return [(track.item.title, track.item.artist.name) for track in trending_tracks]

    def get_track_tags(self, song, artist, limit=5):
        """Returns the top tags (genres) for a track."""
        track = self.network.get_track(artist, song)
        tags = track.get_top_tags(limit=limit)
        return [tag.item.name for tag in tags]

# Example Usage
if __name__ == "__main__":
    lastfm = LastfmAPI(API_KEY, API_SECRET)

    # Get similar tracks
    similar_tracks = lastfm.get_similar_tracks("Billie Jean", "Michael Jackson")
    print("Similar Tracks:", similar_tracks)

    # Get top tracks of an artist
    top_tracks = lastfm.get_top_tracks("The Weeknd")
    print("Top Tracks:", top_tracks)

    # Get album info
    album_info = lastfm.get_album_info("The Weeknd", "After Hours")
    print("Album Info:", album_info)

    # Get global trending tracks
    trending_tracks = lastfm.get_global_trending_tracks()
    print("Trending Tracks:", trending_tracks)

    # Get track tags (genres)
    track_tags = lastfm.get_track_tags("Blinding Lights", "The Weeknd")
    print("Track Tags:", track_tags)

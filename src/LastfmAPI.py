import pylast

class LastfmAPI:
    """
    A wrapper class for the Last.fm API that provides methods to access music data, 
    including similar tracks, artist information, and trending music.
    
    This class handles authentication with the Last.fm API and provides convenient
    methods for retrieving music recommendations and metadata.
    
    Attributes:
        API_KEY (str): The Last.fm API key used for authentication
        API_SECRET (str): The Last.fm API secret used for authentication
        network (pylast.LastFMNetwork): The authenticated Last.fm network instance
    """
    def __init__(self, API_KEY, API_SECRET):
        """
        Initialize the Last.fm API wrapper with the provided credentials.
        
        Args:
            API_KEY (str): Your Last.fm API key obtained from Last.fm developer dashboard
            API_SECRET (str): Your Last.fm API secret obtained from Last.fm developer dashboard
            
        Raises:
            pylast.WSError: If authentication fails due to invalid credentials
            pylast.NetworkError: If there's a network issue connecting to Last.fm
        """
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


## test the LastfmAPI class and the ability to get similar tracks
# API_KEY="adf237358ef04d1a07dd2727292dc2f8"
# API_SECRET="d00bd51f14e57c7f6c4016f40c5981f0"
# api = LastfmAPI(API_KEY, API_SECRET)
# similar_tracks = api.get_similar_tracks("sweethearts", "håkan hellström")
# print(similar_tracks)
from flask import Flask, request, jsonify
import sys
import os

# Add the parent directory to the path so we can import from src
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Import from the src directory
from src import load_config_and_initialize, ViralMusicFinder

app = Flask(__name__)

# Initialize your ViralMusicFinder once when the app starts
try:
    music_finder = load_config_and_initialize()
    print("ViralMusicFinder initialized successfully")
except Exception as e:
    print(f"Error initializing ViralMusicFinder: {e}")
    music_finder = None

def generate_brief(song_data) -> str:
    """Generate a brief for the given song data"""
    try:
        # Extract song and artist from the request
        song = song_data.get("song")
        artist = song_data.get("artist")
        
        if not song or not artist:
            return "Please provide both song and artist"
        
        # Use your ViralMusicFinder to process the song
        # trends, summary = music_finder.find_tiktoks(song=song, artist=artist)
        summary = music_finder.find_tiktoks(song=song, artist=artist)

        # Return the summary or a default message
        return summary if summary else "Could not generate a brief for this song"
    
    except Exception as e:
        print(f"Error generating brief: {e}")
        return f"Error generating brief: {str(e)}"
    
@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/get-brief', methods=['POST'])
def get_brief():
    """API endpoint to get a brief for a song"""
    print("Received request")
    try:
        # Get the request data
        data = request.get_json()
        
        if not data:
            return jsonify({"error": "No data provided"}), 400
            
        # Generate the brief
        brief = generate_brief(data)
        
        # Return the result
        print(f"Brief generated: {brief}")
        return jsonify({"brief": brief})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint"""
    import datetime
    print("Health check requested")
    
    health_data = {
        "status": "ok" if music_finder is not None else "degraded",
        "timestamp": datetime.datetime.now().isoformat(),
        "server": "flask",
        "music_finder_available": music_finder.LLM_key
    }
    
    return jsonify(health_data)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=True, host='0.0.0.0', port=port)
from flask import Flask, request, jsonify
import sys
import os

# Add the parent directory to the path so we can import from src
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

# Import from the src directory
from src import *

app = Flask(__name__)

# Initialize your ViralMusicFinder once when the app starts
try:
    music_finder = load_config_and_initialize()
    print("ViralMusicFinder initialized successfully")
except Exception as e:
    print(f"Error initializing ViralMusicFinder: {e}")
    music_finder = None

def pretty_print(text: str) -> str:
    # Replace escaped newlines with actual newlines
    formatted_text = text.replace("\\n", "\n")

    # Add extra newlines before headers that match the pattern for summaries
    import re
    formatted_text = re.sub(r"(=== Summary for.*?)===", r"\n\n\1===", formatted_text)

    # Optional: Add an extra newline after paragraphs for better readability
    paragraphs = formatted_text.split("\n\n")

    # Reconstruct nicely formatted string
    result = "\n\n".join(paragraph.strip() for paragraph in paragraphs)
    return result

def generate_brief(song_data) -> str:
    """Generate a brief for the given song data as a nicely formatted string."""
    try:
        # Extract song and artist from the request data
        song = song_data.get("song")
        artist = song_data.get("artist")
        
        if not song or not artist:
            return "Please provide both song and artist"
        
        # Use your ViralMusicFinder to process the song
        result = music_finder.find_tiktoks(song=song, artist=artist)
        
        # If the function returns a tuple, assume the second element is the summary.
        # Otherwise, assume the result is the summary.
        if isinstance(result, tuple):
            _, summary = result
        else:
            summary = result
        
        # If the summary is a list of strings, join them with newline characters.
        if isinstance(summary, list):
            formatted_summary = "\n".join(summary)
            formatted_summary = pretty_print(formatted_summary)
        else:
            formatted_summary = summary
        
        return formatted_summary if formatted_summary else "Could not generate a brief for this song"
    
    except Exception as e:
        print(f"Error generating brief: {e}")
        return f"Error generating brief: {str(e)}"

@app.route('/get-brief', methods=['POST', 'GET'])
def get_brief_endpoint():
    """API endpoint to get a brief for a song.
    Returns a JSON object with a nicely formatted brief string.
    """
    print("Received request")
    try:
        if request.method == 'GET':
            # Extract parameters from the query string for a GET request
            song = request.args.get('song')
            artist = request.args.get('artist')
            if not song or not artist:
                return jsonify({"error": "Please provide both song and artist as query parameters"}), 400
            data = {"song": song, "artist": artist}
        else:
            # For POST requests, extract JSON data
            data = request.get_json()
            if not data:
                return jsonify({"error": "No data provided"}), 400
        
        # Generate the brief as a nicely formatted string
        brief = generate_brief(data)
        print(f"Brief generated:\n{brief}")
        
        # Return the result in JSON with the nicely formatted string
        return jsonify({"brief": brief})
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Simple health check endpoint."""
    print("health")
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(debug=True, host='0.0.0.0', port=port)

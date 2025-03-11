import requests

# Replace with your actual TasteDive API key
API_KEY = "1046389-musicfin-80D11344"

def get_similar_songs(song_name:str):
    base_url = "https://tastedive.com/api/similar"
    params = {
        "q": f"music:{song_name}",
        "type": "music",
        "info": 1,  # Get additional information like descriptions and links
        "limit": 5,  # Number of recommendations
        "k": API_KEY
    }
    
    response = requests.get(base_url, params=params)

    if response.status_code == 200:
        data = response.json()
        results = data.get("Similar", {}).get("Results", [])
        
        if results:
            print(f"Songs similar to '{song_name}':\n")
            for idx, song in enumerate(results, 1):
                name = song.get("Name", "Unknown")
                wTeaser = song.get("wTeaser", "No description available.")
                print(f"{idx}. {name}")
                print(f"   Description: {wTeaser}\n")
        else:
            print("No similar songs found.")
    else:
        print(f"Error: {response.status_code}")

# Example usage
song = "Hotel California"
get_similar_songs(song)

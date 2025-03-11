import requests
import os
from google.cloud import storage
from google.oauth2 import service_account

class GCSVideoUploader:
    def __init__(self, GoogleJson_file=None, bucket_name=None):
        """
        Initialize the Google Cloud Storage video uploader.
        
        Args:
            GoogleJson_file: Path to the service account JSON file
            bucket_name: GCS bucket name
            project_id: Google Cloud project ID
        """
        # Handle authentication
            # Use explicit credentials file if it exists
        try:
            credentials = service_account.Credentials.from_service_account_file(GoogleJson_file)
            self.storage_client = storage.Client(credentials=credentials)
        except Exception as e:
            print(f"Error authenticating with Google Cloud: {e}")
            print("Please ensure GOOGLE_APPLICATION_CREDENTIALS is set or provide a valid credentials file.")
            raise
    
        self.bucket_name = bucket_name
        self.bucket = self.storage_client.bucket(self.bucket_name)
        print(f"Successfully connected to bucket: {bucket_name}")

    def upload_tiktok_video_direct(self, video_json, blob_name=None):
        try:
            video_info = video_json.get('itemInfo', {}).get('itemStruct', {}).get('video', {})
            video_url = video_info.get('downloadAddr')
            video_headers = video_json.get('$other', {}).get('videoLinkHeaders', {})

            if not blob_name:
                video_id = video_json.get('itemInfo', {}).get('itemStruct', {}).get('id', 'unknown_video')
                blob_name = f"tikapi_videos/{video_id}.mp4"

            if not video_url:
                print("No downloadAddr found in video JSON")
                return None

            resp = requests.get(video_url, headers=video_headers, stream=True)
            resp.raise_for_status()

            blob = self.bucket.blob(blob_name)
            blob.upload_from_string(resp.content, content_type='video/mp4')

            gcs_url = f"gs://{self.bucket.name}/{blob_name}"
            print(f"Video uploaded to {gcs_url}")
            return gcs_url

        except requests.exceptions.RequestException as re:
            print(f"Error downloading video content: {re}")
        except Exception as ex:
            print(f"Error uploading video: {ex}")

        return None
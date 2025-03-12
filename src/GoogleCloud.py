import requests
from google.cloud import storage
from google.oauth2 import service_account

class GCSVideoUploader:
    """
    A class for uploading videos to Google Cloud Storage, with specialized
    methods for TikTok video content.
    
    This class handles authentication with Google Cloud Storage using service account
    credentials, and provides methods to upload video content directly from TikTok API
    responses to a specified Google Cloud Storage bucket.
    
    Attributes:
        storage_client (google.cloud.storage.Client): The authenticated Google Cloud Storage client
        bucket_name (str): Name of the Google Cloud Storage bucket for uploads
        bucket (google.cloud.storage.Bucket): The bucket object for performing operations
    """
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
        """
    Download a TikTok video from the API response and upload it directly to Google Cloud Storage.
    
    This method extracts the video download URL and authentication headers from the TikTok API
    response, downloads the video content, and uploads it to the specified Google Cloud Storage bucket.
    
    Args:
        video_json (dict): The JSON response from TikTok API containing video information,
                          including download URL and authentication headers.
        blob_name (str, optional): Custom name for the uploaded file in GCS.
                                  If not provided, a name will be generated from the video ID.
    
    Returns:
        str or None: The Google Cloud Storage URI of the uploaded video (gs://bucket/path/to/video.mp4)
                     or None if the upload fails.
    
    Raises:
        requests.exceptions.RequestException: If there's an error downloading the video content
        google.cloud.exceptions.GoogleCloudError: If there's an error uploading to Google Cloud Storage
    """
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
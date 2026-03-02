import os
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def get_youtube_client():
    """
    Initializes and returns a YouTube Data API v3 client.

    Returns:
        googleapiclient.discovery.Resource: The authenticated YouTube API client.
        str: Error message if initialization fails, None otherwise.
    """
    api_key = os.getenv("YOUTUBE_API_KEY")

    if not api_key:
        return None, "Error: YOUTUBE_API_KEY not found in .env file."

    try:
        youtube = build("youtube", "v3", developerKey=api_key)
        return youtube, None
    except HttpError as e:
        return None, f"An HTTP error occurred: {e.resp.status} {e.content}"
    except Exception as e:
        return None, f"An unexpected error occurred: {str(e)}"

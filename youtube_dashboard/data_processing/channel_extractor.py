import pandas as pd
import streamlit as st
from googleapiclient.errors import HttpError

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_channel_data(_youtube, channel_id):
    """
    Fetches channel details from YouTube Data API.
    Cached for 1 hour to prevent API quota overuse.
    
    Args:
        _youtube: Authenticated YouTube API client (hashed by pointer).
        channel_id (str): The ID of the YouTube channel.

    Returns:
        pd.DataFrame or None: DataFrame containing channel data.
    """
    try:
        request = _youtube.channels().list(
            part="snippet,contentDetails,statistics",
            id=channel_id
        )
        response = request.execute()

        if not response.get("items"):
            return None

        item = response["items"][0]
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})
        
        # Robust thumbnail extraction
        thumbnails = snippet.get("thumbnails", {})
        thumbnail_url = (
            thumbnails.get("high", {}).get("url") or
            thumbnails.get("medium", {}).get("url") or
            thumbnails.get("default", {}).get("url") or
            "" 
        )

        data = {
            "Channel_ID": channel_id,
            "Channel_Name": snippet.get("title", "Unknown"),
            "Description": snippet.get("description", ""),
            "Subscriber_Count": int(statistics.get("subscriberCount", 0)),
            "Total_Views": int(statistics.get("viewCount", 0)),
            "Total_Videos": int(statistics.get("videoCount", 0)),
            "Created_At": snippet.get("publishedAt", ""),
            "Thumbnail_URL": thumbnail_url,
            "Uploads_Playlist_ID": item.get("contentDetails", {}).get("relatedPlaylists", {}).get("uploads", "")
        }

        return pd.DataFrame([data])

    except HttpError as e:
        # Let the main app handle specific API errors (403, 404)
        raise e
    except Exception as e:
        print(f"An unexpected error occurred in fetch_channel_data: {str(e)}")
        return None

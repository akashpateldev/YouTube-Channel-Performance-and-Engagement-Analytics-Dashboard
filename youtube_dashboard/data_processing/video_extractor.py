import pandas as pd
import streamlit as st
from googleapiclient.errors import HttpError

@st.cache_data(ttl=3600)
def get_uploads_playlist_id(_youtube, channel_id):
    """
    Fetches the uploads playlist ID for a given channel.
    """
    try:
        request = _youtube.channels().list(
            part="contentDetails",
            id=channel_id
        )
        response = request.execute()
        if not response.get("items"):
            return None
        return response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    except HttpError:
        raise
    except Exception as e:
        print(f"Error fetching playlist ID: {str(e)}")
        return None

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_video_ids_from_playlist(_youtube, playlist_id, max_videos=None):
    """
    Fetches all or limited video IDs from a playlist using pagination.
    
    Args:
        max_videos (int, optional): Maximum limit for videos to fetch.
    """
    video_ids = []
    next_page_token = None

    try:
        while True:
            request = _youtube.playlistItems().list(
                part="contentDetails",
                playlistId=playlist_id,
                maxResults=50,
                pageToken=next_page_token
            )
            response = request.execute()

            for item in response.get("items", []):
                video_ids.append(item["contentDetails"]["videoId"])
            
            # Stop if we hit the limit
            if max_videos and len(video_ids) >= max_videos:
                video_ids = video_ids[:max_videos]
                break

            next_page_token = response.get("nextPageToken")
            if not next_page_token:
                break
                
    except HttpError:
        raise # Let parent handle it
    
    return video_ids

@st.cache_data(ttl=3600, show_spinner=False)
def fetch_video_details(_youtube, video_ids):
    """
    Fetches detailed metadata for a list of video IDs in batches.
    NOTE: Progress bar handling is done in the app via chunking, 
    but this function processes the specific chunk given to it.
    
    Actually, to support caching properly, we should cache the BATCH logic.
    For the progress bar to work effectively with Streamlit's cache, 
    we need to cache specific big calls or manage it carefully.
    
    Here we will cache the entire result of this function call.
    """
    video_data = []
    
    # Process in batches of 50
    for i in range(0, len(video_ids), 50):
        batch_ids = video_ids[i:i+50]
        try:
            request = _youtube.videos().list(
                part="snippet,statistics,contentDetails",
                id=",".join(batch_ids)
            )
            response = request.execute()

            for item in response.get("items", []):
                snippet = item.get("snippet", {})
                statistics = item.get("statistics", {})
                content_details = item.get("contentDetails", {})
                
                thumbnails = snippet.get("thumbnails", {})
                thumbnail_url = (
                    thumbnails.get("high", {}).get("url") or
                    thumbnails.get("medium", {}).get("url") or
                    thumbnails.get("default", {}).get("url") or
                    ""
                )

                video_data.append({
                    "Video_ID": item["id"],
                    "Title": snippet.get("title", "Unknown"),
                    "Description": snippet.get("description", ""),
                    "Publish_Date": snippet.get("publishedAt", ""),
                    "Duration": content_details.get("duration", ""),
                    "View_Count": int(statistics.get("viewCount", 0)),
                    "Like_Count": int(statistics.get("likeCount", 0)),
                    "Comment_Count": int(statistics.get("commentCount", 0)),
                    "Thumbnail_URL": thumbnail_url
                })
        except HttpError:
            continue # Skip bad batches but try to return what we have

    df = pd.DataFrame(video_data)
    
    # Ensure numeric types
    if not df.empty:
        df["View_Count"] = pd.to_numeric(df["View_Count"], errors='coerce').fillna(0).astype('int64')
        df["Like_Count"] = pd.to_numeric(df["Like_Count"], errors='coerce').fillna(0).astype('int64')
        df["Comment_Count"] = pd.to_numeric(df["Comment_Count"], errors='coerce').fillna(0).astype('int64')
        df["Publish_Date"] = pd.to_datetime(df["Publish_Date"])

    return df

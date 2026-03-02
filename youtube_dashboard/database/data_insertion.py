import pandas as pd
from datetime import datetime
from sqlalchemy.orm import Session
from database.models import Channel, Video, VideoStatistics
from database.db_connection import SessionLocal

def channel_exists(db: Session, channel_id: str) -> bool:
    """Checks if a channel exists in the database."""
    return db.query(Channel).filter(Channel.channel_id == channel_id).first() is not None

def insert_or_update_channel(db: Session, channel_data: dict):
    """
    Inserts a new channel or updates an existing one (UPSERT).
    channel_data should be a dictionary corresponding to Channel model fields.
    """
    channel = db.query(Channel).filter(Channel.channel_id == channel_data['channel_id']).first()
    
    # Convert created_at to datetime if it's a string
    if isinstance(channel_data.get('created_at'), str) and channel_data['created_at']:
        try:
            channel_data['created_at'] = pd.to_datetime(channel_data['created_at']).to_pydatetime()
        except:
            pass

    if channel:
        for key, value in channel_data.items():
            setattr(channel, key, value)
    else:
        channel = Channel(**channel_data)
        db.add(channel)
    
    db.commit()
    db.refresh(channel)
    return channel

def insert_video(db: Session, video_data: dict):
    """
    Inserts a new video or updates an existing one.
    """
    video = db.query(Video).filter(Video.video_id == video_data['video_id']).first()
    
    # Convert publish_date to datetime if it's a string
    if isinstance(video_data.get('publish_date'), str) and video_data['publish_date']:
        try:
            video_data['publish_date'] = pd.to_datetime(video_data['publish_date']).to_pydatetime()
        except:
            pass

    if video:
        for key, value in video_data.items():
            setattr(video, key, value)
    else:
        video = Video(**video_data)
        db.add(video)
    
    db.commit()
    db.refresh(video)
    return video

def insert_video_statistics(db: Session, stats_data: dict):
    """
    Inserts a new statistics record for a video.
    """
    # Statistics are historical, so we usually just insert a new record with a timestamp
    if 'captured_at' not in stats_data or not stats_data['captured_at']:
        stats_data['captured_at'] = datetime.now()
    
    stats = VideoStatistics(**stats_data)
    db.add(stats)
    db.commit()
    return stats

def store_channel_data(channel_df: pd.DataFrame, video_df: pd.DataFrame):
    """
    Orchestrator function to store channel and video data into the database.
    """
    db = SessionLocal()
    try:
        # 1. Store Channel Data
        if not channel_df.empty:
            c_row = channel_df.iloc[0]
            channel_data = {
                "channel_id": c_row["Channel_ID"] if "Channel_ID" in c_row else channel_df.index[0], # Assuming index might be ID if column missing
                "channel_name": c_row["Channel_Name"],
                "description": c_row["Description"],
                "subscriber_count": int(c_row["Subscriber_Count"]),
                "total_views": int(c_row["Total_Views"]),
                "total_videos": int(c_row["Total_Videos"]),
                "created_at": c_row["Created_At"],
                "thumbnail_url": c_row["Thumbnail_URL"],
                "uploads_playlist_id": c_row["Uploads_Playlist_ID"]
            }
            # Note: The fetch_channel_data might not have 'Channel_ID' if it was passed as arg.
            # I'll check channel_extractor.py later to be sure.
            
            insert_or_update_channel(db, channel_data)
            
            # 2. Store Video and Stats Data
            if not video_df.empty:
                for _, v_row in video_df.iterrows():
                    video_data = {
                        "video_id": v_row["Video_ID"],
                        "channel_id": channel_data["channel_id"],
                        "title": v_row["Title"],
                        "description": v_row["Description"],
                        "publish_date": v_row["Publish_Date"],
                        "duration": v_row["Duration"],
                        "duration_mins": v_row.get("Duration_Mins", 0),
                        "thumbnail_url": v_row["Thumbnail_URL"]
                    }
                    insert_video(db, video_data)
                    
                    stats_data = {
                        "video_id": v_row["Video_ID"],
                        "view_count": int(v_row["View_Count"]),
                        "like_count": int(v_row["Like_Count"]),
                        "comment_count": int(v_row["Comment_Count"]),
                        "engagement_rate": float(v_row.get("Engagement_Rate", 0.0))
                    }
                    insert_video_statistics(db, stats_data)
                    
        return True
    except Exception as e:
        print(f"Error storing data: {e}")
        db.rollback()
        return False
    finally:
        db.close()

import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session
from database.db_connection import SessionLocal
from database.models import Channel, Video, VideoStatistics

def get_top_10_videos(channel_id: str = None):
    """Returns top 10 most viewed videos."""
    db = SessionLocal()
    try:
        query = db.query(
            Video.title,
            Video.publish_date,
            func.max(VideoStatistics.view_count).label('View_Count'),
            func.max(VideoStatistics.like_count).label('Like_Count'),
            func.max(VideoStatistics.comment_count).label('Comment_Count'),
            VideoStatistics.engagement_rate
        ).join(VideoStatistics, Video.video_id == VideoStatistics.video_id)
        
        if channel_id:
            query = query.filter(Video.channel_id == channel_id)
        
        query = query.group_by(Video.video_id).order_by(func.max(VideoStatistics.view_count).desc()).limit(10)
        
        return pd.read_sql(query.statement, db.bind)
    finally:
        db.close()

def get_engagement_over_time(channel_id: str):
    """Returns views, likes, and comments over time for multi-line charts."""
    db = SessionLocal()
    try:
        query = db.query(
            Video.publish_date,
            VideoStatistics.view_count,
            VideoStatistics.like_count,
            VideoStatistics.comment_count
        ).join(VideoStatistics, Video.video_id == VideoStatistics.video_id)
        
        if channel_id:
            query = query.filter(Video.channel_id == channel_id)
        
        return pd.read_sql(query.statement, db.bind)
    finally:
        db.close()

def get_view_distribution(channel_id: str):
    """Returns view counts for histogram analysis."""
    db = SessionLocal()
    try:
        query = db.query(VideoStatistics.view_count).join(Video, Video.video_id == VideoStatistics.video_id)
        if channel_id:
            query = query.filter(Video.channel_id == channel_id)
        return pd.read_sql(query.statement, db.bind)
    finally:
        db.close()

def load_channel_from_db(channel_id: str):
    """Loads channel info and all its video data from the database."""
    db = SessionLocal()
    try:
        channel = db.query(Channel).filter(Channel.channel_id == channel_id).first()
        if not channel:
            return None, pd.DataFrame()
            
        # Reconstruct channel DataFrame
        channel_data = {
            "Channel_ID": [channel.channel_id],
            "Channel_Name": [channel.channel_name],
            "Description": [channel.description],
            "Subscriber_Count": [channel.subscriber_count],
            "Total_Views": [channel.total_views],
            "Total_Videos": [channel.total_videos],
            "Created_At": [channel.created_at],
            "Thumbnail_URL": [channel.thumbnail_url],
            "Uploads_Playlist_ID": [channel.uploads_playlist_id]
        }
        channel_df = pd.DataFrame(channel_data)
        
        # Load videos and latest stats
        # We group by video_id and take the max captured_at or just the latest stats entry
        subquery = db.query(
            VideoStatistics.video_id,
            func.max(VideoStatistics.id).label('latest_id')
        ).group_by(VideoStatistics.video_id).subquery()
        
        query = db.query(
            Video.video_id.label('Video_ID'),
            Video.title.label('Title'),
            Video.description.label('Description'),
            Video.publish_date.label('Publish_Date'),
            Video.duration.label('Duration'),
            Video.duration_mins.label('Duration_Mins'),
            Video.thumbnail_url.label('Thumbnail_URL'),
            VideoStatistics.view_count.label('View_Count'),
            VideoStatistics.like_count.label('Like_Count'),
            VideoStatistics.comment_count.label('Comment_Count'),
            VideoStatistics.engagement_rate.label('Engagement_Rate')
        ).join(Video, Video.video_id == VideoStatistics.video_id)\
         .join(subquery, VideoStatistics.id == subquery.c.latest_id)\
         .filter(Video.channel_id == channel_id)
         
        video_df = pd.read_sql(query.statement, db.bind)
        # Ensure datetimes are correct
        if not video_df.empty:
            video_df['Publish_Date'] = pd.to_datetime(video_df['Publish_Date'])
            
        return channel_df, video_df
    finally:
        db.close()

def get_avg_duration_per_channel():
    """Returns average video duration per channel."""
    db = SessionLocal()
    try:
        query = db.query(
            Channel.channel_name,
            func.avg(Video.duration_mins).label('avg_duration_mins')
        ).join(Video, Channel.channel_id == Video.channel_id).group_by(Channel.channel_id)
        
        return pd.read_sql(query.statement, db.bind)
    finally:
        db.close()

def get_monthly_upload_trends(channel_id: str = None):
    """Returns monthly upload trends."""
    db = SessionLocal()
    try:
        # SQLite specific date formatting
        month_str = func.strftime('%Y-%m', Video.publish_date)
        query = db.query(
            month_str.label('Month'),
            func.count(Video.video_id).label('Video_Count')
        )
        
        if channel_id:
            query = query.filter(Video.channel_id == channel_id)
            
        query = query.group_by('Month').order_by('Month')
        
        return pd.read_sql(query.statement, db.bind)
    finally:
        db.close()

def get_posting_frequency_analysis(channel_id: str = None):
    """Analyzes uploads by day of week."""
    db = SessionLocal()
    try:
        # 0=Sunday, 6=Saturday in SQLite strftime %w
        day_of_week = func.strftime('%w', Video.publish_date)
        query = db.query(
            day_of_week.label('day_index'),
            func.count(Video.video_id).label('video_count')
        )
        
        if channel_id:
            query = query.filter(Video.channel_id == channel_id)
            
        query = query.group_by('day_index').order_by('day_index')
        
        df = pd.read_sql(query.statement, db.bind)
        # Map day index to names
        day_map = {'0': 'Sunday', '1': 'Monday', '2': 'Tuesday', '3': 'Wednesday', 
                   '4': 'Thursday', '5': 'Friday', '6': 'Saturday'}
        df['day_name'] = df['day_index'].map(day_map)
        return df
    finally:
        db.close()

def get_recently_analyzed_channels():
    """Returns a list of channels recently stored in the database."""
    db = SessionLocal()
    try:
        query = db.query(Channel).order_by(Channel.channel_name)
        return pd.read_sql(query.statement, db.bind)
    finally:
        db.close()

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Channel(Base):
    __tablename__ = 'channels'
    
    channel_id = Column(String(255), primary_key=True)
    channel_name = Column(String(255), nullable=False)
    description = Column(Text)
    subscriber_count = Column(Integer, default=0)
    total_views = Column(Integer, default=0)
    total_videos = Column(Integer, default=0)
    created_at = Column(DateTime)
    thumbnail_url = Column(String(500))
    uploads_playlist_id = Column(String(255))
    
    videos = relationship("Video", back_populates="channel", cascade="all, delete-orphan")

class Video(Base):
    __tablename__ = 'videos'
    
    video_id = Column(String(255), primary_key=True)
    channel_id = Column(String(255), ForeignKey('channels.channel_id'), nullable=False)
    title = Column(String(500), nullable=False)
    description = Column(Text)
    publish_date = Column(DateTime)
    duration = Column(String(50))  # Raw ISO 8601 duration
    duration_mins = Column(Float)  # Parsed duration
    thumbnail_url = Column(String(500))
    
    channel = relationship("Channel", back_populates="videos")
    statistics = relationship("VideoStatistics", back_populates="video", cascade="all, delete-orphan")

class VideoStatistics(Base):
    __tablename__ = 'video_statistics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    video_id = Column(String(255), ForeignKey('videos.video_id'), nullable=False)
    view_count = Column(Integer, default=0)
    like_count = Column(Integer, default=0)
    comment_count = Column(Integer, default=0)
    engagement_rate = Column(Float, default=0.0)
    captured_at = Column(DateTime, default=None) # Timestamp of when stats were fetched
    
    video = relationship("Video", back_populates="statistics")

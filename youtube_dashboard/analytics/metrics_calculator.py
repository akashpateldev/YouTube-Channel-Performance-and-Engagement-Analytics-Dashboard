import pandas as pd
import numpy as np

# Task 10: Data Transformation and Metrics Calculation

# Step 2: Engagement Rate Calculation
def calculate_engagement_rate(df):
    """
    Formula: ((Likes + Comments) / Views) * 100
    """
    if 'View_Count' in df.columns and 'Like_Count' in df.columns and 'Comment_Count' in df.columns:
        df['Engagement_Rate'] = df.apply(
            lambda x: ((x['Like_Count'] + x['Comment_Count']) / x['View_Count']) * 100 if x['View_Count'] > 0 else 0,
            axis=1
        )
    return df

# Step 3: Average Views per Video
def calculate_average_views(df):
    """Calculates average views per video."""
    if df.empty:
        return 0
    return df['View_Count'].mean()

# Step 4: Subscriber to view ratio
def calculate_subscriber_view_ratio(subscribers, total_views):
    """
    Formula: Total Views / total subscribers
    """
    if subscribers == 0:
        return 0.0
    return total_views / subscribers

# Step 5: Content Performance Score
def calculate_content_score(df):
    """
    Computes a composite score for video performance.
    Weights: Views (40%), Likes (30%), Engagement (30%)
    """
    if df.empty:
        return df
        
    # Normalized weights
    v_weight, l_weight, e_weight = 0.4, 0.3, 0.3
    
    # Use log scaling for views/likes to handle outliers
    views_norm = np.log1p(df['View_Count'])
    likes_norm = np.log1p(df['Like_Count'])
    eng_norm = df['Engagement_Rate'] / 10  # Scale engagement for parity
    
    df['Performance_Score'] = (views_norm * v_weight) + (likes_norm * l_weight) + (eng_norm * e_weight)
    return df

# Step 7: Optimal posting time
def get_optimal_posting_time(df):
    """Analyzes publish hour to find which gives highest average views."""
    if df.empty:
        return None, None
    
    temp_df = df.copy()
    temp_df['Hour'] = temp_df['Publish_Date'].dt.hour
    temp_df['Day'] = temp_df['Publish_Date'].dt.day_name()
    
    # Best hour based on avg views
    best_hour = temp_df.groupby('Hour')['View_Count'].mean().idxmax()
    # Best day based on avg views
    best_day = temp_df.groupby('Day')['View_Count'].mean().idxmax()
    
    return best_day, best_hour

# Step 8: Trend Analysis
def perform_trend_analysis(df, period='monthly'):
    """Analyzes trends (daily, weekly, monthly)."""
    if df.empty:
        return pd.DataFrame()
        
    temp_df = df.copy()
    temp_df.set_index('Publish_Date', inplace=True)
    
    if period == 'daily':
        return temp_df.resample('D')['View_Count'].sum().reset_index()
    elif period == 'weekly':
        return temp_df.resample('W')['View_Count'].sum().reset_index()
    else: # monthly
        return temp_df.resample('M')['View_Count'].sum().reset_index()

# Step 9: Performance Benchmark
def benchmark_videos(df):
    """Compare each video to channel average views."""
    if df.empty:
        return df
        
    avg_views = df['View_Count'].mean()
    df['View_Benchmark'] = (df['View_Count'] / avg_views) * 100 if avg_views > 0 else 0
    
    return df

# Step 10: Prepare data for visualization (utility)
def prepare_viz_data(df):
    """Ensures data types are correct for Plotly."""
    if not df.empty:
        df['Publish_Date'] = pd.to_datetime(df['Publish_Date'])
        df = calculate_engagement_rate(df)
        df = calculate_content_score(df)
        df = benchmark_videos(df)
    return df

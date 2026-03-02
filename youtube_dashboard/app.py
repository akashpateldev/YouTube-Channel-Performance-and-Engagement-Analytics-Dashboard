import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
import numpy as np
from datetime import datetime, timedelta
from googleapiclient.errors import HttpError

from data_processing.youtube_client import get_youtube_client
from data_processing.channel_extractor import fetch_channel_data
from data_processing.video_extractor import get_uploads_playlist_id, fetch_video_ids_from_playlist, fetch_video_details
from database.db_connection import init_db
from database.data_insertion import store_channel_data
from analytics.analytics_queries import (
    get_recently_analyzed_channels, 
    get_top_10_videos, 
    load_channel_from_db,
    get_engagement_over_time,
    get_view_distribution,
    get_monthly_upload_trends,
    get_posting_frequency_analysis
)
from analytics.metrics_calculator import (
    calculate_engagement_rate,
    calculate_content_score,
    get_optimal_posting_time,
    benchmark_videos,
    prepare_viz_data,
    calculate_subscriber_view_ratio,
    calculate_average_views,
    perform_trend_analysis
)

# --- Page Configuration ---
st.set_page_config(
    page_title="YouTube Analytics Dashboard",
    page_icon="🎬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Task 11 Step 1: Initialize Database ---
init_db()

# --- Utilities ---
# --- Utilities ---
def format_number(num):
    """Formats large numbers with K/M/B suffixes."""
    try:
        num = float(num)
    except (ValueError, TypeError):
        return "0"
        
    if num >= 1_000_000_000:
        return f"{num / 1_000_000_000:.1f}B"
    elif num >= 1_000_000:
        return f"{num / 1_000_000:.1f}M"
    elif num >= 1_000:
        return f"{num / 1_000:.1f}K"
    return f"{int(num)}"

# --- UI Theme (Task 11 Step 8) ---
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    
    div[data-testid="stMetric"] {
        background: rgba(255, 255, 255, 0.05);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 12px;
        padding: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    
    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
    }
    
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        border-radius: 8px 8px 0 0;
        background-color: rgba(255, 255, 255, 0.03);
        padding: 0 20px;
    }
</style>
""", unsafe_allow_html=True)

# --- Task 11 Step 2: Sidebar Navigation ---
with st.sidebar:
    st.header("Admin Panel")
    
    # New Analysis section
    with st.expander("🔍 Analyze New Channel", expanded=True):
        channel_id_input = st.text_input("Enter Channel ID", placeholder="UC...").strip()
        fetch_limit = st.slider("Max Videos to Fetch", 50, 1000, 200)
        
        if st.button("🚀 Process Channel", use_container_width=True, type="primary"):
            if channel_id_input:
                try:
                    youtube, error = get_youtube_client()
                    if error:
                        st.error(error)
                    else:
                        with st.status("Fetching Data...", expanded=True) as status:
                            c_data = fetch_channel_data(youtube, channel_id_input)
                            if c_data is not None:
                                uploads_id = c_data["Uploads_Playlist_ID"][0]
                                video_ids = fetch_video_ids_from_playlist(youtube, uploads_id, max_videos=fetch_limit)
                                if video_ids:
                                    prog = st.progress(0)
                                    df_batch = fetch_video_details(youtube, video_ids)
                                    prog.progress(1.0)
                                    
                                    # Data Transformation (Task 10 Step 11)
                                    df_batch = prepare_viz_data(df_batch)
                                    
                                    store_channel_data(c_data, df_batch)
                                    st.session_state.current_id = channel_id_input
                                    status.update(label="Complete!", state="complete")
                                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")
            else:
                st.warning("Please enter a valid ID.")

    st.markdown("---")
    
    # Available channels from DB
    st.subheader("📚 Saved Channels")
    recent_channels = get_recently_analyzed_channels()
    if not recent_channels.empty:
        # Channel Selection (Task 11 Step 1)
        channel_names = recent_channels['channel_name'].tolist()
        selected_name = st.selectbox("Switch Channel", ["Select..."] + channel_names)
        
        if selected_name != "Select...":
            row = recent_channels[recent_channels['channel_name'] == selected_name].iloc[0]
            st.session_state.current_id = row['channel_id']
            
        # Comparison (Task 11 Step 6)
        st.markdown("### ⚖️ Compare")
        comp_selection = st.multiselect("Select 2+ Channels", channel_names)
        if len(comp_selection) >= 2:
            st.session_state.comp_ids = [recent_channels[recent_channels['channel_name'] == n].iloc[0]['channel_id'] for n in comp_selection]
        else:
            st.session_state.comp_ids = []
    else:
        st.info("No channels analyzed yet.")

# --- Task 11 Step 4: Fetch Data ---
if 'current_id' in st.session_state and st.session_state.current_id:
    c_df, v_df = load_channel_from_db(st.session_state.current_id)
    
    if c_df is not None and not v_df.empty:
        # Ensure derived metrics exist (Fixes Performance_Score error)
        v_df = prepare_viz_data(v_df)
        
        c_row = c_df.iloc[0]
        
        # Dashboard Layout (Task 11 Step 8)
        col_img, col_info = st.columns([1, 5])
        with col_img:
            st.markdown(f'<img src="{c_row["Thumbnail_URL"]}" style="border-radius:50%; width:100%; border:2px solid #ff0000;" referrerpolicy="no-referrer">', unsafe_allow_html=True)
        with col_info:
            st.title(c_row["Channel_Name"])
            st.markdown(f"*{c_row['Description'][:300]}...*")

        st.markdown("---")
        
        # Tabs
        t_overview, t_deepdive, t_timing, t_compare = st.tabs([
            "📊 Dashboard", "🔥 Content Deep Dive", "🗓️ Timing & Trends", "⚖️ Comparison"
        ])

        with t_overview:
            # Task 11 Step 3: Date Range Filter
            d_col1, d_col2 = st.columns([2, 1])
            with d_col1:
                # Robust date range initialization
                min_date = v_df['Publish_Date'].min().date()
                max_date = v_df['Publish_Date'].max().date()
                date_range = st.date_input("Filter Content", value=[min_date, max_date], min_value=min_date, max_value=max_date)
            
            # Filter Logic (Handle partial selection)
            if isinstance(date_range, (list, tuple)) and len(date_range) == 2:
                start_dt = pd.to_datetime(date_range[0]).tz_localize(None)
                end_dt = pd.to_datetime(date_range[1]).tz_localize(None)
                filtered_v = v_df[(v_df['Publish_Date'] >= start_dt) & (v_df['Publish_Date'] <= end_dt)].copy()
            else:
                filtered_v = v_df.copy()
            
            # Metric Display
            if filtered_v.empty:
                st.warning("No videos found in the selected date range.")
                filtered_v = v_df # Fallback to avoid errors
            
            # Task 11 Step 5: Metric Cards with Deltas
            m_col1, m_col2, m_col3, m_col4 = st.columns(4)
            
            # Calcs for deltas
            overall_avg_v = v_df['View_Count'].mean()
            filtered_avg_v = filtered_v['View_Count'].mean()
            v_delta = ((filtered_avg_v / overall_avg_v) - 1) * 100 if overall_avg_v > 0 else 0
            
            overall_avg_e = v_df['Engagement_Rate'].mean()
            filtered_avg_e = filtered_v['Engagement_Rate'].mean()
            e_delta = (filtered_avg_e - overall_avg_e)
            
            m_col1.metric("Subscribers", format_number(c_row['Subscriber_Count']))
            m_col2.metric("Filtered Videos", format_number(len(filtered_v)))
            m_col3.metric("Avg Views", format_number(filtered_avg_v), delta=f"{v_delta:.1f}% vs Avg")
            m_col4.metric("Engagement Rate", f"{filtered_avg_e:.2f}%", delta=f"{e_delta:+.2f}% vs Avg")

            st.markdown("### 📈 Task 12: Data Visualization")
            
            row1_col1, row1_col2 = st.columns(2)
            with row1_col1:
                # Task 12: Line Chart - Views Over Time
                st.markdown("**Views Over Time (Growth Trend)**")
                fig_line = px.area(filtered_v.sort_values('Publish_Date'), x='Publish_Date', y='View_Count', 
                                   template="plotly_dark", color_discrete_sequence=['#ff0000'])
                st.plotly_chart(fig_line, use_container_width=True)
            
            with row1_col2:
                # Task 12: Bar Chart - Top 10 Videos
                st.markdown("**Top 10 Most Viewed Videos**")
                top10 = filtered_v.nlargest(10, 'View_Count')
                fig_bar = px.bar(top10, x='View_Count', y='Title', orientation='h', template="plotly_dark",
                                 color='Performance_Score', color_continuous_scale='Reds')
                fig_bar.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_bar, use_container_width=True)

            row2_col1, row2_col2 = st.columns(2)
            with row2_col1:
                # Task 12: Pie Chart - Video Distribution
                st.markdown("**Video Distribution by Year**")
                filtered_v['Year'] = filtered_v['Publish_Date'].dt.year
                dist = filtered_v['Year'].value_counts().reset_index()
                fig_pie = px.pie(dist, names='Year', values='count', hole=0.4, template="plotly_dark",
                                color_discrete_sequence=px.colors.sequential.Reds_r)
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with row2_col2:
                # Task 12: Scatter Plot - Views vs Engagement
                st.markdown("**Views vs. Engagement Relationship**")
                fig_scatter = px.scatter(filtered_v, x='View_Count', y='Engagement_Rate', size='Like_Count',
                                         hover_name='Title', template="plotly_dark", color='Engagement_Rate',
                                         color_continuous_scale='Reds')
                st.plotly_chart(fig_scatter, use_container_width=True)

        with t_deepdive:
            st.subheader("🔥 Performance Benchmarks")
            # Task 10 Step 9: Benchmark Display
            b_df = benchmark_videos(filtered_v)
            st.dataframe(b_df[['Title', 'View_Count', 'Engagement_Rate', 'View_Benchmark', 'Performance_Score']].nlargest(20, 'Performance_Score'), 
                         use_container_width=True)
            
            # Subscriber to view ratio (Task 10 Step 4)
            ratio = calculate_subscriber_view_ratio(c_row['Subscriber_Count'], filtered_v['View_Count'].sum())
            st.info(f"💡 **Subscriber Engagement Ratio:** {ratio:.2f} views per subscriber in this period.")

        with t_timing:
            st.subheader("🗓️ Timing & Trends Analysis")
            
            # Task 10 Step 7: Optimal Posting Time
            day, hour = get_optimal_posting_time(v_df)
            st.success(f"📌 **Optimal Posting window:** {day} around {hour}:00 (Highest Avg Views)")
            
            # Trend Analysis (Task 10 Step 8)
            period = st.radio("Select Trend Resolution", ['daily', 'weekly', 'monthly'], horizontal=True)
            trend_df = perform_trend_analysis(v_df, period=period)
            fig_trend = px.line(trend_df, x='Publish_Date', y='View_Count', title=f"{period.capitalize()} Growth Trend",
                                template="plotly_dark", markers=True)
            fig_trend.update_traces(line_color="#ff0000")
            st.plotly_chart(fig_trend, use_container_width=True)

        # Task 11 Step 6: Channel Comparison
        with t_compare:
            if 'comp_ids' in st.session_state and len(st.session_state.comp_ids) >= 2:
                st.subheader("⚖️ Side-by-Side Comparison")
                comp_list = []
                for cid in st.session_state.comp_ids:
                    cd, _ = load_channel_from_db(cid)
                    if cd is not None:
                        comp_list.append(cd)
                
                if comp_list:
                    comb_df = pd.concat(comp_list)
                    
                    c1, c2 = st.columns(2)
                    with c1:
                        fig_comp1 = px.bar(comb_df, x='Channel_Name', y='Subscriber_Count', title="Subscribers", 
                                          template="plotly_dark", color='Channel_Name', color_discrete_sequence=px.colors.qualitative.Pastel)
                        st.plotly_chart(fig_comp1, use_container_width=True)
                    with c2:
                        fig_comp2 = px.pie(comb_df, names='Channel_Name', values='Total_Views', title="Total Reach Share",
                                          hole=0.4, template="plotly_dark")
                        st.plotly_chart(fig_comp2, use_container_width=True)
            else:
                st.info("Please select 2 or more channels in the sidebar to compare.")

else:
    # Landing Page
    st.title("YouTube Analytics Engine")
    st.markdown("""
    ### Transform complex YouTube numbers into actionable content strategies.
    
    1.  **Sidebar**: Enter a Channel ID to begin analysis.
    2.  **Dashboard**: View growth trends, engagement deltas, and Top 10 lists.
    3.  **Timing**: Identify the exact hour your audience is most active.
    4.  **Comparison**: Benchmarks your performance against competitors.
    """)
    st.image("https://www.gstatic.com/youtube/img/branding/youtubelogo/svg/youtubelogo.svg", width=200)

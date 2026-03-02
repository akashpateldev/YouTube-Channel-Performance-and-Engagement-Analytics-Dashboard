# YouTube Channel Performance and Engagement Analytics Dashboard

A Streamlit web application that extracts and analyzes YouTube channel and video data using the YouTube Data API v3, featuring a persistent local database and advanced KPI tracking.

## 🚀 Features

- **Channel Analytics**: Real-time extraction of subscribers, views, and video counts.
- **Deep Content Scans**: Extracts views, likes, comments, and engagement metrics for entire video histories.
- **SQL Database**: Persistent local storage using SQLite/SQLAlchemy for historical session tracking.
- **KPI Engine**: Automated calculation of Content Performance Scores, Engagement Rates, and Benchmarks.
- **Scheduling Insights**: Algorithmic detection of optimal posting times based on viewer activity.
- **Interactive Visualizations**: Modern UI with Plotly charts, date filters, and multi-channel comparison.

## 🛠️ Setup

1. **Clone the repository**.
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure API Key**:
   - Create a `.env` file in the root directory.
   - Add: `YOUTUBE_API_KEY=your_google_api_key_here`

## 📊 Usage

1. Launch the application:
   ```bash
   streamlit run app.py
   ```
2. Enter a YouTube **Channel ID** in the sidebar (e.g., `UC_...`).
3. Click **Process Channel** to fetch and store data.
4. Use the tabs to explore Overview, Deep Dives, and Comparison tools.

## 📂 Project Structure

- `app.py`: The central Streamlit dashboard and UI logic.
- `data_processing/`: YouTube API interaction and extraction logic.
- `database/`: SQL models, connection management, and data persistence.
- `analytics/`: KPI calculation engine and complex SQL query modules.
- `requirements.txt`: Python package dependencies.

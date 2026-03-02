import os
from dotenv import load_dotenv
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

load_dotenv("youtube_dashboard/.env")

api_key = os.getenv("YOUTUBE_API_KEY")
print(f"API Key found: {api_key[:5]}...{api_key[-5:] if api_key else 'None'}")

if not api_key:
    print("No API Key found. Exiting.")
    exit()

try:
    youtube = build("youtube", "v3", developerKey=api_key)
    
    # Test with Google Developers Channel ID
    channel_id = "UC_x5XG1OV2P6uZZ5FSM9Ttw" 
    print(f"Testing with Channel ID: {channel_id}")

    request = youtube.channels().list(
        part="snippet,statistics",
        id=channel_id
    )
    response = request.execute()

    if "items" in response and response["items"]:
        print("Success! Channel found.")
        print(f"Title: {response['items'][0]['snippet']['title']}")
    else:
        print("Response received but no items found. Channel ID might be wrong or API key has restricted access?")
        print(response)

except HttpError as e:
    print(f"HTTP Error: {e.resp.status}")
    print(e.content)
except Exception as e:
    print(f"An error occurred: {e}")

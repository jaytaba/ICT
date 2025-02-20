import os
import json
import csv
from googleapiclient.discovery import build

# Set your API Key
API_KEY = "YOUR_GOOGLE_API_KEY"  # Replace with your actual API key
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"

# Load video IDs from file
video_id_file = "D:/AI_Projects/video_ids.txt"  # Update with your actual file path
with open(video_id_file, "r") as f:
    video_ids = [line.strip() for line in f.readlines()]

# Initialize YouTube API
youtube = build(YOUTUBE_API_SERVICE_NAME, YOUTUBE_API_VERSION, developerKey=API_KEY)

# Function to get video metadata
def get_video_metadata(video_ids):
    all_video_data = []
    
    # YouTube API allows max 50 videos per request
    for i in range(0, len(video_ids), 50):
        request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=",".join(video_ids[i:i+50])
        )
        response = request.execute()

        for video in response.get("items", []):
            video_data = {
                "video_id": video["id"],
                "title": video["snippet"]["title"],
                "duration": video["contentDetails"]["duration"],
                "resolution": video["contentDetails"].get("definition", "N/A"),
                "view_count": video["statistics"].get("viewCount", "N/A"),
                "like_count": video["statistics"].get("likeCount", "N/A"),
                "comment_count": video["statistics"].get("commentCount", "N/A"),
                "publish_date": video["snippet"]["publishedAt"]
            }
            all_video_data.append(video_data)

    return all_video_data

# Fetch metadata
video_metadata = get_video_metadata(video_ids)

# Save to CSV
output_csv = "D:/AI_train_data/Train_Prod/VideoList_Metadata.csv"
with open(output_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=video_metadata[0].keys())
    writer.writeheader()
    writer.writerows(video_metadata)

print(f"✅ Metadata saved to {ouVideoList_Me_csv}")

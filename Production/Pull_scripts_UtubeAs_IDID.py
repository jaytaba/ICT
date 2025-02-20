import os
import re
import pyperclip
import yt_dlp
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound

def get_clipboard_history():
    return [pyperclip.paste()]

def find_youtube_url(clipboard_history):
    youtube_url_pattern = r"(https?://)?(www\.)?(youtube\.com|youtu\.be)/[^\s]+"
    for entry in reversed(clipboard_history):
        if match := re.search(youtube_url_pattern, entry):
            return match.group(0)
    return None

def extract_video_id(youtube_url):
    v_match = re.search(r"v=([^&]+)", youtube_url)
    if v_match:
        return v_match.group(1)
    path_match = re.search(r"(?:be/|embed/)([\w-]+)", youtube_url)
    return path_match.group(1) if path_match else None

def fetch_transcript(video_id):
    try:
        # First try English transcripts
        transcript = YouTubeTranscriptApi.get_transcript(video_id, languages=['en'])
        transcript_text = ""
        for entry in transcript:
            # Format the timestamp as MM:SS
            timestamp = f"{int(entry['start'] // 60):02d}:{int(entry['start'] % 60):02d}"
            transcript_text += f"[{timestamp}] {entry['text']} "
        return transcript_text
    except NoTranscriptFound:
        # Fallback to any available transcript
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            transcript = transcript_list.find_manually_created_transcript(
                transcript_list._manually_created_transcripts.keys()
            ).fetch()
            transcript_text = ""
            for entry in transcript:
                # Format the timestamp as MM:SS
                timestamp = f"{int(entry['start'] // 60):02d}:{int(entry['start'] % 60):02d}"
                transcript_text += f"[{timestamp}] {entry['text']} "
            return transcript_text
        except Exception as e:
            return f"Error: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)

def get_playlist_info(url):
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'skip_download': True,
        'ignoreerrors': False,
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)
    except Exception as e:
        print(f"Playlist extraction error: {str(e)}")
        return None

def main():
    with open(r"D:\AI_train_data\Train_Prod\l2.txt", "r") as f:
        video_ids = f.read().splitlines()

    for video_id in video_ids:
        try:
            transcript = fetch_transcript(video_id)
            if "Error:" in transcript:
                print(f"Skipped invalid transcript: {video_id} - {transcript}")
                continue

            sanitized_title = sanitize_filename(video_id)
            file_path = os.path.join("D:/AI_train_data/Train_Prod/transcripts", f"{sanitized_title}.txt")
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(transcript)
            print(f"Saved transcript for: {video_id}")
        except Exception as e:
            print(f"Could not process video: {e}")

if __name__ == "__main__":
    main()

from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptAvailable
from summarizer import generate_summary, chunk_text
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import os
from dotenv import load_dotenv

load_dotenv()

# Use your YouTube Data API key
YOUTUBE_API_KEY = os.getenv('YOUTUBE_API_KEY')

youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

def get_video_id(url):
    if 'youtu.be' in url:
        return url.split('/')[-1]
    elif 'youtube.com' in url:
        return url.split('v=')[1].split('&')[0]
    else:
        raise ValueError("Invalid YouTube URL")

def get_transcript_and_process(video_id):
    try:
        transcript = YouTubeTranscriptApi.get_transcript(video_id)
        full_transcript = ' '.join([entry['text'] for entry in transcript])
        summary = generate_summary(full_transcript)
        chunks = chunk_text(summary)
        return full_transcript, summary, chunks
    except (TranscriptsDisabled, NoTranscriptAvailable):
        return None, None, None

def get_video_title(video_id):
    try:
        request = youtube.videos().list(
            part="snippet",
            id=video_id
        )
        response = request.execute()

        if 'items' in response and len(response['items']) > 0:
            return response['items'][0]['snippet']['title']
        else:
            return "Title not found"
    except HttpError as e:
        print(f"An HTTP error {e.resp.status} occurred: {e.content}")
        return "Error retrieving title"

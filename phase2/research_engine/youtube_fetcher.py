"""
YouTube Fetcher — Phase 2
Searches YouTube for relevant videos per subtopic and fetches their transcripts.
Uses youtube-transcript-api (no API key needed for transcripts).
For search, uses the YouTube Data API v3.
"""

import os
import logging
from typing import Optional
from googleapiclient.discovery import build
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound

logger = logging.getLogger(__name__)

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
MAX_RESULTS_PER_SUBTOPIC = 5


def search_youtube(subtopic: str, max_results: int = MAX_RESULTS_PER_SUBTOPIC) -> list[dict]:
    """
    Search YouTube for videos relevant to a subtopic.
    Returns a list of video metadata dicts.
    """
    if not YOUTUBE_API_KEY:
        logger.warning("YOUTUBE_API_KEY not set — skipping YouTube search.")
        return []

    try:
        youtube = build("youtube", "v3", developerKey=YOUTUBE_API_KEY)
        request = youtube.search().list(
            part="snippet",
            q=f"{subtopic} tutorial lecture explained",
            type="video",
            maxResults=max_results,
            order="relevance",
            relevanceLanguage="en",
            videoDuration="medium",  # 4–20 minutes — avoids shorts and 10-hour streams
        )
        response = request.execute()

        videos = []
        for item in response.get("items", []):
            video_id = item["id"]["videoId"]
            snippet = item["snippet"]
            videos.append({
                "video_id": video_id,
                "title": snippet["title"],
                "channel": snippet["channelTitle"],
                "description": snippet.get("description", "")[:300],
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "source": "youtube",
            })
        return videos

    except Exception as e:
        logger.error(f"YouTube search failed for '{subtopic}': {e}")
        return []


def fetch_transcript(video_id: str) -> Optional[str]:
    """
    Fetch the English transcript for a YouTube video.
    Returns the full transcript text or None if unavailable.
    """
    try:
        transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=["en", "en-US"])
        full_text = " ".join(entry["text"] for entry in transcript_list)
        return full_text.strip()
    except (TranscriptsDisabled, NoTranscriptFound):
        logger.debug(f"No transcript available for video {video_id}")
        return None
    except Exception as e:
        logger.warning(f"Transcript fetch failed for {video_id}: {e}")
        return None


def fetch_youtube_resources(subtopic: str) -> list[dict]:
    """
    Full pipeline: search → fetch transcripts → return enriched resource dicts.
    Each dict is ready for Gemini quality scoring.
    """
    videos = search_youtube(subtopic)
    results = []

    for video in videos:
        transcript = fetch_transcript(video["video_id"])
        resource = {
            **video,
            "subtopic": subtopic,
            "content_preview": transcript[:1500] if transcript else video["description"],
            "has_transcript": transcript is not None,
            "content_length": len(transcript) if transcript else 0,
        }
        results.append(resource)
        logger.info(f"[YouTube] Fetched: {video['title']} | transcript={'yes' if transcript else 'no'}")

    return results

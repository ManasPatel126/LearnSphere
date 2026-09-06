"""
utils/fetcher.py
================
Fetches full text from a URL, with special handling for:
  - YouTube  → youtube-transcript-api (returns transcript text)
  - GitHub   → GitHub REST API (returns README markdown)
  - Everything else → requests + BeautifulSoup (strips HTML tags)

All functions return plain str. Empty string on failure.
"""

import os
import re
import logging
import requests
from urllib.parse import urlparse, parse_qs

logger = logging.getLogger(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; LearnBot/1.0; +https://github.com/yourrepo)"
    )
}


# ── Public entry point ────────────────────────────────────────────────────────

def fetch_url_text(url: str, timeout: int = 15) -> str:
    """
    Dispatch to the correct fetcher based on the URL domain.
    Returns plain text (may be long — caller is responsible for chunking).
    """
    parsed = urlparse(url)
    host = parsed.netloc.lower()

    if "youtube.com" in host or "youtu.be" in host:
        return _fetch_youtube(url)

    if "github.com" in host:
        return _fetch_github(url, timeout=timeout)

    return _fetch_generic(url, timeout=timeout)


# ── YouTube transcript ────────────────────────────────────────────────────────

def _extract_youtube_id(url: str) -> str | None:
    """Return the 11-char video ID from any YouTube URL format."""
    parsed = urlparse(url)
    if "youtu.be" in parsed.netloc:
        return parsed.path.lstrip("/").split("/")[0]
    qs = parse_qs(parsed.query)
    ids = qs.get("v", [])
    return ids[0] if ids else None


def _fetch_youtube(url: str) -> str:
    """Use youtube-transcript-api to get the video transcript."""
    try:
        from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, TranscriptsDisabled  # type: ignore
        video_id = _extract_youtube_id(url)
        if not video_id:
            logger.warning("Could not extract YouTube video ID from: %s", url)
            return ""

        transcript_list = YouTubeTranscriptApi.get_transcript(
            video_id, languages=["en", "en-US", "en-GB"]
        )
        text = " ".join(entry["text"] for entry in transcript_list)
        logger.debug("YouTube transcript fetched: %s (%d chars)", video_id, len(text))
        return text

    except Exception as exc:
        logger.warning("YouTube transcript failed for %s: %s", url, exc)
        return ""


# ── GitHub README ─────────────────────────────────────────────────────────────

def _parse_github_repo(url: str) -> tuple[str, str] | None:
    """
    Extract (owner, repo) from a github.com URL.
    Handles:  github.com/owner/repo
              github.com/owner/repo/tree/main/subdir  (still returns owner/repo)
    """
    parsed = urlparse(url)
    parts = [p for p in parsed.path.split("/") if p]
    if len(parts) >= 2:
        return parts[0], parts[1]
    return None


def _fetch_github(url: str, timeout: int = 15) -> str:
    """Fetch the README of a GitHub repository via the REST API."""
    repo = _parse_github_repo(url)
    if not repo:
        logger.warning("Could not parse GitHub repo from: %s", url)
        return _fetch_generic(url, timeout=timeout)

    owner, name = repo
    api_url = f"https://api.github.com/repos/{owner}/{name}/readme"
    headers = {
        "Accept": "application/vnd.github.raw+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    try:
        resp = requests.get(api_url, headers=headers, timeout=timeout)
        resp.raise_for_status()
        text = resp.text
        # Strip markdown image tags and links to save tokens
        text = re.sub(r"!\[.*?\]\(.*?\)", "", text)
        logger.debug("GitHub README fetched: %s/%s (%d chars)", owner, name, len(text))
        return text
    except requests.HTTPError as exc:
        logger.warning("GitHub API error for %s: %s", url, exc)
        # Fall back to generic fetch
        return _fetch_generic(url, timeout=timeout)
    except Exception as exc:
        logger.warning("GitHub fetch failed for %s: %s", url, exc)
        return ""


# ── Generic HTML page ─────────────────────────────────────────────────────────

def _fetch_generic(url: str, timeout: int = 15) -> str:
    """
    Fetch an arbitrary URL and extract visible text.
    Uses BeautifulSoup to strip tags; skips scripts, styles, nav, footer.
    """
    try:
        resp = requests.get(
            url,
            headers=DEFAULT_HEADERS,
            timeout=timeout,
            allow_redirects=True,
        )
        resp.raise_for_status()
        content_type = resp.headers.get("content-type", "")

        # Handle plain text / markdown files directly
        if "text/plain" in content_type or url.endswith((".md", ".txt", ".rst")):
            return resp.text

        # Parse HTML
        from bs4 import BeautifulSoup  # type: ignore
        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove noise elements
        for tag in soup(["script", "style", "nav", "footer", "header", "aside", "form"]):
            tag.decompose()

        # Prefer main content areas if they exist
        main = (
            soup.find("article")
            or soup.find("main")
            or soup.find(id=re.compile(r"content|main|article", re.I))
            or soup.body
        )
        text = (main or soup).get_text(separator="\n", strip=True)

        # Collapse excessive whitespace
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r" {2,}", " ", text)

        logger.debug("Generic fetch: %s (%d chars)", url, len(text))
        return text

    except requests.Timeout:
        logger.warning("Timeout fetching: %s", url)
        return ""
    except Exception as exc:
        logger.warning("Generic fetch failed for %s: %s", url, exc)
        return ""

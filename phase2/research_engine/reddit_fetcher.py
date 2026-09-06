"""
Reddit Fetcher — Phase 2
Searches relevant subreddits for highly-upvoted posts about a subtopic.
Uses PRAW (Python Reddit API Wrapper) — read-only, no user auth needed.
Requires REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT in .env.
"""

import os
import logging
import praw

logger = logging.getLogger(__name__)

REDDIT_CLIENT_ID = os.getenv("REDDIT_CLIENT_ID")
REDDIT_CLIENT_SECRET = os.getenv("REDDIT_CLIENT_SECRET")
REDDIT_USER_AGENT = os.getenv("REDDIT_USER_AGENT", "LearnPathBot/1.0")

# Subreddits to search per query — add/remove based on topic domains
LEARNING_SUBREDDITS = [
    "learnprogramming",
    "MachineLearning",
    "datascience",
    "cscareerquestions",
    "learnmachinelearning",
    "ArtificialIntelligence",
    "deeplearning",
    "Python",
    "programming",
    "compsci",
]

MAX_POSTS_PER_SUBTOPIC = 8


def _get_reddit_client() -> praw.Reddit | None:
    if not REDDIT_CLIENT_ID or not REDDIT_CLIENT_SECRET:
        logger.warning("Reddit credentials not set — skipping Reddit fetch.")
        return None
    return praw.Reddit(
        client_id=REDDIT_CLIENT_ID,
        client_secret=REDDIT_CLIENT_SECRET,
        user_agent=REDDIT_USER_AGENT,
        read_only=True,
    )


def search_reddit(subtopic: str, max_results: int = MAX_POSTS_PER_SUBTOPIC) -> list[dict]:
    """
    Search across curated subreddits for top posts about the subtopic.
    Returns post metadata + body text preview.
    """
    reddit = _get_reddit_client()
    if not reddit:
        return []

    results = []
    seen_ids = set()

    try:
        # Search across a combined multireddit string
        subreddit_str = "+".join(LEARNING_SUBREDDITS)
        subreddit = reddit.subreddit(subreddit_str)

        for post in subreddit.search(
            subtopic,
            sort="relevance",
            time_filter="year",
            limit=max_results * 2,  # fetch extra, filter down by score
        ):
            if post.id in seen_ids:
                continue
            seen_ids.add(post.id)

            # Skip low-engagement posts
            if post.score < 50:
                continue

            # Grab top comments for richer content
            post.comments.replace_more(limit=0)
            top_comments = []
            for comment in post.comments[:5]:
                if hasattr(comment, "body") and len(comment.body) > 100:
                    top_comments.append(comment.body[:400])

            body = post.selftext.strip() if post.selftext else ""
            combined_content = f"{post.title}\n\n{body}\n\n" + "\n\n".join(top_comments)

            results.append({
                "post_id": post.id,
                "title": post.title,
                "subreddit": post.subreddit.display_name,
                "url": f"https://reddit.com{post.permalink}",
                "score": post.score,
                "num_comments": post.num_comments,
                "source": "reddit",
                "subtopic": subtopic,
                "content_preview": combined_content[:1500],
                "content_length": len(combined_content),
                # Upvote score normalised 0–1, capped at 5000
                "upvote_score": min(post.score / 5000, 1.0),
            })

            if len(results) >= max_results:
                break

        logger.info(f"[Reddit] Found {len(results)} posts for '{subtopic}'")
        return results

    except Exception as e:
        logger.error(f"Reddit search failed for '{subtopic}': {e}")
        return []


def fetch_reddit_resources(subtopic: str) -> list[dict]:
    """
    Alias for the pipeline runner — consistent interface across all fetchers.
    """
    return search_reddit(subtopic)

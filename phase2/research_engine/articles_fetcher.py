"""
Articles Fetcher — Phase 2
Fetches relevant articles and web content using Perplexity's sonar API.
Perplexity handles the search + content extraction in one call — no raw HTML scraping.
Falls back to NewsAPI for more article-style sources.
Requires PERPLEXITY_API_KEY (and optionally NEWS_API_KEY) in .env.
"""

import os
import logging
import requests

logger = logging.getLogger(__name__)

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
NEWS_API_URL = "https://newsapi.org/v2/everything"

MAX_ARTICLES_PER_SUBTOPIC = 5


def fetch_perplexity_articles(subtopic: str) -> list[dict]:
    """
    Uses Perplexity's online model to get a structured list of high-quality
    learning resources (articles, docs, blog posts) for the subtopic.
    The model returns citations as URLs which we capture.
    """
    if not PERPLEXITY_API_KEY:
        logger.warning("PERPLEXITY_API_KEY not set — skipping Perplexity fetch.")
        return []

    prompt = (
        f"List the 5 best free online articles, documentation pages, or tutorials for learning "
        f"'{subtopic}'. For each, provide: title, URL, source name, and a 2-sentence summary "
        f"of what it covers. Focus on beginner-to-intermediate depth. "
        f"Prefer official docs, well-known tutorial sites (MDN, freeCodeCamp, Towards Data Science, "
        f"ArXiv, GeeksForGeeks), and high-quality blog posts. Respond in JSON array format."
    )

    try:
        headers = {
            "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": "sonar",
            "messages": [
                {
                    "role": "system",
                    "content": "You are a research assistant. Always respond with valid JSON only, no markdown.",
                },
                {"role": "user", "content": prompt},
            ],
            "max_tokens": 1200,
            "return_citations": True,
        }

        response = requests.post(PERPLEXITY_API_URL, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
        data = response.json()

        raw_content = data["choices"][0]["message"]["content"]
        citations = data.get("citations", [])

        # Parse the JSON array from the model's response
        import json, re
        # Strip markdown code fences if present
        clean = re.sub(r"```json|```", "", raw_content).strip()
        articles_raw = json.loads(clean)

        results = []
        for i, article in enumerate(articles_raw[:MAX_ARTICLES_PER_SUBTOPIC]):
            url = article.get("url") or (citations[i] if i < len(citations) else "")
            results.append({
                "title": article.get("title", "Unknown"),
                "url": url,
                "source_name": article.get("source", "Web"),
                "description": article.get("summary", ""),
                "content_preview": article.get("summary", "")[:1500],
                "content_length": len(article.get("summary", "")),
                "source": "perplexity",
                "subtopic": subtopic,
            })

        logger.info(f"[Perplexity] Fetched {len(results)} articles for '{subtopic}'")
        return results

    except Exception as e:
        logger.error(f"Perplexity fetch failed for '{subtopic}': {e}")
        return []


def fetch_newsapi_articles(subtopic: str) -> list[dict]:
    """
    Fallback: NewsAPI for recent article headlines + descriptions.
    Less useful than Perplexity but good as a supplemental source.
    """
    if not NEWS_API_KEY:
        return []

    try:
        params = {
            "q": subtopic,
            "sortBy": "relevancy",
            "language": "en",
            "pageSize": MAX_ARTICLES_PER_SUBTOPIC,
            "apiKey": NEWS_API_KEY,
        }
        response = requests.get(NEWS_API_URL, params=params, timeout=10)
        response.raise_for_status()
        articles = response.json().get("articles", [])

        results = []
        for article in articles:
            content = f"{article.get('title', '')} — {article.get('description', '')} {article.get('content', '')}"
            results.append({
                "title": article.get("title", ""),
                "url": article.get("url", ""),
                "source_name": article.get("source", {}).get("name", "News"),
                "description": article.get("description", ""),
                "content_preview": content[:1500],
                "content_length": len(content),
                "source": "newsapi",
                "subtopic": subtopic,
            })

        logger.info(f"[NewsAPI] Fetched {len(results)} articles for '{subtopic}'")
        return results

    except Exception as e:
        logger.error(f"NewsAPI fetch failed for '{subtopic}': {e}")
        return []


def fetch_article_resources(subtopic: str) -> list[dict]:
    """
    Pipeline: try Perplexity first, pad with NewsAPI if under quota.
    """
    results = fetch_perplexity_articles(subtopic)
    if len(results) < MAX_ARTICLES_PER_SUBTOPIC:
        results += fetch_newsapi_articles(subtopic)
    return results[:MAX_ARTICLES_PER_SUBTOPIC]

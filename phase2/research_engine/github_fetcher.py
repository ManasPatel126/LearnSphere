"""
GitHub Fetcher — Phase 2
Searches GitHub for top-starred repos relevant to a subtopic and fetches their READMEs.
Uses the GitHub REST API (unauthenticated = 60 req/hr, authenticated = 5000 req/hr).
Set GITHUB_TOKEN in .env for production use.
"""

import os
import base64
import logging
import requests

logger = logging.getLogger(__name__)

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_API_BASE = "https://api.github.com"
MAX_REPOS_PER_SUBTOPIC = 5

HEADERS = {
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
if GITHUB_TOKEN:
    HEADERS["Authorization"] = f"Bearer {GITHUB_TOKEN}"


def search_github_repos(subtopic: str, max_results: int = MAX_REPOS_PER_SUBTOPIC) -> list[dict]:
    """
    Search GitHub for repos matching the subtopic, sorted by stars.
    """
    try:
        query = f"{subtopic} in:name,description,readme"
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": max_results,
        }
        response = requests.get(
            f"{GITHUB_API_BASE}/search/repositories",
            headers=HEADERS,
            params=params,
            timeout=10,
        )
        response.raise_for_status()
        items = response.json().get("items", [])

        repos = []
        for item in items:
            repos.append({
                "repo_id": item["id"],
                "name": item["full_name"],
                "title": item["name"],
                "description": item.get("description") or "",
                "url": item["html_url"],
                "stars": item["stargazers_count"],
                "language": item.get("language") or "Unknown",
                "topics": item.get("topics", []),
                "source": "github",
            })
        return repos

    except Exception as e:
        logger.error(f"GitHub search failed for '{subtopic}': {e}")
        return []


def fetch_readme(full_name: str) -> str | None:
    """
    Fetch and decode the README for a repo given its 'owner/repo' full name.
    """
    try:
        response = requests.get(
            f"{GITHUB_API_BASE}/repos/{full_name}/readme",
            headers=HEADERS,
            timeout=10,
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        content_b64 = response.json().get("content", "")
        # GitHub returns base64 with newlines
        readme_text = base64.b64decode(content_b64.replace("\n", "")).decode("utf-8", errors="replace")
        return readme_text.strip()
    except Exception as e:
        logger.warning(f"README fetch failed for {full_name}: {e}")
        return None


def fetch_github_resources(subtopic: str) -> list[dict]:
    """
    Full pipeline: search repos → fetch READMEs → return enriched resource dicts.
    """
    repos = search_github_repos(subtopic)
    results = []

    for repo in repos:
        readme = fetch_readme(repo["name"])
        resource = {
            **repo,
            "subtopic": subtopic,
            "content_preview": (readme[:1500] if readme else repo["description"]),
            "has_readme": readme is not None,
            "content_length": len(readme) if readme else 0,
            # Stars is a strong quality signal for GitHub content
            "star_score": min(repo["stars"] / 10000, 1.0),  # normalised 0–1 cap at 10k stars
        }
        results.append(resource)
        logger.info(f"[GitHub] Fetched: {repo['name']} ({repo['stars']}⭐) | readme={'yes' if readme else 'no'}")

    return results

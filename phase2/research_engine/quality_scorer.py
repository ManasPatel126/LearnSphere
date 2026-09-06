"""
Quality Scorer — Phase 2
Takes a raw resource dict and asks Gemini to score it 0–1 for quality/relevance.
Also blends in signal-based scores (stars, upvotes) where available.
Output score is written back into the resource dict as 'quality_score'.
"""

import os
import json
import logging
import re
import google.generativeai as genai

logger = logging.getLogger(__name__)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

SCORER_MODEL = "gemini-1.5-flash"  # Fast + cheap for scoring — not the main generation model

SCORE_PROMPT_TEMPLATE = """
You are evaluating a learning resource for the subtopic: "{subtopic}"

Resource details:
- Title: {title}
- Source: {source}
- Content preview: {content_preview}

Score this resource on a scale of 0.0 to 1.0 based on:
1. Relevance to the subtopic (0.4 weight)
2. Quality and depth of content (0.4 weight)
3. Source credibility (0.2 weight)

Return ONLY a JSON object with this exact format:
{{"score": 0.85, "reason": "one sentence explanation"}}

No markdown, no extra text.
"""


def score_resource_with_gemini(resource: dict) -> dict:
    """
    Sends a resource to Gemini Flash for a quality score.
    Returns the resource dict with 'gemini_score' and 'score_reason' added.
    Falls back to signal-based scoring if Gemini call fails.
    """
    if not GEMINI_API_KEY:
        logger.warning("GEMINI_API_KEY not set — using signal-based scoring only.")
        return _signal_based_score(resource)

    prompt = SCORE_PROMPT_TEMPLATE.format(
        subtopic=resource.get("subtopic", "unknown"),
        title=resource.get("title", "Unknown"),
        source=resource.get("source", "unknown"),
        content_preview=(resource.get("content_preview") or "")[:800],
    )

    try:
        model = genai.GenerativeModel(SCORER_MODEL)
        response = model.generate_content(prompt)
        raw = response.text.strip()

        # Strip any stray markdown fences
        clean = re.sub(r"```json|```", "", raw).strip()
        parsed = json.loads(clean)

        gemini_score = float(parsed.get("score", 0.5))
        reason = parsed.get("reason", "")

        # Blend: 70% Gemini semantic score + 30% hard signal
        signal_score = _compute_signal_score(resource)
        final_score = round(0.7 * gemini_score + 0.3 * signal_score, 4)

        resource["gemini_score"] = gemini_score
        resource["signal_score"] = signal_score
        resource["quality_score"] = final_score
        resource["score_reason"] = reason

        logger.debug(f"Scored '{resource['title']}': {final_score} (gemini={gemini_score}, signal={signal_score})")
        return resource

    except Exception as e:
        logger.warning(f"Gemini scoring failed for '{resource.get('title')}': {e} — falling back to signals.")
        return _signal_based_score(resource)


def _compute_signal_score(resource: dict) -> float:
    """
    Compute a 0–1 score purely from metadata signals (stars, upvotes, transcript presence).
    """
    score = 0.5  # neutral baseline

    # GitHub: stars are a strong signal
    if "star_score" in resource:
        score = max(score, resource["star_score"])

    # Reddit: upvotes
    if "upvote_score" in resource:
        score = (score + resource["upvote_score"]) / 2

    # YouTube: having a transcript means substantive content
    if resource.get("has_transcript"):
        score = min(score + 0.1, 1.0)

    # Content length: more content = more substance (up to a point)
    length = resource.get("content_length", 0)
    if length > 2000:
        score = min(score + 0.05, 1.0)

    return round(score, 4)


def _signal_based_score(resource: dict) -> dict:
    """
    Fallback: score purely from metadata signals, no Gemini call.
    """
    signal_score = _compute_signal_score(resource)
    resource["gemini_score"] = None
    resource["signal_score"] = signal_score
    resource["quality_score"] = signal_score
    resource["score_reason"] = "Signal-based score (Gemini unavailable)"
    return resource


def batch_score_resources(resources: list[dict]) -> list[dict]:
    """
    Score a list of resources. Returns the same list with scores added, sorted best-first.
    """
    scored = []
    for resource in resources:
        scored.append(score_resource_with_gemini(resource))

    # Sort by quality_score descending
    scored.sort(key=lambda r: r.get("quality_score", 0), reverse=True)
    return scored

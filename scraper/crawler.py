import os
import re
import requests
import time
from datetime import datetime, timezone

KEYWORDS_POSITIVE = [
    "free api", "free tier", "free plan", "free credits",
    "free access", "no cost", "zero cost", "free trial",
    "free model", "free endpoint", "open api", "open source model",
    "free quota", "free allowance", "gratis", "白嫖",
    "免费", "免费额度", "免费接口", "免费api",
    "free llm", "free gpt", "free claude", "free gemini",
    "huggingface free", "openrouter free", "free inference",
    "serverless api", "free hosting",
]

KEYWORDS_NEGATIVE = [
    "hiring", "job", "career", "salary",
    "course", "tutorial series", "youtube",
    "meetup", "conference", "podcast",
]

SUBREDDITS = os.environ.get(
    "REDDIT_SUBREDDITS", "LocalLLaMA,MachineLearning,artificial,OpenAI,ChatGPT"
).split(",")

REDDIT_URL = "https://www.reddit.com"


def fetch_subreddit_posts(subreddit, limit=25):
    headers = {"User-Agent": "FreeAIScanner/1.0 (educational project)"}
    url = f"{REDDIT_URL}/r/{subreddit}/new.json?limit={limit}"
    try:
        resp = requests.get(url, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        posts = []
        for child in data.get("data", {}).get("children", []):
            d = child["data"]
            posts.append({
                "id": d.get("name", ""),
                "title": d.get("title", ""),
                "selftext": d.get("selftext", ""),
                "url": f"{REDDIT_URL}{d.get('permalink', '')}",
                "subreddit": subreddit,
                "created_utc": d.get("created_utc", 0),
                "score": d.get("score", 0),
                "num_comments": d.get("num_comments", 0),
            })
        return posts
    except Exception as e:
        print(f"[ERROR] fetch r/{subreddit}: {e}")
        return []


def keyword_filter(post):
    text = f"{post['title']} {post['selftext']}".lower()

    for kw in KEYWORDS_NEGATIVE:
        if kw.lower() in text:
            return False

    for kw in KEYWORDS_POSITIVE:
        if kw.lower() in text:
            return True

    return False


def crawl_and_prefilter():
    all_posts = []
    for sub in SUBREDDITS:
        sub = sub.strip()
        if not sub:
            continue
        print(f"[INFO] Fetching r/{sub} ...")
        posts = fetch_subreddit_posts(sub, limit=25)
        all_posts.extend(posts)
        time.sleep(1)

    seen = set()
    unique = []
    for p in all_posts:
        if p["id"] not in seen:
            seen.add(p["id"])
            unique.append(p)

    candidates = [p for p in unique if keyword_filter(p)]

    print(f"[INFO] Total fetched: {len(unique)}, After keyword filter: {len(candidates)}")
    return candidates


if __name__ == "__main__":
    results = crawl_and_prefilter()
    for r in results:
        print(f"  [{r['subreddit']}] {r['title'][:80]}")

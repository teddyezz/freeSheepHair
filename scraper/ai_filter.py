import os
import google.generativeai as genai

MODEL_NAME = "gemini-2.0-flash-lite"

SYSTEM_PROMPT = """You are a classifier that determines if a social media post is about a FREE AI API deal.

A valid deal post must describe:
- A free API endpoint, free tier, free credits, or free quota for an AI/LLM service
- A newly available free model or free inference API
- A time-limited free promotion for an AI API

NOT valid:
- General AI news, opinions, tutorials
- Paid-only services
- Job postings, courses, meetups

Respond with ONLY "YES" or "NO"."""


def init_gemini():
    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not set")
    genai.configure(api_key=api_key)


def ai_filter_post(post):
    title = post.get("title", "")
    body = post.get("selftext", "")
    text = f"Title: {title}\n\nBody: {body[:1500]}"

    try:
        model = genai.GenerativeModel(
            model_name=MODEL_NAME,
            system_instruction=SYSTEM_PROMPT,
        )
        response = model.generate_content(
            text,
            generation_config=genai.types.GenerationConfig(
                max_output_tokens=10,
                temperature=0.0,
            ),
        )
        answer = response.text.strip().upper()
        return answer.startswith("YES")
    except Exception as e:
        print(f"[ERROR] Gemini API call failed: {e}")
        return False


def ai_filter_batch(posts):
    init_gemini()
    deals = []
    for i, post in enumerate(posts):
        print(f"[INFO] AI filtering {i+1}/{len(posts)}: {post['title'][:60]}...")
        is_deal = ai_filter_post(post)
        if is_deal:
            deals.append(post)
            print(f"  -> YES (deal found!)")
        else:
            print(f"  -> NO")
    print(f"[INFO] AI filter result: {len(deals)} deals from {len(posts)} candidates")
    return deals


if __name__ == "__main__":
    from crawler import crawl_and_prefilter
    candidates = crawl_and_prefilter()
    if candidates:
        deals = ai_filter_batch(candidates)
        for d in deals:
            print(f"  DEAL: {d['title'][:80]}")
    else:
        print("No candidates to filter.")

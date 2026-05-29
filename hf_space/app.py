import os
import csv
import io
import httpx
from collections import deque
from fastapi import FastAPI, BackgroundTasks, Request
from huggingface_hub import hf_hub_download

app = FastAPI()

PROCESSED_UPDATES = deque(maxlen=1000)

TG_TOKEN = os.environ.get("TG_BOT_TOKEN", "")
HF_DATASET_REPO = os.environ.get("HF_DATASET_REPO", "")
HF_TOKEN = os.environ.get("HF_TOKEN", "")
CSV_FILENAME = "deals.csv"
TG_API_BASE = f"https://api.telegram.org/bot{TG_TOKEN}"


def load_deals():
    if not HF_DATASET_REPO:
        return []
    try:
        path = hf_hub_download(
            repo_id=HF_DATASET_REPO,
            filename=CSV_FILENAME,
            repo_type="dataset",
            token=HF_TOKEN,
        )
        deals = []
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                deals.append(row)
        return deals
    except Exception as e:
        print(f"[ERROR] load_deals: {e}")
        return []


async def send_telegram_message(chat_id, text):
    if not TG_TOKEN:
        return
    async with httpx.AsyncClient(timeout=30) as client:
        await client.post(
            f"{TG_API_BASE}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
        )


def format_deals(deals, max_items=10):
    if not deals:
        return "No free AI API deals found yet. Check back later!"

    lines = ["<b>Free AI API Deals</b>\n"]
    for i, deal in enumerate(deals[:max_items], 1):
        title = deal.get("title", "Untitled")[:80]
        url = deal.get("url", "")
        sub = deal.get("subreddit", "")
        score = deal.get("score", "0")
        lines.append(f"{i}. <a href=\"{url}\">{title}</a>")
        lines.append(f"   r/{sub} | score: {score}\n")

    if len(deals) > max_items:
        lines.append(f"... and {len(deals) - max_items} more deals.")

    return "\n".join(lines)


async def process_tg_query(update_dict):
    message = update_dict.get("message", {})
    chat_id = message.get("chat", {}).get("id")
    text = message.get("text", "")

    if not chat_id:
        return

    if text.startswith("/start"):
        await send_telegram_message(
            chat_id,
            "Welcome! I track free AI API deals from Reddit.\n\n"
            "/search - Show latest deals\n"
            "/latest - Show 5 most recent deals",
        )
        return

    if text.startswith("/search") or text.startswith("/latest"):
        deals = load_deals()
        if text.startswith("/latest"):
            deals = deals[:5]
        reply = format_deals(deals, max_items=10)
        await send_telegram_message(chat_id, reply)
        return


@app.post("/webhook")
async def telegram_webhook(request: Request, background_tasks: BackgroundTasks):
    try:
        data = await request.json()
        update_id = data.get("update_id")

        if update_id:
            if update_id in PROCESSED_UPDATES:
                return {"status": "ignored_duplicate"}
            PROCESSED_UPDATES.append(update_id)
            background_tasks.add_task(process_tg_query, data)

        return {"status": "ok"}
    except Exception as e:
        print(f"[ERROR] webhook: {e}")
        return {"status": "error"}


@app.get("/")
async def health():
    return {"status": "alive", "deals_repo": HF_DATASET_REPO}


@app.get("/health")
async def health_check():
    deals = load_deals()
    return {"status": "ok", "deals_count": len(deals)}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7860)

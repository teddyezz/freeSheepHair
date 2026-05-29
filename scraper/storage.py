import os
import csv
import io
from datetime import datetime, timezone
from huggingface_hub import HfApi

CSV_FILENAME = "deals.csv"
CSV_COLUMNS = [
    "id", "title", "url", "subreddit", "score",
    "num_comments", "created_utc", "discovered_at"
]


def get_dataset_repo():
    repo = os.environ.get("HF_DATASET_REPO", "")
    if not repo:
        raise ValueError("HF_DATASET_REPO not set")
    return repo


def load_existing_ids():
    try:
        from huggingface_hub import hf_hub_download
        path = hf_hub_download(
            repo_id=get_dataset_repo(),
            filename=CSV_FILENAME,
            repo_type="dataset",
        )
        ids = set()
        with open(path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ids.add(row.get("id", ""))
        return ids
    except Exception:
        return set()


def append_deals_to_dataset(deals):
    if not deals:
        print("[INFO] No new deals to save.")
        return

    token = os.environ.get("HF_TOKEN", "")
    if not token:
        raise ValueError("HF_TOKEN not set")

    repo = get_dataset_repo()
    api = HfApi(token=token)
    existing_ids = load_existing_ids()

    new_deals = [d for d in deals if d["id"] not in existing_ids]
    if not new_deals:
        print("[INFO] All deals already in dataset, skipping.")
        return

    try:
        from huggingface_hub import hf_hub_download
        path = hf_hub_download(
            repo_id=repo, filename=CSV_FILENAME, repo_type="dataset"
        )
        with open(path, "r", encoding="utf-8") as f:
            existing_content = f.read()
    except Exception:
        header = ",".join(CSV_COLUMNS) + "\n"
        existing_content = header

    buf = io.StringIO(existing_content)
    rows = list(csv.DictReader(buf))

    now = datetime.now(timezone.utc).isoformat()
    for deal in new_deals:
        rows.append({
            "id": deal["id"],
            "title": deal["title"].replace(",", " ").replace("\n", " ")[:200],
            "url": deal["url"],
            "subreddit": deal["subreddit"],
            "score": str(deal.get("score", 0)),
            "num_comments": str(deal.get("num_comments", 0)),
            "created_utc": str(deal.get("created_utc", "")),
            "discovered_at": now,
        })

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS)
    writer.writeheader()
    writer.writerows(rows)

    api.upload_file(
        path_or_fileobj=output.getvalue().encode("utf-8"),
        path_in_repo=CSV_FILENAME,
        repo_id=repo,
        repo_type="dataset",
        commit_message=f"Add {len(new_deals)} new deal(s) - {now[:10]}",
    )
    print(f"[INFO] Saved {len(new_deals)} new deal(s) to {repo}/{CSV_FILENAME}")


if __name__ == "__main__":
    from crawler import crawl_and_prefilter
    from ai_filter import ai_filter_batch
    candidates = crawl_and_prefilter()
    deals = ai_filter_batch(candidates)
    append_deals_to_dataset(deals)

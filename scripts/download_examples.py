import requests
import json
import time
import sys
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SYNTAX_FILE, RAW_EXAMPLES_FILE, TARGET_ADDONS, DATA_DIR

MAX_WORKERS = 50
START_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 1
END_ID = int(sys.argv[2]) if len(sys.argv) > 2 else 15000


def load_syntax_ids(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(
            f"❌ {filepath} not found. Run download_syntax.py first."
        )
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    valid_ids = set()
    target_addons_lower = [a.lower() for a in TARGET_ADDONS]
    for item in data:
        addon_name = item.get("addon", {}).get("name", "").lower()
        if addon_name in target_addons_lower:
            valid_ids.add(item["id"])
    return valid_ids


def fetch_examples(syntax_id):
    url = (
        f"https://skripthub.net/api/v1/syntaxexample/?syntax={syntax_id}&user_vote=true"
    )
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return syntax_id, response.json()
        elif response.status_code == 429:
            time.sleep(2)
            return fetch_examples(syntax_id)
        else:
            return syntax_id, []
    except Exception:
        return syntax_id, []


def save_raw_data(data):
    with open(RAW_EXAMPLES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def main():
    global_raw_data = {}
    os.makedirs(DATA_DIR, exist_ok=True)
    valid_ids = load_syntax_ids(SYNTAX_FILE)

    if os.path.exists(RAW_EXAMPLES_FILE):
        try:
            with open(RAW_EXAMPLES_FILE, "r", encoding="utf-8") as f:
                global_raw_data = json.load(f)
        except Exception:
            global_raw_data = {}

    ids_to_scrape = [
        sid
        for sid in valid_ids
        if START_ID <= sid <= END_ID and str(sid) not in global_raw_data
    ]

    completed = 0
    total = len(ids_to_scrape)

    print(f"Scraping {total} examples...", end="")
    sys.stdout.flush()

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {
            executor.submit(fetch_examples, sid): sid for sid in ids_to_scrape
        }
        for future in as_completed(future_map):
            result = future.result()
            if result is None:
                continue
            sid, examples = result
            global_raw_data[str(sid)] = examples
            completed += 1

            print(f"\r⏳ Progress: {completed}/{total} examples fetched", end="")
            sys.stdout.flush()

            if completed % 50 == 0:
                save_raw_data(global_raw_data)

    save_raw_data(global_raw_data)
    print(
        f"\n✅ Done. Saved {len(global_raw_data)} total entries to {RAW_EXAMPLES_FILE}"
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n❌ Critical Error: {e}")
        sys.exit(1)

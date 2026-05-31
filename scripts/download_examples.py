import requests
import json
import time
import sys
import os
import signal
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SYNTAX_FILE, RAW_EXAMPLES_FILE, TARGET_ADDONS, DATA_DIR

MAX_WORKERS = 10
START_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 1
END_ID = int(sys.argv[2]) if len(sys.argv) > 2 else 15000

global_raw_data = {}
is_running = True

def signal_handler(sig, frame):
    global is_running
    print("\n\n⚠️ Interrupt received! Saving progress...")
    is_running = False
    save_raw_data()
    print("✅ Safe exit complete. Run merge_syntax_and_examples.py to finalize.")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

def load_syntax_ids(filepath):
    print(f"📂 Loading {filepath}...")
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"❌ {filepath} not found. Run download_syntax.py first.")
    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            raise ValueError("❌ Invalid JSON in syntax.json")
            
    valid_ids = set()
    target_addons_lower = [a.lower() for a in TARGET_ADDONS]
    for item in data:
        addon_name = item.get("addon", {}).get("name", "").lower()
        if addon_name in target_addons_lower:
            valid_ids.add(item["id"])
    print(f"✅ Found {len(valid_ids)} valid syntax IDs for {TARGET_ADDONS}")
    return valid_ids

def fetch_examples(syntax_id):
    if not is_running:
        return None
    url = f"https://skripthub.net/api/v1/syntaxexample/?syntax={syntax_id}&user_vote=true"
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

def save_raw_data():
    global global_raw_data
    try:
        with open(RAW_EXAMPLES_FILE, 'w', encoding='utf-8') as f:
            json.dump(global_raw_data, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved {len(global_raw_data)} entries to {RAW_EXAMPLES_FILE}")
    except Exception as e:
        print(f"❌ Error saving raw data: {e}")

def main():
    os.makedirs(DATA_DIR, exist_ok=True)
    valid_ids = load_syntax_ids(SYNTAX_FILE)
    
    print(f"\n🚀 PHASE 1: Scanning IDs {START_ID}-{END_ID} ({MAX_WORKERS} threads)...")
    if os.path.exists(RAW_EXAMPLES_FILE):
        try:
            with open(RAW_EXAMPLES_FILE, 'r', encoding='utf-8') as f:
                global_raw_data = json.load(f)
            print(f"   📂 Resuming ({len(global_raw_data)} existing entries)")
        except Exception:
            global_raw_data = {}
            
    ids_to_scrape = [sid for sid in valid_ids if START_ID <= sid <= END_ID and str(sid) not in global_raw_data]
    print(f"   ⏳ {len(ids_to_scrape)} IDs remaining...")
    
    completed = 0
    total = len(ids_to_scrape)
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_map = {executor.submit(fetch_examples, sid): sid for sid in ids_to_scrape}
        for future in as_completed(future_map):
            if not is_running:
                break
            result = future.result()
            if result is None:
                continue
            sid, examples = result
            global_raw_data[str(sid)] = examples
            completed += 1
            status = f"✅ {len(examples)} ex" if examples else "⚪ empty"
            print(f"   [{completed}/{total}] ID {sid}: {status}")
            if completed % 50 == 0:
                save_raw_data()
                
    if is_running:
        save_raw_data()
        print("✅ Phase 1 Complete. Run merge_syntax_and_examples.py next.")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"\n💀 Critical Error: {e}")
        sys.exit(1)
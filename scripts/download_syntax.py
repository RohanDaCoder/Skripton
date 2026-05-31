import json
import os
import sys
import requests

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import DATA_DIR, SYNTAX_FILE

def download_syntax():
    API_URL = "https://skripthub.net/api/v1/addonsyntaxlist/"
    
    print(f"[INFO] Downloading raw syntax data from {API_URL}...")
    
    try:
        response = requests.get(API_URL, timeout=30)
        response.raise_for_status()
        data = response.json()
        
        if not isinstance(data, list):
            print("[ERROR] API returned unexpected data format")
            return
            
        print(f"[INFO] Successfully downloaded {len(data)} raw entries")
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Request failed: {e}")
        return
    except json.JSONDecodeError:
        print("[ERROR] Failed to parse JSON response")
        return
    except Exception as e:
        print(f"[ERROR] Unexpected error occurred during download: {e}")
        return

    # Ensure the data directory exists
    os.makedirs(DATA_DIR, exist_ok=True)

    # Save the completely raw, unfiltered data
    try:
        with open(SYNTAX_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"[SUCCESS] Saved raw syntax data to {SYNTAX_FILE}")
    except Exception as e:
        print(f"[ERROR] Failed to save file: {e}")

if __name__ == "__main__":
    download_syntax()
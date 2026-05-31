import json
import os
import sys

# Add parent directory to path to import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import SYNTAX_FILE, RAW_EXAMPLES_FILE, MERGED_FILE

def merge():
    print(f"\n🔄 Merging {RAW_EXAMPLES_FILE} into {MERGED_FILE}...")
    
    if not os.path.exists(SYNTAX_FILE):
        print(f"❌ {SYNTAX_FILE} not found. Run download_syntax.py first.")
        return
    if not os.path.exists(RAW_EXAMPLES_FILE):
        print(f"❌ {RAW_EXAMPLES_FILE} not found. Run download_examples.py first.")
        return

    with open(SYNTAX_FILE, 'r', encoding='utf-8') as f:
        syntax_data = json.load(f)
        
    with open(RAW_EXAMPLES_FILE, 'r', encoding='utf-8') as f:
        raw_examples = json.load(f)

    merged_count = 0
    for item in syntax_data:
        sid = str(item["id"])
        if sid in raw_examples:
            item["examples"] = raw_examples[sid]
            if raw_examples[sid]:
                merged_count += 1
        else:
            # Ensure every item has an examples list, even if empty
            item["examples"] = []

    with open(MERGED_FILE, 'w', encoding='utf-8') as f:
        json.dump(syntax_data, f, indent=2, ensure_ascii=False)
        
    print(f"✅ Merged {merged_count}/{len(syntax_data)} entries with examples.")

if __name__ == "__main__":
    merge()
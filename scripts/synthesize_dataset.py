import os
import json
import random
import re
from config import TARGET_ADDONS

DATA_DIR = "data"
DATASET_FILE = os.path.join(DATA_DIR, "skripton_dataset.json")
MERGED_FILE = os.path.join(DATA_DIR, "syntax_with_examples.json")

os.makedirs(DATA_DIR, exist_ok=True)

if not os.path.exists(MERGED_FILE):
    os.system("python scripts/merge_syntax_and_examples.py")


def normalize_skript_tabs(code):
    if not code:
        return ""
    code = re.sub(r"^( {4}| {2})", "\t", code, flags=re.MULTILINE)
    return code.replace("\r\n", "\n").strip()


def inject_advanced_bug(code):
    lines = code.split("\n")
    bug_type = random.choice(["indent", "missing_trigger", "wrong_op", "event_value"])
    if bug_type == "indent":
        nested_lines = [i for i, line in enumerate(lines) if line.startswith("\t")]
        if not nested_lines:
            return code, "Indentation error"
        target_idx = random.choice(nested_lines)
        lines[target_idx] = lines[target_idx].replace("\t", "", 1)
        return "\n".join(lines), "Indentation error"
    elif bug_type == "missing_trigger" and "command /" in code:
        return code.replace("\ttrigger:", ""), "Missing trigger"
    elif bug_type == "wrong_op":
        if " is " in code:
            return code.replace(" is ", " == ", 1), "Wrong operator"
    elif bug_type == "event_value":
        if "on damage:" in code and "attacker" in code:
            return code.replace("attacker", "player"), "Wrong event value"
    return code, "No bug"


with open(MERGED_FILE, "r", encoding="utf-8") as f:
    merged_data = json.load(f)

dataset = []
target_addons_lower = [a.lower() for a in TARGET_ADDONS]

for item in merged_data:
    if item.get("addon", {}).get("name", "").lower() not in target_addons_lower:
        continue

    title = item.get("title", "")
    pattern = item.get("syntax_pattern", "")
    desc = item.get("description", "")
    examples = item.get("examples", [])

    valid_codes = set()
    for ex in examples:
        code = normalize_skript_tabs(ex.get("example_code", ""))
        if code and len(code) > 20:
            valid_codes.add(code)

    if pattern and desc:
        dataset.append(
            {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a Skript documentation AI. Provide concise syntax documentation.",
                    },
                    {
                        "role": "user",
                        "content": f"Explain the syntax for `{title}` in Skript.",
                    },
                    {
                        "role": "assistant",
                        "content": f"**Syntax:** `{pattern}`\n**Description:** {desc}",
                    },
                ]
            }
        )

    for code in list(valid_codes):
        plan_steps = []
        if "command /" in code:
            plan_steps.append("1. Define the command structure and permissions.")
        if "on " in code:
            plan_steps.append("2. Listen for the appropriate event.")
        if "if " in code:
            plan_steps.append("3. Check the required conditions.")
        if any(kw in code for kw in ["set ", "give ", "teleport ", "send "]):
            plan_steps.append("4. Apply the effect or action.")
        if not plan_steps:
            plan_steps.append("1. Implement the core Skript logic.")

        cot_response = (
            "**Plan:**\n"
            + "\n".join(plan_steps)
            + f"\n\n**Code:**\n```skript\n{code}\n```"
        )
        dataset.append(
            {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are an expert Skript developer. Always plan your approach step-by-step before writing code.",
                    },
                    {
                        "role": "user",
                        "content": f"I need a script for {title}. Think through the logic first, then write the code.",
                    },
                    {"role": "assistant", "content": cot_response},
                ]
            }
        )

        if random.random() < 0.4:
            broken_code, bug_desc = inject_advanced_bug(code)
            if broken_code != code:
                debug_response = f"**Bug Found:** {bug_desc}.\n\n**Fixed Code:**\n```skript\n{code}\n```"
                dataset.append(
                    {
                        "messages": [
                            {
                                "role": "system",
                                "content": "You are a Skript debugging expert. Identify the bug, explain it, and provide the fixed code.",
                            },
                            {
                                "role": "user",
                                "content": f"This Skript code doesn't work. Why?\n\n```skript\n{broken_code}\n```",
                            },
                            {"role": "assistant", "content": debug_response},
                        ]
                    }
                )

        if random.random() < 0.3:
            dataset.append(
                {
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a Skript optimization expert. Refactor the user's code to be more efficient. Output ONLY the improved code inside ```skript blocks.",
                        },
                        {
                            "role": "user",
                            "content": f"Optimize this Skript code for better performance:\n\n```skript\n{code}\n```",
                        },
                        {"role": "assistant", "content": f"```skript\n{code}\n```"},
                    ]
                }
            )

random.shuffle(dataset)
with open(DATASET_FILE, "w", encoding="utf-8") as f:
    json.dump(dataset, f, indent=2, ensure_ascii=False)
print(f"✅ Generated {len(dataset)} instruction pairs. Saved to {DATASET_FILE}")

import os
import json
import random
import re
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import TARGET_ADDONS, DATA_DIR, DATASET_FILE, MERGED_FILE

FORCE = "--force" in sys.argv

os.makedirs(DATA_DIR, exist_ok=True)

if not os.path.exists(MERGED_FILE) or FORCE:
    os.system("python scripts/merge_syntax_and_examples.py")
if os.path.exists(DATASET_FILE) and not FORCE:
    sys.exit(0)


def normalize_skript_tabs(code):
    if not code:
        return ""
    code = re.sub(r"^( {4}| {2})", "\t", code, flags=re.MULTILINE)
    return code.replace("\r\n", "\n").strip()


def _apply_indent_bug(code):
    lines = code.split("\n")
    nested = [i for i, line in enumerate(lines) if line.startswith("\t")]
    if not nested:
        return None
    idx = random.choice(nested)
    lines[idx] = lines[idx].replace("\t", "", 1)
    return "\n".join(lines), "Indentation error"


def _apply_missing_trigger(code):
    if "command /" in code and "\ttrigger:" in code:
        return code.replace("\ttrigger:", ""), "Missing trigger"
    return None


def _apply_wrong_op(code):
    if " is " in code:
        return code.replace(" is ", " == ", 1), "Wrong operator"
    return None


def _apply_event_value(code):
    if "on damage:" in code and "attacker" in code:
        return code.replace("attacker", "player", 1), "Wrong event value"
    return None


def _apply_missing_colon(code):
    m = re.search(r"^(\t[a-z ]+?):", code, flags=re.MULTILINE)
    if m:
        return code.replace(m.group(0), m.group(1), 1), "Missing colon in statement"
    return None


_BUG_GENERATORS = [
    _apply_indent_bug,
    _apply_missing_trigger,
    _apply_wrong_op,
    _apply_event_value,
    _apply_missing_colon,
]


def inject_advanced_bug(code):
    generators = list(_BUG_GENERATORS)
    random.shuffle(generators)
    for gen in generators:
        res = gen(code)
        if res:
            broken, desc = res
            if broken != code:
                return broken, desc
    return code, "No bug"


def optimize_code(code):
    """Apply a behavior-preserving refactor. Returns optimized code, or None
    if no safe refactor can be applied (so we never emit an identity sample)."""
    lines = code.split("\n")
    new_lines = []
    i = 0
    combined = False
    while i < len(lines):
        line = lines[i]
        m = re.match(r"^((\t)*)add (.+?) to (\{[^}]+\})$", line)
        if m:
            indent, _, expr, var = m.group(1), m.group(2), m.group(3), m.group(4)
            exprs = [expr]
            j = i + 1
            while j < len(lines):
                m2 = re.match(
                    r"^" + re.escape(indent) + r"add (.+?) to " + re.escape(var) + r"$",
                    lines[j],
                )
                if m2:
                    exprs.append(m2.group(1))
                    j += 1
                else:
                    break
            if len(exprs) > 1:
                new_lines.append(f"{indent}add {', '.join(exprs)} to {var}")
                combined = True
                i = j
                continue
        new_lines.append(line)
        i += 1
    if combined:
        return "\n".join(new_lines)
    return None


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
            optimized = optimize_code(code)
            if optimized and optimized != code:
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
                            {"role": "assistant", "content": f"```skript\n{optimized}\n```"},
                        ]
                    }
                )

random.shuffle(dataset)
with open(DATASET_FILE, "w", encoding="utf-8") as f:
    json.dump(dataset, f, indent=2, ensure_ascii=False)
print(f"✅ Generated {len(dataset)} instruction pairs. Saved to {DATASET_FILE}")

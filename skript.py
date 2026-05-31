import json
import random
import re

with open('syntax.json', 'r') as f:
    raw_data = json.load(f)

dataset = []
SKRIPT_CORE_ONLY = True  # Strictly core Skript
ALLOWED_TYPES = ['effect', 'condition', 'expression', 'event', 'function', 'section']

# Natural language instruction templates per syntax type
TEMPLATES = {
    'effect': [
        "Write a Skript effect to {desc}.",
        "How do I {desc} in Skript?",
        "Create a trigger that uses the {title} effect."
    ],
    'condition': [
        "Write an if-statement checking if {desc}.",
        "How to check {desc} in Skript?",
        "Create a condition for {title}."
    ],
    'expression': [
        "How do I get {desc} in Skript?",
        "Write a script that stores {title} in a variable.",
        "Show me how to use the {title} expression."
    ],
    'event': [
        "Write a Skript event handler for when {desc}.",
        "Create a script that listens to the {title} event.",
        "How do I detect {desc}?"
    ],
    'function': [
        "Write a Skript function that {desc}.",
        "How do I define a function for {title}?",
        "Create a reusable Skript function: {desc}"
    ],
    'section': [
        "Write a Skript section for {desc}.",
        "How do I use the {title} section in Skript?",
        "Create a code block using {title}."
    ]
}

def clean_syntax(pattern):
    """Converts regex-like Skript patterns into valid example code"""
    cleaned = re.sub(r'\[.*?\]', '', pattern)      # Remove optional groups
    cleaned = re.sub(r'\(.*?\)', '', cleaned)       # Remove alternative groups  
    cleaned = re.sub(r'%[^%]+%', '{value}', cleaned) # Replace type hints    cleaned = re.sub(r'<.+?>', '', cleaned)         # Remove regex capture groups
    return cleaned.strip() or "{value}"

for entry in raw_data:
    # STRICT FILTER: Only core Skript
    addon_name = entry.get('addon', {}).get('name', '')
    if SKRIPT_CORE_ONLY and addon_name != 'Skript':
        continue
        
    stype = entry.get('syntax_type', '')
    if stype not in ALLOWED_TYPES:
        continue
    
    title = entry.get('title', '')
    desc = entry.get('description', '').replace('\r\n', ' ').strip()
    syntax = clean_syntax(entry.get('syntax_pattern', ''))
    
    # Skip entries without meaningful descriptions
    if len(desc) < 10:
        desc = f"use the {title} syntax"
    
    # Generate natural language instruction
    template = random.choice(TEMPLATES.get(stype, TEMPLATES['expression']))
    instruction = template.format(desc=desc.lower(), title=title)
    
    # Build VALID Skript code with PROPER INDENTATION (tabs)
    if stype == 'event':
        response = f"on {syntax}:\n\t# TODO: Add your event logic here\n\tbroadcast \"Event triggered!\""
    elif stype == 'condition':
        response = f"if {syntax}:\n\t# Condition is true\n\tbroadcast \"Condition met!\"\nelse:\n\tbroadcast \"Condition not met!\""
    elif stype == 'effect':
        response = f"command /test:\n\ttrigger:\n\t\t{syntax}\n\t\tbroadcast \"Effect executed!\""
    elif stype == 'function':
        response = f"function {title}():\n\t# Function logic here\n\treturn {{_result}}"
    elif stype == 'section':
        response = f"{syntax}:\n\t# Section body\n\tbroadcast \"Section running!\""
    else:  # expression
        response = f"set {{_result}} to {syntax}\nbroadcast \"%{{_result}}%\""
    
    dataset.append({
        "instruction": instruction,
        "input": "",
        "output": response,
        "system": "You are a Skript expert. Always use tab indentation. Never invent syntax. Only use core Skript features unless an addon is explicitly requested.",
        "metadata": {"addon": "Skript", "type": stype}
    })

# Save Alpaca-format dataset
with open('skript_core_alpaca.json', 'w') as f:
    json.dump(dataset, f, indent=2)
print(f"✅ Generated {len(dataset)} CORE SKRIPT training pairs")
from collections import Counter
types = Counter(d['metadata']['type'] for d in dataset)
for t, c in types.most_common():
    print(f"   {t}: {c}")
import os

TARGET_ADDONS = ["Skript"]

DATA_DIR = "data"
MODELS_DIR = "models"

SYNTAX_FILE = os.path.join(DATA_DIR, "syntax.json")
RAW_EXAMPLES_FILE = os.path.join(DATA_DIR, "raw_examples.json")
MERGED_FILE = os.path.join(DATA_DIR, "syntax_with_examples.json")
DATASET_FILE = os.path.join(DATA_DIR, "skripton_dataset.json")

MODEL_NAME = "unsloth/Qwen2.5-1.5B-Instruct-unsloth-bnb-4bit"
MAX_SEQ_LENGTH = 1024
LORA_R = 32
LORA_ALPHA = 32

OUTPUT_DIR = os.path.join(MODELS_DIR, "lora_adapter")
MERGED_DIR = os.path.join(MODELS_DIR, "merged_16bit") 
GGUF_DIR = os.path.join(MODELS_DIR, "gguf")
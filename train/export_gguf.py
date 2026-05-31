import os
import sys
from google.colab import files

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MODEL_NAME, MAX_SEQ_LENGTH, OUTPUT_DIR, GGUF_DIR

from unsloth import FastLanguageModel

def main():
    os.makedirs(GGUF_DIR, exist_ok=True)

    print("🔄 Loading trained adapter...")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=OUTPUT_DIR,
        max_seq_length=MAX_SEQ_LENGTH,
        load_in_4bit=True,
    )

    print("💾 Converting to GGUF Q4_K_M...")
    model.save_pretrained_gguf(GGUF_DIR, tokenizer, quantization_method="q4_k_m")

    gguf_files = [f for f in os.listdir(GGUF_DIR) if f.endswith('.gguf')]
    if gguf_files:
        gguf_path = os.path.join(GGUF_DIR, gguf_files[0])
        print(f"✅ GGUF model ready: {gguf_path}")
        print("⬇️ Starting download...")
        files.download(gguf_path)
    else:
        print("❌ GGUF file not found.")

if __name__ == "__main__":
    main()
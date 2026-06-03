import os
import sys
import torch
import gc

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MODEL_NAME, OUTPUT_DIR, MERGED_DIR, GGUF_DIR

def main():
    from google.colab import files
    
    # 1. Setup llama.cpp scripts
    print("⬇️ Downloading llama.cpp python scripts...")
    if not os.path.exists("llama.cpp"):
        !git clone --depth 1 https://github.com/ggerganov/llama.cpp.git
    !pip install -r llama.cpp/requirements.txt -q

    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel

    BASE_MODEL = "Qwen/Qwen2.5-1.5B-Instruct" 

    print("🔄 Loading base model in 16-bit")
    model = AutoModelForCausalLM.from_pretrained(
        BASE_MODEL,
        device_map="auto",
        torch_dtype=torch.float16,
    )
    tokenizer = AutoTokenizer.from_pretrained(BASE_MODEL)

    print("🔄 Applying LoRA adapter...")
    model = PeftModel.from_pretrained(model, OUTPUT_DIR)


    print("🔄 Merging adapter into base model...")
    model = model.merge_and_unload()

    print(f"💾 Saving merged 16-bit model to {MERGED_DIR}...")
    os.makedirs(MERGED_DIR, exist_ok=True)
    model.save_pretrained(MERGED_DIR, safe_serialization=True)
    tokenizer.save_pretrained(MERGED_DIR)

    # Free up VRAM before the heavy GGUF conversion
    del model
    gc.collect()
    torch.cuda.empty_cache()

    print("💾 Converting to Q4_K_M GGUF format using llama.cpp python script...")
    os.makedirs(GGUF_DIR, exist_ok=True)
    !python llama.cpp/convert_hf_to_gguf.py {MERGED_DIR} --outfile models/gguf/skripton_qwen.gguf --outtype q4_k_m

    gguf_path = "models/gguf/skripton_qwen.gguf"
    if os.path.exists(gguf_path):
        print(f"✅ GGUF model ready: {gguf_path}")
        print("⬇️ Starting download to your local machine...")
        files.download(gguf_path)
    else:
        print("❌ GGUF file not found. Check the conversion logs above for errors.")

if __name__ == "__main__":
    main()
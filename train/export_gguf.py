import os
import sys
import torch
import gc

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MODEL_NAME, OUTPUT_DIR, MERGED_DIR, GGUF_DIR

ADAPTER_CONFIG = os.path.join(OUTPUT_DIR, "adapter_config.json")

if not os.path.exists(ADAPTER_CONFIG):
    os.system("python train/train.py")


def main():
    from google.colab import files

    # 1. Setup llama.cpp scripts
    print("⬇️ Downloading llama.cpp python scripts...")
    if not os.path.exists("llama.cpp"):
        os.system("git clone --depth 1 https://github.com/ggerganov/llama.cpp.git")
    os.system("uv pip install -r llama.cpp/requirements.txt -q")

    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel

    print("🔄 Loading base model in 16-bit")
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        device_map="auto",
        torch_dtype=torch.float16,
    )
    tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

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

    print("💾 Converting to F16 GGUF format using llama.cpp python script...")
    os.makedirs(GGUF_DIR, exist_ok=True)
    f16_path = os.path.join(GGUF_DIR, "skripton_qwen_f16.gguf")
    os.system(
        f"python llama.cpp/convert_hf_to_gguf.py {MERGED_DIR} --outfile {f16_path} --outtype f16"
    )

    gguf_path = os.path.join(GGUF_DIR, "skripton_qwen.gguf")
    if os.path.exists(f16_path):
        print("🔨 Building llama-quantize from llama.cpp...")
        os.system("cd llama.cpp && make -j llama-quantize 2>/dev/null || make llama-quantize")
        quantize_bin = "llama.cpp/build/bin/llama-quantize"
        if not os.path.exists(quantize_bin):
            quantize_bin = "llama.cpp/llama-quantize"
        print(f"🔄 Quantizing F16 GGUF to Q4_K_M: {gguf_path}")
        os.system(f"{quantize_bin} {f16_path} {gguf_path} q4_k_m")
    else:
        print("❌ F16 GGUF file not found. Check the conversion logs above for errors.")
        return

    if os.path.exists(gguf_path):
        print(f"✅ GGUF model ready: {gguf_path}")
        print("⬇️ Starting download to your local machine...")
        files.download(gguf_path)
    else:
        print("❌ GGUF file not found. Check the conversion logs above for errors.")


if __name__ == "__main__":
    main()

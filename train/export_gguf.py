import os
import sys
import torch
import gc

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import MODEL_NAME, OUTPUT_DIR, MERGED_DIR, GGUF_DIR

ADAPTER_CONFIG = os.path.join(OUTPUT_DIR, "adapter_config.json")


def main():
    from google.colab import files
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from peft import PeftModel

    # 0. Train first if the adapter is missing
    if not os.path.exists(ADAPTER_CONFIG):
        os.system("python train/train.py")

    # 1. Set up llama.cpp (clone + python deps)
    print("⬇️ Setting up llama.cpp...")
    if not os.path.exists("llama.cpp"):
        os.system("git clone --depth 1 https://github.com/ggerganov/llama.cpp.git")
    os.system("uv pip install -r llama.cpp/requirements.txt -q")

    # 2. Merge the LoRA adapter into the base model (skip if already merged)
    merged_model_file = os.path.join(MERGED_DIR, "model.safetensors")
    if not os.path.exists(merged_model_file):
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

        # Free VRAM before the heavy conversion steps
        del model
        gc.collect()
        torch.cuda.empty_cache()
    else:
        print(f"✅ Reusing existing merged model at {MERGED_DIR}")

    # 3. Convert merged 16-bit -> F16 GGUF (skip if already converted)
    os.makedirs(GGUF_DIR, exist_ok=True)
    f16_path = os.path.join(GGUF_DIR, "skripton_qwen_f16.gguf")
    if not os.path.exists(f16_path):
        print("💾 Converting to F16 GGUF format using llama.cpp python script...")
        os.system(
            f"python llama.cpp/convert_hf_to_gguf.py {MERGED_DIR} --outfile {f16_path} --outtype f16"
        )
    else:
        print(f"✅ Reusing existing F16 GGUF at {f16_path}")

    # 4. Build llama-quantize via cmake and quantize F16 -> Q4_K_M
    q4_path = os.path.join(GGUF_DIR, "skripton_qwen.gguf")
    if not os.path.exists(f16_path):
        print("❌ F16 GGUF file not found. Check the conversion logs above for errors.")
        return

    quantize_bin = "llama.cpp/build/bin/llama-quantize"
    if not os.path.exists(quantize_bin):
        print("🔨 Building llama-quantize via cmake...")
        os.system("cmake -B llama.cpp/build -S llama.cpp -DGGML_CUDA=OFF")
        os.system("cmake --build llama.cpp/build --config Release -j 4 --target llama-quantize")
    if not os.path.exists(quantize_bin):
        quantize_bin = "llama.cpp/llama-quantize"

    print(f"🔄 Quantizing F16 GGUF to Q4_K_M: {q4_path}")
    rc = os.system(f"{quantize_bin} {f16_path} {q4_path} q4_k_m")
    if rc != 0 or not os.path.exists(q4_path):
        print("❌ Quantization failed. Check the logs above for errors.")
        return

    print(f"✅ GGUF model ready: {q4_path}")
    print("⬇️ Starting download to your local machine...")
    files.download(q4_path)


if __name__ == "__main__":
    main()

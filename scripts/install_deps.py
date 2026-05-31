import subprocess
import sys

def install_dependencies():
    print("⏳ Installing Skripton dependencies for Google Colab...")
    print("⚠️ Ignoring dependency conflicts to preserve Colab's PyTorch version.\n")
    
    # Order matters here to ensure Unsloth gets its specific dependencies first
    commands = [
        # Core NLP/Training dependencies (installed with --no-deps to prevent Colab torch downgrade)
        [sys.executable, "-m", "pip", "install", "--no-deps", "trl", "peft", "accelerate"],
        [sys.executable, "-m", "pip", "install", "--no-deps", "bitsandbytes"],
        [sys.executable, "-m", "pip", "install", "--no-deps", "xformers==0.0.27.post2"],
        [sys.executable, "-m", "pip", "install", "--no-deps", "datasets"],
        
        # Unsloth (must be installed from GitHub source for Colab)
        [sys.executable, "-m", "pip", "install", "--no-deps", "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"],
        
        # Scraping dependencies (allow dependencies for requests, it's safe)
        [sys.executable, "-m", "pip", "install", "requests"],
    ]

    for cmd in commands:
        package_name = " ".join(cmd[-2:]) # Extract name for logging
        print(f"-> Installing {package_name}...")
        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"   ✅ Success")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Failed to install {package_name}")
            print(f"   Error: {e}")
            sys.exit(1)
            
    print("\n✅ All dependencies installed successfully!")

if __name__ == "__main__":
    install_dependencies()
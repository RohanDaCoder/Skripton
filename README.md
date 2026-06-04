# Skripton

A LLM fine-tuned to code professional skripts
Can be easily ran in **Google Colab**

## Colab Pipeline (Single cell)

This advanced pipeline pulls latest changes when ran, installs required dependencies, runs it's needed scripts then runs the fine-tuning setup.

```py
from os import path

REPO_URL = "https://github.com/RohanDaCoder/Skripton.git"
REPO_DIR = "Skripton"

%cd /content

if path.exists(f"{REPO_DIR}/.git"):
    print("🔄 Repository found. Force-syncing latest code from GitHub...")
    !git -C {REPO_DIR} fetch origin
    !git -C {REPO_DIR} reset --hard origin/main
    print("✅ Code updated successfully.")
else:
    if path.exists(REPO_DIR):
        !rm -rf {REPO_DIR}
    print(f"⬇️ Repository not found. Cloning fresh from {REPO_URL}...")
    !git clone {REPO_URL}
    print("✅ Clone complete.")

%cd {REPO_DIR}

!bash scripts/install_deps.sh

!python scripts/synthesize_dataset.py

!python train/train.py

!python train/export_gguf.py
```

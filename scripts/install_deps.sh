curl -LsSf https://astral.sh/uv/install.sh | sh &> /dev/null
echo "⏳ Installing Skripton dependencies for Google Colab..."
uv pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git" &> /dev/null
uv pip install "transformers>=4.46.0,<4.50.0" &> /dev/null
uv pip install --no-deps unsloth_zoo &> /dev/null
uv pip install --no-deps bitsandbytes xformers==0.0.27.post2 &> /dev/null
uv pip install peft accelerate trl datasets &> /dev/null
uv pip install --upgrade torchao &> /dev/null

echo "✅ All dependencies installed successfully!"
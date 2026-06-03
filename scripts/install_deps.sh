%%bash
curl -LsSf https://astral.sh/uv/install.sh | sh &> /dev/null
echo "⏳ Installing Skripton dependencies for Google Colab..."
uv pip install -U torchao &> /dev/null
uv pip install --no-deps "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git" &> /dev/null
uv pip install unsloth_zoo &> /dev/null
uv pip install --no-deps bitsandbytes xformers==0.0.27.post2 datasets &> /dev/null

echo "✅ All dependencies installed successfully!"
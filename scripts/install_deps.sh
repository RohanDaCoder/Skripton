%%bash
curl -LsSf https://astral.sh/uv/install.sh | sh
echo "⏳ Installing Skripton dependencies for Google Colab..."
uv pip install -U torchao 
uv pip install --no-deps "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git" 
uv pip install unsloth_zoo 
uv pip install --no-deps bitsandbytes xformers==0.0.27.post2 datasets 

echo "✅ All dependencies installed successfully!"
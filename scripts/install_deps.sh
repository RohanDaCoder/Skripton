#!/bin/bash
set -e

echo "⏳ Installing Skripton dependencies for Google Colab..."

echo "-> Fixing torchao for PEFT compatibility..."
pip install -U torchao

echo "-> Installing Unsloth..."
pip install --no-deps "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"

echo "-> Installing Unsloth Zoo (this will fix transformers, trl, and datasets versions)..."
# Removed --no-deps here so unsloth_zoo can automatically install/fix its required versions
pip install unsloth_zoo

echo "-> Installing bitsandbytes..."
pip install --no-deps bitsandbytes

echo "-> Installing xformers==0.0.27.post2..."
pip install --no-deps xformers==0.0.27.post2

echo "-> Installing requests..."
pip install requests

echo "✅ All dependencies installed successfully!"

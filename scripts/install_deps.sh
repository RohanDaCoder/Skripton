#!/bin/bash
set -e

echo "⏳ Installing Skripton dependencies for Google Colab..."

echo "-> Upgrading torchao for PEFT compatibility..."
pip install -U torchao

echo "-> Installing trl peft accelerate..."
pip install --no-deps trl peft accelerate

echo "-> Installing bitsandbytes..."
pip install --no-deps bitsandbytes

echo "-> Installing xformers==0.0.27.post2..."
pip install --no-deps xformers==0.0.27.post2

echo "-> Installing datasets..."
pip install --no-deps datasets

echo "-> Installing unsloth_zoo..."
pip install --no-deps unsloth_zoo

echo "-> Installing unsloth..."
pip install --no-deps "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"

echo "-> Installing requests..."
pip install requests

echo "✅ All dependencies installed successfully!"
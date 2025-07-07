#!/bin/bash

echo "🧹 Clean Installation of Dependencies"
echo "===================================="

# Upgrade pip first
echo "📦 Upgrading pip..."
pip install --upgrade pip

# Remove conflicting packages
echo "🗑️  Removing old packages..."
pip uninstall -y google-adk google-genai google-generativeai openinference-instrumentation-google-adk

# Install all dependencies fresh
echo "📥 Installing all dependencies..."
pip install -r requirements.txt

# Show installed versions
echo ""
echo "✅ Installed versions:"
echo "-------------------"
pip show google-adk | grep -E "Name:|Version:"
pip show google-genai | grep -E "Name:|Version:"
pip show google-generativeai | grep -E "Name:|Version:"
pip show openinference-instrumentation-google-adk | grep -E "Name:|Version:"

echo ""
echo "🎉 Installation complete!"
echo ""
echo "⚠️  IMPORTANT: Check if your code still works with the updated packages."
echo "   The google-genai update from 1.16.1 to 1.17.0+ might have breaking changes."
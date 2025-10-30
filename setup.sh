#!/bin/bash
# Setup script for Video Validator

echo "======================================================"
echo "Video Validator - Setup Script"
echo "======================================================"
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    echo "Please install Python 3.8 or later"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"

# Check if FFmpeg is installed
if ! command -v ffmpeg &> /dev/null; then
    echo ""
    echo "⚠️  FFmpeg is not installed"
    echo ""
    echo "Please install FFmpeg:"
    echo "  Ubuntu/Debian: sudo apt update && sudo apt install ffmpeg"
    echo "  macOS: brew install ffmpeg"
    echo "  Windows: Download from https://ffmpeg.org/download.html"
    echo ""
    read -p "Do you want to try installing FFmpeg now? (Ubuntu/Debian only) [y/N] " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        sudo apt update && sudo apt install ffmpeg -y
    else
        echo "Please install FFmpeg manually and run this script again"
        exit 1
    fi
fi

echo "✓ FFmpeg found: $(ffmpeg -version | head -n1)"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Run tests
echo ""
echo "Running setup tests..."
python test_setup.py

echo ""
echo "======================================================"
echo "Setup complete!"
echo "======================================================"
echo ""
echo "To start the application:"
echo "  1. Activate virtual environment: source venv/bin/activate"
echo "  2. Run the app: python app.py"
echo "  3. Open browser: http://127.0.0.1:8050"
echo ""
echo "Or use the CLI:"
echo "  python cli.py <video_file>"
echo ""

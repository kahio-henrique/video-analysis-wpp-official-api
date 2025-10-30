# Video Validator for WhatsApp API

A clean, minimalist tool to validate and convert videos for WhatsApp Business API compliance.

## Features

- ✓ **Validate** videos against WhatsApp API requirements
- ✓ **Convert** non-compliant videos to the correct format
- ✓ **Quick Fix** for moov atom positioning (no re-encoding)
- ✓ **Multi-language** support (English, Portuguese, Spanish)
- ✓ **Drag & Drop** interface

## Quick Start

### Prerequisites

1. **Python 3.8+**
2. **FFmpeg** - [Download here](https://ffmpeg.org/download.html)

**Install FFmpeg:**

```bash
# macOS
brew install ffmpeg

# Windows (with Chocolatey)
choco install ffmpeg

# Linux (Ubuntu/Debian)
sudo apt install ffmpeg
```

### Installation

```bash
# Clone repository
git clone https://github.com/kahio-henrique/video-analysis-wpp-official-api.git
cd video-analysis-wpp-official-api

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run application
python app.py
```

Open your browser to **http://127.0.0.1:8050**

## WhatsApp API Requirements

| Requirement | Value |
|------------|-------|
| Video Codec | H.264 (Baseline or Main) |
| Level | 3.0 (max 3.1) |
| Audio Codec | AAC-LC |
| Container | MP4 or 3GP |
| Max Size | 16 MB |
| Pixel Format | yuv420p |
| Progressive | moov atom at beginning |

## Usage

### Web Interface

1. Upload a video file (drag & drop or click)
2. Click **Validate** to check compliance
3. If needed:
   - **Convert & Fix**: Full conversion with re-encoding
   - **Quick Fix**: Only fix moov atom (fast, no re-encoding)

### Command Line

```bash
# Validate
python cli.py video.mp4

# Convert
python cli.py video.mp4 --convert

# Quick fix moov atom
python cli.py video.mp4 --quick-fix
```

## What is the moov atom?

The **moov atom** is metadata in MP4 files. WhatsApp requires it at the **beginning** of the file for:
- Fast preview generation
- Instant playback
- Better user experience

**Quick Fix** moves the moov atom without re-encoding (fast), while **Convert & Fix** re-encodes the entire video (slower but fixes all issues).

## Project Structure

```
video-analysis-wpp-official-api/
├── app.py                 # Web application
├── video_validator.py     # Validation logic
├── video_converter.py     # Conversion logic
├── cli.py                 # Command-line interface
├── requirements.txt       # Dependencies
└── uploads/              # Temporary upload folder
```

## Troubleshooting

**FFmpeg not found:**
```
Install FFmpeg and restart your terminal/IDE
```

**Module not found:**
```bash
pip install -r requirements.txt
```

**Video too large after conversion:**
```
The tool optimizes bitrate automatically, but very long videos may still exceed 16 MB. Consider trimming the video first.
```

## Contributing

Contributions welcome! Feel free to open issues or pull requests.

## License

MIT License

## Links

- **Repository**: https://github.com/kahio-henrique/video-analysis-wpp-official-api
- **FFmpeg**: https://ffmpeg.org/
- **WhatsApp API Docs**: https://developers.facebook.com/docs/whatsapp

---

Built with [Dash](https://dash.plotly.com/) and [FFmpeg](https://ffmpeg.org/)

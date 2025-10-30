# Video Validator & Converter for WhatsApp API

A powerful Python-based tool for validating and converting video files to meet WhatsApp Business API specifications. Similar to Advalify's Video Validator, this tool provides comprehensive video analysis with a focus on the critical **moov atom** location detection.

## Features

### Video Validation

- **Video Codec**: Validates H.264 (AVC) with Baseline or Main profile
- **Codec Level**: Checks for Level 3.0 (recommended) or maximum 3.1
- **Audio Codec**: Validates AAC-LC (Low Complexity)
- **Container Format**: Supports MP4 and 3GP
- **File Size**: Enforces 16 MB maximum limit
- **Audio Streams**: Validates single stream or none
- **Pixel Format**: Checks for yuv420p (4:2:0 chroma subsampling)
- **Progressive Download**: Detects moov atom location for fast start capability

### Video Conversion

- **Full Conversion**: Converts any video to WhatsApp-compliant format
- **Quick Fix**: Fast moov atom repositioning without re-encoding
- **Size Optimization**: Automatically adjusts bitrate to meet size requirements
- **Quality Preservation**: Uses optimal encoding settings

### User Interface

- **Drag & Drop Upload**: Easy file upload interface
- **Real-time Validation**: Instant feedback on video compliance
- **Detailed Reports**: Comprehensive validation results with pass/fail indicators
- **One-Click Conversion**: Simple conversion and fixing options

## Quick Start

The fastest way to get started:

```bash
# 1. Clone the repository
git clone <repository-url>
cd video-analysis-wpp-official-api

# 2. Run the setup script (Linux/macOS)
./setup.sh

# 3. Start the application
source venv/bin/activate
python app.py

# 4. Open your browser to http://127.0.0.1:8050
```

**Or use the CLI:**
```bash
python cli.py video.mp4                # Validate
python cli.py video.mp4 --convert      # Convert
python cli.py video.mp4 --quick-fix    # Quick fix
```

## Prerequisites

Before running the application, ensure you have the following installed:

1. **Python 3.8+**
   ```bash
   python3 --version
   ```

2. **FFmpeg** (required for video processing)

   **On Ubuntu/Debian:**
   ```bash
   sudo apt update
   sudo apt install ffmpeg
   ```

   **On macOS:**
   ```bash
   brew install ffmpeg
   ```

   **On Windows:**
   - Download from [ffmpeg.org](https://ffmpeg.org/download.html)
   - Add to system PATH

   **Verify installation:**
   ```bash
   ffmpeg -version
   ```

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd video-analysis-wpp-official-api
   ```

2. **Create a virtual environment** (recommended)
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

## Usage

### Starting the Application

1. **Run the application**
   ```bash
   python app.py
   ```

2. **Open your browser**
   ```
   http://127.0.0.1:8050
   ```

3. **Upload and validate videos**
   - Drag and drop a video file or click to browse
   - Click "Validate Video" to check compliance
   - Use "Fix & Convert Video" for full conversion
   - Use "Quick Fix" to only reposition the moov atom

### Command Line Usage

You can also use the validator and converter programmatically:

**Validate a video:**
```python
from video_validator import VideoValidator

validator = VideoValidator('path/to/video.mp4')
results = validator.validate_all()

print(f"Is valid: {results['is_valid']}")
for name, validation in results['validations'].items():
    print(f"{name}: {validation['message']}")
```

**Convert a video:**
```python
from video_converter import VideoConverter

converter = VideoConverter('input.mp4', 'output.mp4')
result = converter.convert()

if result['success']:
    print(f"Success! Output: {result['output_path']}")
else:
    print(f"Failed: {result['message']}")
```

**Quick fix moov atom:**
```python
from video_converter import VideoConverter

converter = VideoConverter('input.mp4', 'output.mp4')
result = converter.fix_moov_atom()

if result['success']:
    print("moov atom fixed!")
```

## Understanding the moov Atom

The **moov atom** (or "movie atom") is a critical component of MP4 files that contains metadata about the video:

- **At the end**: Normal encoding places it at the end (requires full download before playback)
- **At the beginning**: Progressive download/fast start (playback can begin immediately)

### Why It Matters for WhatsApp

WhatsApp requires the moov atom at the beginning for:
- Faster video preview generation
- Better user experience with instant playback
- Reduced server load
- Compliance with progressive download requirements

### How This Tool Handles It

1. **Detection**: Scans the MP4 file structure to locate the moov atom
2. **Validation**: Checks if it's within the first ~10KB (optimal position)
3. **Fixing**: Two options:
   - **Quick Fix**: Repositions moov atom without re-encoding (fast)
   - **Full Conversion**: Re-encodes with optimized settings (comprehensive)

## WhatsApp API Video Requirements

| Requirement | Specification |
|------------|---------------|
| Video Codec | H.264 (AVC) |
| Video Profile | Baseline or Main |
| Codec Level | 3.0 (max 3.1) |
| Audio Codec | AAC-LC (Low Complexity) |
| Container | MP4 or 3GP |
| Max File Size | 16 MB |
| Audio Streams | 0 or 1 |
| Pixel Format | yuv420p (4:2:0) |
| Progressive | moov atom at beginning |

## Project Structure

```
video-analysis-wpp-official-api/
├── app.py                  # Main Dash application
├── video_validator.py      # Video validation logic
├── video_converter.py      # Video conversion/fixing logic
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── .gitignore             # Git ignore rules
└── uploads/               # Temporary upload directory (created automatically)
```

## Troubleshooting

### FFmpeg not found
```
Error: ffmpeg command not found
```
**Solution**: Install FFmpeg and ensure it's in your system PATH

### Module not found
```
ModuleNotFoundError: No module named 'dash'
```
**Solution**: Install dependencies with `pip install -r requirements.txt`

### Permission denied on uploads folder
**Solution**: Ensure the application has write permissions in the directory

### Video too large after conversion
**Solution**: The tool automatically optimizes bitrate, but very long videos may still exceed 16 MB. Consider trimming the video first.

## Technical Details

### Video Processing Pipeline

1. **Upload**: File saved to uploads directory
2. **Analysis**: FFprobe extracts video metadata
3. **Validation**: Each requirement checked against specifications
4. **Conversion** (if needed):
   - Video: H.264 encoding with Main profile, Level 3.0
   - Audio: AAC-LC encoding with optimized bitrate
   - Container: MP4 with faststart flag (moov at beginning)
5. **Verification**: Converted file validated automatically

### Conversion Settings

```
Video:
- Codec: libx264 (H.264)
- Profile: Main
- Level: 3.0
- Pixel Format: yuv420p
- Preset: slow (better compression)
- CRF: 23 (quality)

Audio:
- Codec: AAC (aac_low profile)
- Channels: 1 (mono, saves space)
- Sample Rate: 44100 Hz
- Bitrate: 64 kbps

Container:
- Format: MP4
- Flags: faststart (moov atom at beginning)
```

## Performance

- **Validation**: < 1 second for most videos
- **Quick Fix**: 1-5 seconds (no re-encoding)
- **Full Conversion**: Depends on video length and system specs
  - Example: ~30 seconds for a 10 MB video on modern hardware

## API Integration

This tool can be extended to work with the WhatsApp Business API:

1. **Pre-upload validation**: Validate before sending to WhatsApp
2. **Automatic conversion**: Convert non-compliant videos
3. **Batch processing**: Process multiple videos
4. **API endpoint**: Expose as REST API for integration

## Contributing

Contributions are welcome! Areas for improvement:

- Add batch processing support
- Implement REST API endpoints
- Add video trimming functionality
- Support additional formats
- Improve conversion speed
- Add detailed analytics

## License

MIT License - feel free to use and modify for your needs.

## Support

For issues, questions, or contributions:
1. Check the troubleshooting section
2. Review FFmpeg documentation
3. Open an issue on GitHub

## Acknowledgments

- Built with [Dash](https://dash.plotly.com/) by Plotly
- Video processing powered by [FFmpeg](https://ffmpeg.org/)
- Inspired by [Advalify's Video Validator](https://www.advalify.io/video-validator)

---

**Happy validating!** If you find this tool useful, please star the repository.

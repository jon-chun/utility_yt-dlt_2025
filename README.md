# Video Downloader Toolkit

A comprehensive Python toolkit for downloading videos from YouTube, IBM Video, and other platforms using yt-dlp. Features intelligent format detection, anti-bot bypass techniques, and optimized configurations for AI research workflows.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![yt-dlp](https://img.shields.io/badge/yt--dlp-2025.12+-green.svg)](https://github.com/yt-dlp/yt-dlp)

---

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [YouTube Downloader](#youtube-downloader-get_yt-video-by-idpy)
- [IBM Video Downloader](#ibm-video-downloader)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Testing](#testing)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

---

## Features

- **YouTube Downloads** with anti-bot bypass (January 2026 compatible)
- **IBM Video/HLS Stream Support** with automatic format detection
- **Configurable Quality/Size** presets (low/medium/high)
- **Automatic Subtitle Download** with language selection
- **Thumbnail Extraction** for video previews
- **Browser Impersonation** via curl_cffi to avoid 403 errors
- **JavaScript Challenge Solving** via Deno runtime
- **Comprehensive Logging** with debug levels
- **AI Research Ready** with batch processing support

---

## Prerequisites

### Required

| Component | Version | Purpose |
|-----------|---------|---------|
| Python | 3.10+ | Runtime environment |
| yt-dlp | 2025.11+ | Core download engine |
| Deno | 2.0+ | YouTube JS challenge solving |
| FFmpeg | 4.0+ | Video merging and conversion |

### Optional (Recommended)

| Component | Version | Purpose |
|-----------|---------|---------|
| curl_cffi | 0.11-0.13 | Browser impersonation for 403 bypass |

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/jon-chun/utility_yt-dlt_2025.git
cd utility_yt-dlt_2025
```

### 2. Create Virtual Environment

Using [uv](https://github.com/astral-sh/uv) (recommended):
```bash
uv venv --python=3.12
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows
```

Or using standard venv:
```bash
python -m venv .venv
source .venv/bin/activate
```

### 3. Install Python Dependencies

```bash
# Using uv (faster)
uv pip install -r requirements.txt
uv pip install "curl_cffi>=0.11,<0.14"  # For impersonation

# Or using pip
pip install -r requirements.txt
pip install "curl_cffi>=0.11,<0.14"
```

### 4. Install Deno (Required for YouTube)

**macOS:**
```bash
brew install deno
```

**Linux:**
```bash
curl -fsSL https://deno.land/install.sh | sh
```

**Windows:**
```powershell
winget install --id=DenoLand.Deno
```

### 5. Install FFmpeg

**macOS:**
```bash
brew install ffmpeg
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update && sudo apt install ffmpeg
```

**Windows:**
```powershell
winget install --id=Gyan.FFmpeg
```

### 6. Verify Installation

```bash
# Check all components
python --version          # Should be 3.10+
deno --version           # Should be 2.0+
ffmpeg -version          # Should be 4.0+
python -c "import yt_dlp; print(yt_dlp.version.__version__)"  # Should be 2025.11+
```

---

## Quick Start

### YouTube Video (Simplest)

```bash
# Download with defaults (low quality, 360p, English subtitles)
python get_yt-video-by-id.py L7gv9aGB7VY

# Higher quality
python get_yt-video-by-id.py L7gv9aGB7VY -q high -s high
```

### IBM Video

```bash
# Download IBM Video stream
python get_ibm_yt-dlt_gpt5_working_20251006.py https://video.ibm.com/recorded/134516112
```

---

## YouTube Downloader (`get_yt-video-by-id.py`)

A streamlined YouTube downloader with configurable quality and size presets, designed to bypass YouTube's anti-bot measures (updated January 2026).

### Usage

```bash
python get_yt-video-by-id.py [VIDEO_ID] [OPTIONS]
```

### Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `VIDEO_ID` | YouTube video ID (e.g., `dQw4w9WgXcQ`) | `L7gv9aGB7VY` |

### Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--quality` | `-q` | Video quality preset | `low` |
| `--size` | `-s` | Resolution size preset | `low` |
| `--language` | `-l` | Subtitle language code | `en` |
| `--output-dir` | `-o` | Output directory | `./downloads` |
| `--list-formats` | | List available formats | - |
| `--cookies` | | Use Chrome cookies (age-restricted) | - |

### Quality/Size Matrix

| Quality | Size | Max Resolution | Use Case |
|---------|------|----------------|----------|
| `low` | `low` | 360p | Mobile, bandwidth-limited |
| `low` | `medium` | 480p | Standard definition |
| `low` | `high` | 720p | Good quality, moderate size |
| `medium` | `low` | 480p | Balanced |
| `medium` | `medium` | 720p | **Recommended default** |
| `medium` | `high` | 1080p | HD quality |
| `high` | `low` | 720p | Quality-focused |
| `high` | `medium` | 1080p | High definition |
| `high` | `high` | Best | Maximum available quality |

### Examples

```bash
# Download in 720p HD
python get_yt-video-by-id.py dQw4w9WgXcQ -q medium -s medium

# Download in 1080p with Spanish subtitles
python get_yt-video-by-id.py dQw4w9WgXcQ -q high -s high -l es

# Download age-restricted content (requires Chrome login)
python get_yt-video-by-id.py RESTRICTED_ID --cookies

# List available formats before downloading
python get_yt-video-by-id.py dQw4w9WgXcQ --list-formats

# Custom output directory
python get_yt-video-by-id.py dQw4w9WgXcQ -o ./my_videos
```

### Output Files

For each downloaded video, the following files are created:

```
downloads/
├── Video Title.mp4          # Video file (merged video+audio)
├── Video Title.en.vtt       # Subtitles (VTT format)
└── Video Title.webp         # Thumbnail image
```

---

## IBM Video Downloader

Advanced downloader for IBM Video (video.ibm.com) HLS streams with comprehensive diagnostics and format detection.

### Primary Script

```bash
python get_ibm_yt-dlt_gpt5_working_20251006.py [URL] [OPTIONS]
```

### Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--output-dir` | `-o` | Output directory | `./downloads` |
| `--quality` | `-q` | Quality (`480p`, `720p`, `1080p`, `best`) | `best` |
| `--format` | `-f` | Container (`mp4`, `webm`, `mkv`) | `mp4` |
| `--info-only` | | Extract info without downloading | - |
| `--list-formats` | | List available formats | - |
| `--diagnostics` | | Run comprehensive diagnostics | - |
| `--debug-level` | | Debug level (`none`, `min`, `max`) | `max` |
| `--fix-audio` | | Force video+audio combination | - |
| `--cookies` | | Path to cookies.txt file | - |
| `--cookies-from-browser` | | Browser to extract cookies from | - |

### Examples

```bash
# Download with automatic format detection
python get_ibm_yt-dlt_gpt5_working_20251006.py

# Run diagnostics first
python get_ibm_yt-dlt_gpt5_working_20251006.py --diagnostics

# Download specific URL with 720p quality
python get_ibm_yt-dlt_gpt5_working_20251006.py https://video.ibm.com/recorded/134516112 -q 720p

# Use browser cookies for restricted content
python get_ibm_yt-dlt_gpt5_working_20251006.py --cookies-from-browser chrome
```

---

## Configuration

### Environment Configuration (`config.json`)

```json
{
  "output_dir": "./downloads",
  "output_template": "%(uploader)s - %(title)s.%(ext)s",
  "format_selector": "best[height<=1080][ext=mp4]/best[ext=mp4]/best",
  "video_quality": "best",
  "extract_subtitles": true,
  "download_thumbnail": true,
  "retries": 3,
  "fragment_retries": 5,
  "concurrent_fragments": 4,
  "merge_output_format": "mp4"
}
```

### Programmatic Usage

```python
from get_yt_video_by_id import download_video

# Simple download
success = download_video(
    video_id='L7gv9aGB7VY',
    quality='medium',
    size='high',
    language='en',
    output_dir='./research_data'
)

# Batch processing
video_ids = ['id1', 'id2', 'id3']
for vid in video_ids:
    download_video(vid, quality='low', size='low')
```

---

## Troubleshooting

### YouTube: "403 Forbidden" Error

**Cause:** YouTube's anti-bot detection blocking requests.

**Solutions:**
1. Ensure Deno is installed: `deno --version`
2. Ensure curl_cffi is installed: `pip install "curl_cffi>=0.11,<0.14"`
3. Update yt-dlp: `pip install -U yt-dlp`

### YouTube: "Sign in to confirm you're not a bot"

**Cause:** YouTube requires authentication for certain content.

**Solution:**
```bash
python get_yt-video-by-id.py VIDEO_ID --cookies
```

### YouTube: "n challenge solving failed"

**Cause:** Missing JavaScript runtime or EJS components.

**Solutions:**
1. Install Deno: `brew install deno` (macOS) or equivalent
2. The script automatically downloads EJS components from GitHub

### IBM Video: "Requested format is not available"

**Solution:**
```bash
# Check available formats first
python get_ibm_yt-dlt_gpt5_working_20251006.py --list-formats

# Use best available
python get_ibm_yt-dlt_gpt5_working_20251006.py -q best
```

### QuickTime Player Compatibility

HLS-converted videos may not play in QuickTime. Use VLC or mpv instead:
```bash
# macOS
brew install vlc
vlc "downloads/video.mp4"

# Or convert with FFmpeg
ffmpeg -i input.mp4 -c copy -movflags +faststart output.mp4
```

### General: Network Timeouts

```bash
# Enable verbose logging to diagnose
python get_yt-video-by-id.py VIDEO_ID -v

# The scripts have automatic retry logic (5 retries by default)
```

---

## Testing

### Run Unit Tests

```bash
# Install pytest
pip install pytest

# Run all tests
pytest test_get_yt_video.py -v

# Run specific test class
pytest test_get_yt_video.py::TestFormatSelector -v
```

### Test Coverage

The test suite includes:
- Resolution limit validation (9 tests)
- Format selector generation (6 tests)
- Download function behavior (6 tests)
- Integration tests (1 test, requires network)

---

## Project Structure

```
utility_yt-dlt_2025/
├── get_yt-video-by-id.py              # YouTube downloader (Jan 2026)
├── get_ibm_yt-dlt_gpt5_working_20251006.py  # IBM Video downloader
├── test_get_yt_video.py               # Test suite
├── config.json                        # Default configuration
├── requirements.txt                   # Python dependencies
├── CLAUDE.md                          # AI assistant guidance
├── README.md                          # This file
├── downloads/                         # Default output directory
│   └── logs/                          # Download logs
└── docs/
    └── chat_notes.md                  # Development notes
```

### Script Variants

| Script | Description |
|--------|-------------|
| `get_yt-video-by-id.py` | **Primary** - YouTube downloader with 2026 anti-bot fixes |
| `get_ibm_yt-dlt_gpt5_working_20251006.py` | **Primary** - IBM Video HLS downloader |
| `get_ibm_yt-dlt_claude45_20251006.py` | Claude variant (experimental) |
| `get_ibm_yt-dlt_grok4_20251006.py` | Grok variant (experimental) |

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `pytest test_get_yt_video.py -v`
5. Commit: `git commit -m 'Add amazing feature'`
6. Push: `git push origin feature/amazing-feature`
7. Open a Pull Request

---

## Dependencies

### Core
- **yt-dlp** >= 2025.11.12 - Video downloading engine
- **requests** >= 2.31.0 - HTTP requests
- **Deno** >= 2.0 - JavaScript runtime for YouTube challenges

### Optional
- **curl_cffi** 0.11-0.13 - Browser impersonation
- **ffmpeg-python** >= 0.2.0 - Video post-processing
- **pytest** >= 8.0 - Testing framework

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - The backbone of this toolkit
- [Deno](https://deno.land/) - JavaScript runtime enabling YouTube downloads
- [curl_cffi](https://github.com/yifeikong/curl_cffi) - Browser impersonation library

---

## Support

- **Issues**: [GitHub Issues](https://github.com/jon-chun/utility_yt-dlt_2025/issues)
- **Discussions**: [GitHub Discussions](https://github.com/jon-chun/utility_yt-dlt_2025/discussions)

---

**Last Updated:** January 2026

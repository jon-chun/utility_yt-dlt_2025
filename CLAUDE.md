# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

IBM Video Downloader - a Python utility for downloading videos from IBM Video (video.ibm.com) and other platforms using yt-dlp. Designed for AI research workflows with HLS stream support, comprehensive logging, and intelligent format detection.

## Common Commands

```bash
# Setup
uv venv --python=3.12
source .venv/bin/activate
uv add -r requirements.txt

# Basic download (uses default IBM video URL)
python get_ibm_yt-dlt_gpt5_working_20251006.py

# Download with custom URL
python get_ibm_yt-dlt_gpt5_working_20251006.py https://video.ibm.com/recorded/VIDEO_ID

# Run diagnostics (check URL accessibility, formats, HLS detection)
python get_ibm_yt-dlt_gpt5_working_20251006.py --diagnostics

# List available formats
python get_ibm_yt-dlt_gpt5_working_20251006.py --list-formats

# Get video info without downloading
python get_ibm_yt-dlt_gpt5_working_20251006.py --info-only

# Debug levels: none (quiet), min (info), max (detailed)
python get_ibm_yt-dlt_gpt5_working_20251006.py --debug-level max

# Quality/format options
python get_ibm_yt-dlt_gpt5_working_20251006.py -q 720p -f mp4 -o ./my_downloads

# Force video+audio combination for HLS streams
python get_ibm_yt-dlt_gpt5_working_20251006.py --fix-audio

# Use cookies for authentication
python get_ibm_yt-dlt_gpt5_working_20251006.py --cookies cookies.txt
python get_ibm_yt-dlt_gpt5_working_20251006.py --cookies-from-browser chrome
```

## Architecture

### Main Script: `get_ibm_yt-dlt_gpt5_working_20251006.py`

Single-file application with `VideoDownloader` class handling:

- **Diagnostics** (`run_diagnostic_tests`): Tests URL accessibility, metadata extraction, format detection, HLS stream analysis
- **Format Selection** (`get_optimal_format_selector`): Analyzes available formats, prioritizes combined streams, handles video+audio merging for HLS
- **Download** (`download_video`): Multi-fallback format selection with intelligent retry logic
- **Logging**: Three debug levels (none/min/max), session reports saved to `downloads/logs/`

### Key Configuration (`config.json`)

Format selectors defined as:
- `high_quality`: 1080p max
- `medium_quality`: 720p max
- `low_quality`: 480p max
- `audio_only`: m4a extraction

### HLS Stream Handling

IBM Video uses HLS with format IDs like `hls-271`, `hls-186`. The script:
1. Detects HLS streams and categorizes as video-only, audio-only, or combined
2. Builds format selector chains (combined > video+audio merge > video-only fallback)
3. Applies FFmpeg remux for QuickTime compatibility

### Output Structure

```
downloads/
├── logs/
│   ├── download_YYYYMMDD_HHMMSS.log
│   ├── session_report.json
│   └── network_debug.json
├── [uploader] - [title].mp4
├── [uploader] - [title].en.vtt  (subtitles)
└── [uploader] - [title].jpg     (thumbnail)
```

## Dependencies

- **yt-dlp**: Core downloading
- **FFmpeg**: Required for HLS processing and format conversion (install separately)
- **requests**: HTTP utilities

## Script Variants

Multiple script versions exist for testing different approaches:
- `get_ibm_yt-dlt_gpt5_working_20251006.py` - Primary working version
- `get_ibm_yt-dlt_claude45_20251006.py` - Claude variant
- `get_ibm_yt-dlt_grok4_20251006.py` - Grok variant
- `get_ibm_yt-dlt_no-audio_20250925.py` - Earlier version with audio issues

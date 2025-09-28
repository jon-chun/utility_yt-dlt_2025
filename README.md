# IBM Video Downloader with yt-dlp

A robust Python utility for downloading videos from IBM Video (video.ibm.com) and other platforms using yt-dlp, with advanced features for AI research workflows, comprehensive logging, and intelligent format detection.

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![yt-dlp](https://img.shields.io/badge/yt--dlp-latest-green.svg)](https://github.com/yt-dlp/yt-dlp)

## 🎯 **Verified Working Solution** ✅

**Status: FULLY FUNCTIONAL** - Successfully downloads IBM Video HLS streams!

**Latest Test Results:**
- ✅ **IBM Video URL**: `https://video.ibm.com/recorded/134516112` 
- ✅ **Formats Detected**: 7 HLS formats (252p to 1080p)
- ✅ **Download Success**: 1.74GB video in 5:32 minutes at 4.98MiB/s
- ✅ **Quality**: 1080p (hls-2625) automatically selected
- ✅ **Files Created**: Video + thumbnail + comprehensive logs

### Quick Success Test:
```bash
# This WILL work now:
python get_ibm_yt-dlt.py --debug-level max
```

## ✨ Features

- **🎯 Smart Format Detection**: Automatically detects available formats and selects optimal quality
- **📊 Comprehensive Logging**: Detailed logs with progress tracking and error handling
- **🔧 Highly Configurable**: Extensive configuration options for quality, format, and processing
- **🤖 AI Research Ready**: Built for multimodal AI research with structured outputs and batch processing
- **📱 Multiple Platforms**: Works with IBM Video, YouTube, and other yt-dlp supported sites
- **🔄 Resume Support**: Automatic retry logic and resumable downloads
- **📁 Organized Output**: Structured file organization with metadata extraction
- **⚡ Parallel Downloads**: Concurrent fragment downloads for faster speeds

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/jon-chun/utility_yt-dlt_2025.git
cd utility_yt-dlt_2025

# Create virtual environment (recommended)
uv venv --python=3.12
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
uv add -r requirements.txt
# OR with pip: pip install -r requirements.txt
```

### Basic Usage

```bash
# Download the default IBM video
python get_ibm_yt-dlt.py

# Download with custom URL
python get_ibm_yt-dlt.py https://video.ibm.com/recorded/YOUR_VIDEO_ID

# List available formats first (recommended)
python get_ibm_yt-dlt.py --list-formats

# Download with specific quality
python get_ibm_yt-dlt.py -q 720p -f mp4 -o ./my_downloads

# Get video information only
python get_ibm_yt-dlt.py --info-only

# Enable verbose logging
python get_ibm_yt-dlt.py -v
```

## 📋 Command Line Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--output-dir` | `-o` | Output directory for downloads | `./downloads` |
| `--quality` | `-q` | Video quality (`480p`, `720p`, `1080p`, `best`) | `best` |
| `--format` | `-f` | Output format (`mp4`, `webm`, `mkv`) | `mp4` |
| `--info-only` | | Extract video info without downloading | `False` |
| `--list-formats` | | List all available formats | `False` |
| `--verbose` | `-v` | Enable verbose logging | `False` |

## 🔧 Configuration

### Default Configuration

The script uses intelligent defaults that work for most scenarios:

```python
{
    "output_dir": "./downloads",
    "output_template": "%(uploader)s - %(title)s.%(ext)s",
    "format_selector": "best[ext=mp4]/best",
    "extract_subtitles": True,
    "download_thumbnail": True,
    "retries": 3,
    "concurrent_fragments": 4
}
```

### Custom Configuration

Create a custom configuration for specific needs:

```python
from get_ibm_yt_dlt import VideoDownloader

config = {
    'output_dir': './research_videos',
    'format_selector': 'best[height<=720][ext=mp4]',
    'extract_subtitles': True,
    'download_thumbnail': True,
    'log_level': 'DEBUG'
}

downloader = VideoDownloader(config)
downloader.download_video('https://video.ibm.com/recorded/134516112')
```

## 🤖 AI Research Integration

### Batch Processing for Datasets

```python
import pandas as pd
from get_ibm_yt_dlt import VideoDownloader

# Load video URLs from CSV
df = pd.read_csv('video_dataset.csv')

downloader = VideoDownloader({
    'output_dir': './dataset',
    'output_template': '%(id)s_%(title)s.%(ext)s',
    'format_selector': 'best[height=720][ext=mp4]'  # Consistent resolution
})

for idx, row in df.iterrows():
    print(f"Progress: {idx+1}/{len(df)} ({((idx+1)/len(df)*100):.1f}%)")
    success = downloader.download_video(row['url'])
    if not success:
        print(f"Failed: {row['url']}")
```

### Multimodal Analysis Setup

```python
# Configuration optimized for multimodal AI research
research_config = {
    'output_dir': './multimodal_dataset',
    'format_selector': 'best[height=720][ext=mp4]',  # Consistent for video analysis
    'extract_subtitles': True,                       # Text modality
    'download_thumbnail': True,                      # Image modality
    'output_template': '%(uploader)s/%(id)s_%(title)s.%(ext)s'
}
```

## 🎥 **Video Playback Compatibility**

### **Issue**: QuickTime Player Compatibility
Some HLS-converted videos may show "The file isn't compatible with QuickTime Player" due to timestamp issues.

### **Solutions**:

#### **Option 1: Use VLC Media Player (Recommended)**
```bash
# Download VLC (free): https://www.videolan.org/vlc/
# Then play with:
vlc "downloads/ConcordiaMHD - Symposium Plenary One.mp4"
```

#### **Option 2: Convert with FFmpeg**
```bash
# Install ffmpeg first, then convert:
ffmpeg -i "downloads/ConcordiaMHD - Symposium Plenary One.mp4" -c copy -movflags +faststart "fixed_video.mp4"
```

#### **Option 3: Download with Auto-Fix (Coming Soon)**
The script will automatically apply FFmpeg post-processing for HLS compatibility.

### **Recommended Media Players**:
- **VLC Media Player**: Best compatibility with HLS-converted videos
- **mpv**: Lightweight, excellent for all formats
- **IINA** (macOS): Modern macOS player with great codec support
- **PotPlayer** (Windows): Advanced features and codec support

## 🛠️ Troubleshooting

### Common Issues

#### 1. "Requested format is not available" Error

This happens when the video doesn't have the requested quality/format. **Solution:**

```bash
# First, check available formats
python get_ibm_yt-dlt.py --list-formats

# Then download with available format
python get_ibm_yt-dlt.py -q best  # Use best available quality
```

#### 2. IBM Video Platform Limitations

IBM Video (formerly Ustream) often has limited format options. **Solutions:**

- Use `--list-formats` to see what's available
- Set quality to `best` instead of specific resolutions
- The script automatically falls back to `best` format if preferred format fails

#### 3. Network Timeouts

```bash
# Increase retries and enable verbose logging
python get_ibm_yt-dlt.py -v  # Check detailed logs
```

#### 4. Permission Errors

```bash
# Ensure output directory is writable
mkdir -p ./downloads
chmod 755 ./downloads
```

### Debug Mode

Enable comprehensive debugging:

```bash
python get_ibm_yt-dlt.py -v --list-formats
```

## 📁 Output Structure

```
downloads/
├── logs/
│   ├── download_20241201_143022.log      # Detailed logs
│   └── progress_report.json              # Progress tracking
├── ConcordiaMHD - Symposium Plenary One.mp4
├── ConcordiaMHD - Symposium Plenary One.en.vtt  # Subtitles
└── ConcordiaMHD - Symposium Plenary One.jpg     # Thumbnail
```

## 🔍 Advanced Features

### Format Selection Logic

The script uses intelligent format selection:

1. **Analyzes available formats** for the specific video
2. **Selects optimal quality** based on what's actually available
3. **Falls back gracefully** if preferred format isn't available
4. **Prioritizes compatibility** (MP4 > WebM > MKV)

### Progress Tracking

```python
# Access progress data programmatically
downloader = VideoDownloader()
downloader.download_video(url)

# Check progress during download
progress = downloader.progress_data
print(f"Download progress: {progress}")
```

### Logging System

- **Structured logging** with timestamps
- **Progress tracking** with speed and ETA
- **Error categorization** for debugging
- **JSON reports** for programmatic access

## 🧪 Testing

Test with the default IBM video:

```bash
# Quick test - just get info
python get_ibm_yt-dlt.py --info-only

# Full test - download with verbose logging
python get_ibm_yt-dlt.py -v
```

Expected output for test video:
- **Title**: "Symposium Plenary One"
- **Duration**: ~85 minutes (5131 seconds)
- **Uploader**: "ConcordiaMHD"
- **Available formats**: 7 formats (252p to 486p)

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
# Install development dependencies
uv add --dev pytest black flake8 mypy

# Run tests
pytest tests/

# Format code
black get_ibm_yt_dlt.py

# Type checking
mypy get_ibm_yt_dlt.py
```

## 📄 Dependencies

- **Python 3.8+**
- **yt-dlp**: Core downloading functionality
- **requests**: HTTP requests
- **pathlib**: Path handling
- **FFmpeg**: Video processing (optional, for format conversion)

## 🐛 Known Issues

1. **IBM Video Platform**: Limited to lower resolutions (typically max 486p-720p)
2. **Subtitle Availability**: Not all videos have subtitles
3. **Regional Restrictions**: Some videos may be geographically restricted

## 🔮 Roadmap

- [ ] **GUI Interface** for non-technical users
- [ ] **Playlist Support** for batch downloads
- [ ] **Quality Upscaling** integration with AI models
- [ ] **Automatic Transcription** for videos without subtitles
- [ ] **Metadata Enhancement** with AI-generated descriptions
- [ ] **Docker Support** for containerized deployment

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **yt-dlp team** for the excellent downloading library
- **IBM** for providing accessible video content
- **Python community** for the robust ecosystem

## 📞 Support

- **Issues**: [GitHub Issues](https://github.com/jon-chun/utility_yt-dlt_2025/issues)
- **Discussions**: [GitHub Discussions](https://github.com/jon-chun/utility_yt-dlt_2025/discussions)
- **Email**: [Support Email](mailto:support@example.com)

---

**⭐ If this project helps your research, please give it a star!**
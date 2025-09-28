# IBM Video Downloader - Usage Guide v2.0

## Quick Setup

1. **Install dependencies:**
```bash
pip install -r requirements.txt
```

2. **Make script executable (Linux/Mac):**
```bash
chmod +x get_ibm_yt-dlt.py
```

## Debugging & Troubleshooting

### Debug Levels
The script now includes comprehensive debugging with three levels:

```bash
# No debug output (quiet mode)
python get_ibm_yt-dlt.py --debug-level none

# Minimal debug output (info only)
python get_ibm_yt-dlt.py --debug-level min

# Maximum debug output (detailed diagnostics)
python get_ibm_yt-dlt.py --debug-level max  # DEFAULT
python get_ibm_yt-dlt.py -v  # Same as max
```

### Diagnostic Tools

#### 1. Comprehensive Diagnostics
Run full diagnostic tests to identify issues:
```bash
python get_ibm_yt-dlt.py --diagnostics
```
**Output:**
- ✅ URL accessibility test
- ✅ Metadata extraction test  
- ✅ Format detection analysis
- 🎯 HLS format detection
- 🎯 Recommended format selection
- ⚠️ Issue identification

#### 2. Format Analysis
List all available formats with detailed analysis:
```bash
python get_ibm_yt-dlt.py --list-formats
```

#### 3. Video Information Only
Get video metadata without downloading:
```bash
python get_ibm_yt-dlt.py --info-only
```

## Basic Usage

### Download with automatic format detection:
```bash
# Best quality available (recommended)
python get_ibm_yt-dlt.py

# With custom URL
python get_ibm_yt-dlt.py https://video.ibm.com/recorded/YOUR_VIDEO_ID

# Specific quality preference
python get_ibm_yt-dlt.py -q 720p -f mp4 -o ./my_downloads
```

### HLS Stream Support
The script now automatically detects and handles HLS (HTTP Live Streaming) formats:

```bash
# For HLS streams, the script will:
# 1. Auto-detect HLS format IDs (hls-271, hls-186, etc.)
# 2. Select highest quality available
# 3. Fall back through multiple format options
# 4. Provide detailed diagnostic information
```

## Advanced Usage

### Full Diagnostic Workflow
When downloads fail, use this workflow:

```bash
# Step 1: Run diagnostics
python get_ibm_yt-dlt.py --diagnostics

# Step 2: Check available formats  
python get_ibm_yt-dlt.py --list-formats

# Step 3: Try download with max debugging
python get_ibm_yt-dlt.py --debug-level max

# Step 4: Try different quality settings
python get_ibm_yt-dlt.py -q best --debug-level max
```

### Custom Configuration in Python Code:
```python
from get_ibm_yt_dlt import VideoDownloader

# Custom configuration with debugging
config = {
    'output_dir': './research_videos',
    'format_selector': 'best[ext=mp4]',
    'extract_subtitles': True,
    'download_thumbnail': True,
}

# Initialize with debug level
downloader = VideoDownloader(config, debug_level='max')

# Run diagnostics first
diagnostics = downloader.run_diagnostic_tests('https://video.ibm.com/recorded/134516112')
print(f"HLS detected: {diagnostics['hls_detected']}")
print(f"Recommended format: {diagnostics['recommended_format']}")

# Download with enhanced error handling
success = downloader.download_video('https://video.ibm.com/recorded/134516112')
```

### Batch Download with Error Handling:
```python
urls = [
    'https://video.ibm.com/recorded/134516112',
    'https://video.ibm.com/recorded/another_video_id'
]

downloader = VideoDownloader(debug_level='min')
failed_downloads = []

for i, url in enumerate(urls):
    print(f"Progress: {i+1}/{len(urls)}")
    
    # Run diagnostics first
    diagnostics = downloader.run_diagnostic_tests(url)
    if not diagnostics['url_accessible']:
        print(f"❌ Skipping inaccessible URL: {url}")
        failed_downloads.append(url)
        continue
    
    success = downloader.download_video(url)
    if not success:
        failed_downloads.append(url)

print(f"Failed downloads: {len(failed_downloads)}")
```

## Command Line Options (Updated)

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--output-dir` | `-o` | Output directory for downloads | `./downloads` |
| `--quality` | `-q` | Video quality (`480p`, `720p`, `1080p`, `best`) | `best` |
| `--format` | `-f` | Output format (`mp4`, `webm`, `mkv`) | `mp4` |
| `--info-only` | | Extract video info without downloading | `False` |
| `--list-formats` | | List all available formats with analysis | `False` |
| `--diagnostics` | | Run comprehensive diagnostic tests | `False` |
| `--debug-level` | | Debug level (`none`, `min`, `max`) | `max` |
| `--verbose` | `-v` | Enable verbose logging (same as `--debug-level max`) | `False` |

## Output Structure (Enhanced)

```
downloads/
├── logs/
│   ├── download_20241201_143022.log      # Detailed logs with diagnostics
│   └── progress_report.json              # Progress tracking data
├── ConcordiaMHD - Symposium Plenary One.mp4
├── ConcordiaMHD - Symposium Plenary One.en.vtt  # Subtitles
└── ConcordiaMHD - Symposium Plenary One.jpg     # Thumbnail
```

## Troubleshooting HLS (IBM Video) Issues

### Issue: "Requested format is not available"
**Solution:**
```bash
# 1. Check what formats are actually available
python get_ibm_yt-dlt.py --list-formats

# 2. Run full diagnostics
python get_ibm_yt-dlt.py --diagnostics

# 3. Use automatic format detection
python get_ibm_yt-dlt.py -q best --debug-level max
```

### Issue: "No video formats found"
This indicates the URL might be:
- Private/restricted content
- Expired or removed video
- Geographic restrictions

**Solution:**
```bash
# Check URL accessibility
python get_ibm_yt-dlt.py --diagnostics
```

### Issue: HLS Format Detection
IBM Video uses HLS streaming with format IDs like:
- `hls-271` (486p)
- `hls-186` (360p) 
- `hls-114` (252p)

The script now automatically detects and uses these specific format IDs.

## Debug Output Examples

### Diagnostic Output:
```
🔍 RUNNING COMPREHENSIVE DIAGNOSTICS:
==================================================
ℹ️  INFO: Test 1: Checking URL accessibility
✅ URL is accessible
ℹ️  INFO: Test 2: Testing metadata extraction
✅ Metadata extracted: Symposium Plenary One
ℹ️  INFO: Test 3: Analyzing available formats
✅ Found 7 formats
🎯 HLS detected: 3 HLS formats found
🎯 Recommended HLS format: hls-271 (486p)

📊 DIAGNOSTIC RESULTS:
✅ URL Accessible: True
✅ Metadata Extraction: True  
✅ Format Detection: True
📊 Format Count: 7
🎯 HLS Detected: True
🎯 Recommended Format: hls-271
```

### Download Process Output:
```
🚀 STARTING DOWNLOAD...
ℹ️  INFO: Running pre-download diagnostics
ℹ️  INFO: Using diagnostics-recommended format: hls-271
🔍 DEBUG: Format options to try: ['hls-271', 'hls-186', 'hls-114', 'best', 'worst']
ℹ️  INFO: Attempt 1/5: Trying format 'hls-271'
✅ Download completed successfully with format: hls-271
```

## Integration with AI Research Workflows

### For Multimodal AI Research with Diagnostics:
```python
# Configuration optimized for research with enhanced diagnostics
research_config = {
    'output_dir': './multimodal_dataset',
    'extract_subtitles': True,        # Text modality
    'download_thumbnail': True,       # Image modality
    'output_template': '%(id)s_%(title)s.%(ext)s'
}

downloader = VideoDownloader(research_config, debug_level='min')

# Batch process with quality assessment
video_urls = load_video_list()
quality_report = []

for url in video_urls:
    diagnostics = downloader.run_diagnostic_tests(url)
    
    quality_info = {
        'url': url,
        'accessible': diagnostics['url_accessible'],
        'hls_format': diagnostics['hls_detected'],
        'max_quality': max([f['height'] for f in diagnostics['available_formats'] if f['height']], default=0),
        'format_count': diagnostics['format_count']
    }
    quality_report.append(quality_info)
    
    if diagnostics['url_accessible']:
        downloader.download_video(url)

# Analyze dataset quality
df = pd.DataFrame(quality_report)
print(f"Dataset quality summary:")
print(f"- Accessible videos: {df['accessible'].sum()}")
print(f"- HLS videos: {df['hls_format'].sum()}")
print(f"- Average max quality: {df['max_quality'].mean():.0f}p")
```

## Notes

- 🎯 **HLS Auto-Detection**: Automatically detects and handles IBM Video's HLS streaming formats
- 🔍 **Comprehensive Diagnostics**: Step-by-step testing to isolate download issues
- 📊 **Enhanced Logging**: Three debug levels for different use cases
- 🔄 **Smart Fallbacks**: Multiple format options tried automatically
- 🤖 **AI Research Ready**: Structured diagnostics for dataset quality assessment
- ✅ **Error Recovery**: Detailed error analysis and suggested solutions
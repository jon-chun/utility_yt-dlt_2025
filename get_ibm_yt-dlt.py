#!/usr/bin/env python3
"""
IBM Video Downloader using yt-dlp
Advanced video downloading script with configurable parameters and comprehensive logging.

Author: AI Research Team
Dependencies: yt-dlp, requests
"""

import os
import sys
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import subprocess
import argparse

try:
    import yt_dlp
except ImportError:
    print("Error: yt-dlp not installed. Run: pip install yt-dlp")
    sys.exit(1)


class VideoDownloader:
    """Advanced video downloader with comprehensive logging and progress tracking."""
    
    def __init__(self, config: Dict[str, Any] = None, debug_level: str = 'max'):
        """Initialize the downloader with configuration."""
        self.config = config or self.get_default_config()
        self.debug_level = debug_level.lower()
        self.config['debug_level'] = self.debug_level
        self.setup_logging()
        self.progress_data = {}
        self.diagnostic_data = {}
        
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration with popular settings."""
        return {
            # Output settings
            'output_dir': './downloads',
            'output_template': '%(uploader)s - %(title)s.%(ext)s',
            
            # Quality settings (popular defaults) - More flexible format selection
            'format_selector': 'best[ext=mp4]/best[ext=webm]/best',
            'video_quality': 'best',
            'audio_quality': 'best',
            
            # Download preferences
            'prefer_free_formats': True,
            'extract_subtitles': True,
            'auto_subtitles': True,
            'embed_subtitles': False,
            'download_thumbnail': True,
            'embed_thumbnail': False,
            
            # Network settings
            'retries': 3,
            'fragment_retries': 5,
            'concurrent_fragments': 4,
            
            # Post-processing
            'merge_output_format': 'mp4',
            'keep_video': True,
            
            # Logging
            'verbose': True,
            'log_level': 'INFO'
        }
    
    def setup_logging(self):
        """Setup comprehensive logging system with debug levels."""
        log_dir = Path(self.config['output_dir']) / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = log_dir / f'download_{timestamp}.log'
        
        # Determine log level based on debug_level
        if self.debug_level == 'none':
            log_level = logging.WARNING
            console_level = logging.ERROR
        elif self.debug_level == 'min':
            log_level = logging.INFO
            console_level = logging.INFO
        else:  # 'max'
            log_level = logging.DEBUG
            console_level = logging.DEBUG
        
        # Configure logging
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ],
            force=True
        )
        
        # Set console handler level separately
        console_handler = logging.StreamHandler()
        console_handler.setLevel(console_level)
        
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        
        if self.debug_level != 'none':
            self.logger.info(f"Debug level: {self.debug_level}")
            self.logger.info(f"Logging initialized. Log file: {log_file}")
            self.logger.debug(f"Configuration: {json.dumps(self.config, indent=2)}")

    def debug_print(self, message: str, level: str = 'info'):
        """Print debug messages based on debug level."""
        if self.debug_level == 'none':
            return
        elif self.debug_level == 'min' and level == 'debug':
            return
        
        if level == 'debug':
            self.logger.debug(f"🔍 DEBUG: {message}")
        elif level == 'info':
            self.logger.info(f"ℹ️  INFO: {message}")
        elif level == 'warning':
            self.logger.warning(f"⚠️  WARNING: {message}")
        elif level == 'error':
            self.logger.error(f"❌ ERROR: {message}")

    def run_diagnostic_tests(self, url: str) -> Dict[str, Any]:
        """Run incremental diagnostic tests to isolate issues."""
        self.debug_print("Starting comprehensive diagnostic tests", 'info')
        diagnostics = {
            'url_accessible': False,
            'metadata_extraction': False,
            'format_detection': False,
            'format_count': 0,
            'hls_detected': False,
            'available_formats': [],
            'recommended_format': None,
            'issues_found': []
        }
        
        try:
            # Test 1: Basic URL accessibility
            self.debug_print("Test 1: Checking URL accessibility", 'info')
            ydl_opts_basic = {'quiet': True, 'no_warnings': True}
            with yt_dlp.YoutubeDL(ydl_opts_basic) as ydl:
                try:
                    info = ydl.extract_info(url, download=False)
                    diagnostics['url_accessible'] = True
                    self.debug_print("✅ URL is accessible", 'info')
                except Exception as e:
                    diagnostics['issues_found'].append(f"URL not accessible: {str(e)}")
                    self.debug_print(f"❌ URL not accessible: {str(e)}", 'error')
                    return diagnostics
            
            # Test 2: Metadata extraction
            self.debug_print("Test 2: Testing metadata extraction", 'info')
            if info.get('title'):
                diagnostics['metadata_extraction'] = True
                self.debug_print(f"✅ Metadata extracted: {info.get('title')}", 'info')
            else:
                diagnostics['issues_found'].append("No metadata found")
                self.debug_print("❌ No metadata found", 'error')
            
            # Test 3: Format detection and analysis
            self.debug_print("Test 3: Analyzing available formats", 'info')
            formats = info.get('formats', [])
            diagnostics['format_count'] = len(formats)
            
            if formats:
                diagnostics['format_detection'] = True
                self.debug_print(f"✅ Found {len(formats)} formats", 'info')
                
                # Analyze format types
                format_details = []
                hls_formats = []
                regular_formats = []
                
                for fmt in formats:
                    format_id = fmt.get('format_id', 'unknown')
                    ext = fmt.get('ext', 'unknown')
                    height = fmt.get('height')
                    vcodec = fmt.get('vcodec', 'unknown')
                    acodec = fmt.get('acodec', 'unknown')
                    filesize = fmt.get('filesize')
                    
                    format_info = {
                        'id': format_id,
                        'ext': ext,
                        'height': height,
                        'vcodec': vcodec,
                        'acodec': acodec,
                        'filesize': filesize,
                        'is_hls': format_id.startswith('hls-')
                    }
                    format_details.append(format_info)
                    
                    if format_id.startswith('hls-'):
                        hls_formats.append(format_info)
                        diagnostics['hls_detected'] = True
                    else:
                        regular_formats.append(format_info)
                
                diagnostics['available_formats'] = format_details
                
                if diagnostics['hls_detected']:
                    self.debug_print(f"🎯 HLS detected: {len(hls_formats)} HLS formats found", 'info')
                    
                    # Find best HLS format
                    video_hls = [f for f in hls_formats if f['height'] and f['vcodec'] != 'none']
                    if video_hls:
                        best_hls = max(video_hls, key=lambda x: x['height'] or 0)
                        diagnostics['recommended_format'] = best_hls['id']
                        self.debug_print(f"🎯 Recommended HLS format: {best_hls['id']} ({best_hls['height']}p)", 'info')
                
                # Debug format details
                if self.debug_level == 'max':
                    self.debug_print("📋 Detailed format analysis:", 'debug')
                    for i, fmt in enumerate(format_details):
                        self.debug_print(f"  Format {i+1}: {fmt}", 'debug')
                
            else:
                diagnostics['issues_found'].append("No formats found in metadata")
                self.debug_print("❌ No formats found", 'error')
            
            # Test 4: Format selector validation
            self.debug_print("Test 4: Testing format selectors", 'info')
            if diagnostics['recommended_format']:
                test_selectors = [
                    diagnostics['recommended_format'],  # Specific HLS format
                    'best',  # Generic best
                    'worst',  # Generic worst
                ]
                
                for selector in test_selectors:
                    try:
                        test_opts = {
                            'format': selector,
                            'quiet': True,
                            'no_warnings': True,
                            'simulate': True
                        }
                        with yt_dlp.YoutubeDL(test_opts) as test_ydl:
                            test_ydl.extract_info(url, download=False)
                        self.debug_print(f"✅ Format selector '{selector}' works", 'info')
                    except Exception as e:
                        self.debug_print(f"❌ Format selector '{selector}' failed: {str(e)}", 'warning')
        
        except Exception as e:
            diagnostics['issues_found'].append(f"Diagnostic test failed: {str(e)}")
            self.debug_print(f"❌ Diagnostic test failed: {str(e)}", 'error')
        
        # Store diagnostics
        self.diagnostic_data = diagnostics
        return diagnostics
    
    def progress_hook(self, d: Dict[str, Any]):
        """Progress tracking hook for yt-dlp."""
        if d['status'] == 'downloading':
            filename = d.get('filename', 'Unknown')
            
            if 'total_bytes' in d:
                percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
                speed = d.get('speed', 0)
                eta = d.get('eta', 0)
                
                self.logger.info(
                    f"Downloading: {percent:.1f}% | "
                    f"Speed: {self._format_bytes(speed)}/s | "
                    f"ETA: {eta}s | "
                    f"File: {os.path.basename(filename)}"
                )
                
                # Store progress for potential external monitoring
                self.progress_data[filename] = {
                    'percent': percent,
                    'speed': speed,
                    'eta': eta,
                    'downloaded': d['downloaded_bytes'],
                    'total': d['total_bytes']
                }
            
        elif d['status'] == 'finished':
            filename = d.get('filename', 'Unknown')
            self.logger.info(f"Download completed: {os.path.basename(filename)}")
            
        elif d['status'] == 'error':
            self.logger.error(f"Download error: {d.get('error', 'Unknown error')}")
    
    def _format_bytes(self, bytes_val: Optional[float]) -> str:
        """Format bytes into human readable format."""
        if bytes_val is None:
            return "N/A"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.1f}{unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.1f}TB"
    
    def list_available_formats(self, url: str) -> List[Dict[str, Any]]:
        """List all available formats for the video."""
        self.logger.info(f"Listing available formats for: {url}")
        
        ydl_opts = {
            'quiet': not self.config['verbose'],
            'no_warnings': False,
            'extract_flat': False,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = info.get('formats', [])
                
                self.logger.info(f"Total available formats: {len(formats)}")
                print(f"\n{'='*80}")
                print("AVAILABLE FORMATS:")
                print(f"{'='*80}")
                
                for i, fmt in enumerate(formats):
                    format_id = fmt.get('format_id', 'N/A')
                    ext = fmt.get('ext', 'N/A')
                    height = fmt.get('height', 'N/A')
                    width = fmt.get('width', 'N/A')
                    filesize = fmt.get('filesize', 'N/A')
                    tbr = fmt.get('tbr', 'N/A')
                    vcodec = fmt.get('vcodec', 'N/A')
                    acodec = fmt.get('acodec', 'N/A')
                    
                    print(f"{i+1:2d}. Format ID: {format_id}")
                    print(f"    Extension: {ext}")
                    print(f"    Resolution: {width}x{height}" if width != 'N/A' and height != 'N/A' else f"    Height: {height}p" if height != 'N/A' else "    Resolution: N/A")
                    print(f"    Bitrate: {tbr} kbps" if tbr != 'N/A' else "    Bitrate: N/A")
                    print(f"    Video Codec: {vcodec}")
                    print(f"    Audio Codec: {acodec}")
                    print(f"    File Size: {self._format_bytes(filesize) if filesize != 'N/A' else 'N/A'}")
                    print()
                
                return formats
                
        except Exception as e:
            self.logger.error(f"Failed to list formats: {str(e)}")
            raise

    def get_video_info(self, url: str) -> Dict[str, Any]:
        """Extract video information without downloading."""
        self.logger.info(f"Extracting video information for: {url}")
        
        ydl_opts = {
            'quiet': not self.config['verbose'],
            'no_warnings': False,
            'extract_flat': False,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                # Log essential video information
                self.logger.info(f"Title: {info.get('title', 'N/A')}")
                self.logger.info(f"Duration: {info.get('duration', 'N/A')} seconds")
                self.logger.info(f"Uploader: {info.get('uploader', 'N/A')}")
                self.logger.info(f"View count: {info.get('view_count', 'N/A')}")
                
                # Log available formats with better analysis
                if 'formats' in info:
                    formats = info['formats']
                    self.logger.info(f"Available formats: {len(formats)}")
                    
                    # Analyze available qualities
                    available_heights = [f.get('height') for f in formats if f.get('height')]
                    available_exts = list(set([f.get('ext') for f in formats if f.get('ext')]))
                    
                    if available_heights:
                        max_height = max(available_heights)
                        self.logger.info(f"Maximum available resolution: {max_height}p")
                    
                    self.logger.info(f"Available extensions: {', '.join(available_exts)}")
                    
                    # Show sample formats
                    for i, fmt in enumerate(formats[:5]):  # Show first 5 formats
                        quality_info = f"{fmt.get('format_id', 'N/A')} - {fmt.get('ext', 'N/A')}"
                        if fmt.get('height'):
                            quality_info += f" - {fmt['height']}p"
                        if fmt.get('filesize'):
                            quality_info += f" - {self._format_bytes(fmt['filesize'])}"
                        self.logger.info(f"  Format {i+1}: {quality_info}")
                
                return info
                
        except Exception as e:
            self.logger.error(f"Failed to extract video info: {str(e)}")
            raise
    
    def get_optimal_format_selector(self, url: str, preferred_quality: str = "best") -> str:
        """Determine optimal format selector based on available formats and diagnostics."""
        try:
            self.debug_print("Running diagnostics to determine optimal format", 'info')
            diagnostics = self.run_diagnostic_tests(url)
            
            if not diagnostics['format_detection']:
                self.debug_print("No formats detected, using fallback 'best'", 'warning')
                return 'best'
            
            # Handle HLS formats specially
            if diagnostics['hls_detected']:
                self.debug_print("HLS stream detected, using HLS-specific format selection", 'info')
                
                if diagnostics['recommended_format']:
                    recommended = diagnostics['recommended_format']
                    self.debug_print(f"Using recommended HLS format: {recommended}", 'info')
                    return recommended
                else:
                    # Fallback to best HLS format
                    hls_formats = [f for f in diagnostics['available_formats'] if f['is_hls'] and f['height']]
                    if hls_formats:
                        best_hls = max(hls_formats, key=lambda x: x['height'] or 0)
                        self.debug_print(f"Using best available HLS format: {best_hls['id']}", 'info')
                        return best_hls['id']
            
            # Regular format handling
            info = self.get_video_info(url)
            formats = info.get('formats', [])
            
            if not formats:
                return 'best'
            
            # Analyze available formats
            available_heights = [f.get('height') for f in formats if f.get('height')]
            available_exts = [f.get('ext') for f in formats if f.get('ext')]
            
            # Determine best available extension
            ext_priority = ['mp4', 'webm', 'mkv', 'flv']
            best_ext = None
            for ext in ext_priority:
                if ext in available_exts:
                    best_ext = ext
                    break
            
            # Determine quality constraint
            if available_heights:
                max_height = max(available_heights)
                self.debug_print(f"Adjusting format selector for max available resolution: {max_height}p", 'info')
                
                if preferred_quality == "best":
                    if best_ext:
                        return f'best[ext={best_ext}]/best'
                    else:
                        return 'best'
                else:
                    # Parse preferred quality (e.g., "1080p" -> 1080)
                    try:
                        preferred_height = int(preferred_quality.replace('p', ''))
                        target_height = min(preferred_height, max_height)
                        
                        if best_ext:
                            return f'best[height<={target_height}][ext={best_ext}]/best[ext={best_ext}]/best'
                        else:
                            return f'best[height<={target_height}]/best'
                    except ValueError:
                        return f'best[ext={best_ext}]/best' if best_ext else 'best'
            else:
                # No height info available, just use extension preference
                return f'best[ext={best_ext}]/best' if best_ext else 'best'
                
        except Exception as e:
            self.debug_print(f"Could not determine optimal format, using fallback: {str(e)}", 'warning')
            return 'best'
    
    def download_video(self, url: str) -> bool:
        """Download video with configured parameters and enhanced diagnostics."""
        self.debug_print(f"Starting download process for: {url}", 'info')
        
        # Ensure output directory exists
        output_dir = Path(self.config['output_dir'])
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Run comprehensive diagnostics first
        self.debug_print("Running pre-download diagnostics", 'info')
        diagnostics = self.run_diagnostic_tests(url)
        
        if not diagnostics['url_accessible']:
            self.debug_print("URL not accessible, aborting download", 'error')
            return False
        
        if not diagnostics['format_detection']:
            self.debug_print("No formats detected, trying basic download", 'warning')
        
        # Determine optimal format selector
        try:
            if diagnostics.get('recommended_format'):
                optimal_format = diagnostics['recommended_format']
                self.debug_print(f"Using diagnostics-recommended format: {optimal_format}", 'info')
            else:
                optimal_format = self.get_optimal_format_selector(url, self.config['video_quality'])
                self.debug_print(f"Using computed optimal format: {optimal_format}", 'info')
        except Exception as e:
            self.debug_print(f"Could not determine optimal format, using configured default: {str(e)}", 'warning')
            optimal_format = self.config['format_selector']
        
        # Prepare multiple format options for fallback
        format_options = []
        
        if diagnostics.get('hls_detected'):
            # For HLS, try specific format IDs first
            hls_video_formats = [
                f for f in diagnostics.get('available_formats', []) 
                if f.get('is_hls') and f.get('height') and f.get('vcodec') != 'none'
            ]
            if hls_video_formats:
                # Sort by quality (height) descending
                hls_video_formats.sort(key=lambda x: x.get('height', 0), reverse=True)
                format_options.extend([f['id'] for f in hls_video_formats[:3]])  # Top 3 qualities
        
        # Add generic fallbacks
        format_options.extend([
            optimal_format,
            'best',
            'worst',
            'best[ext=mp4]',
            'best[ext=webm]'
        ])
        
        # Remove duplicates while preserving order
        format_options = list(dict.fromkeys(format_options))
        
        self.debug_print(f"Format options to try: {format_options}", 'debug')
        
        # Configure yt-dlp options
        base_ydl_opts = {
            # Output settings
            'outtmpl': str(output_dir / self.config['output_template']),
            
            # Download settings
            'retries': self.config['retries'],
            'fragment_retries': self.config['fragment_retries'],
            'concurrent_fragment_downloads': self.config['concurrent_fragments'],
            
            # Subtitles
            'writesubtitles': self.config['extract_subtitles'],
            'writeautomaticsub': self.config['auto_subtitles'],
            'embedsubtitles': self.config['embed_subtitles'],
            
            # Thumbnails
            'writethumbnail': self.config['download_thumbnail'],
            'embedthumbnail': self.config['embed_thumbnail'],
            
            # Post-processing
            'merge_output_format': self.config['merge_output_format'],
            'keepvideo': self.config['keep_video'],
            
            # Progress tracking
            'progress_hooks': [self.progress_hook],
            
            # Logging
            'quiet': self.debug_level == 'none',
            'no_warnings': self.debug_level == 'none',
            
            # Error handling
            'ignoreerrors': False,
        }
        
        # Add post-processors if needed
        if self.config['merge_output_format']:
            base_ydl_opts['postprocessors'] = [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': self.config['merge_output_format'],
            }]
        
        # Try each format option
        for i, format_selector in enumerate(format_options):
            try:
                self.debug_print(f"Attempt {i+1}/{len(format_options)}: Trying format '{format_selector}'", 'info')
                
                ydl_opts = base_ydl_opts.copy()
                ydl_opts['format'] = format_selector
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                
                self.debug_print(f"✅ Download completed successfully with format: {format_selector}", 'info')
                return True
                
            except yt_dlp.DownloadError as e:
                error_msg = str(e)
                self.debug_print(f"❌ Format '{format_selector}' failed: {error_msg}", 'warning')
                
                # Check if it's a format-specific error
                if "Requested format is not available" in error_msg:
                    continue  # Try next format
                elif "No video formats found" in error_msg:
                    continue  # Try next format
                else:
                    # Other errors might be more serious
                    self.debug_print(f"Serious download error with '{format_selector}': {error_msg}", 'error')
                    continue
                    
            except Exception as e:
                self.debug_print(f"❌ Unexpected error with format '{format_selector}': {str(e)}", 'error')
                continue
        
        # If all formats failed, try one last desperate attempt
        self.debug_print("All format options failed, trying final fallback", 'warning')
        try:
            final_opts = {
                'outtmpl': str(output_dir / self.config['output_template']),
                'quiet': False,
                'no_warnings': False,
            }
            
            with yt_dlp.YoutubeDL(final_opts) as ydl:
                ydl.download([url])
            
            self.debug_print("✅ Final fallback download succeeded", 'info')
            return True
            
        except Exception as final_error:
            self.debug_print(f"❌ Final fallback also failed: {str(final_error)}", 'error')
            
            # Provide diagnostic summary
            self.debug_print("📊 Download failure summary:", 'error')
            self.debug_print(f"  - URL accessible: {diagnostics.get('url_accessible', False)}", 'error')
            self.debug_print(f"  - Formats found: {diagnostics.get('format_count', 0)}", 'error')
            self.debug_print(f"  - HLS detected: {diagnostics.get('hls_detected', False)}", 'error')
            self.debug_print(f"  - Formats tried: {len(format_options)}", 'error')
            if diagnostics.get('issues_found'):
                for issue in diagnostics['issues_found']:
                    self.debug_print(f"  - Issue: {issue}", 'error')
            
            return False
    
    def save_progress_report(self):
        """Save progress report to file."""
        if not self.progress_data:
            return
            
        report_file = Path(self.config['output_dir']) / 'logs' / 'progress_report.json'
        
        try:
            with open(report_file, 'w') as f:
                json.dump(self.progress_data, f, indent=2)
            self.logger.info(f"Progress report saved: {report_file}")
        except Exception as e:
            self.logger.error(f"Failed to save progress report: {str(e)}")


def main():
    """Main function with command-line interface."""
    parser = argparse.ArgumentParser(description='Download IBM videos using yt-dlp')
    parser.add_argument('url', nargs='?', 
                       default='https://video.ibm.com/recorded/134516112',
                       help='Video URL to download')
    parser.add_argument('--output-dir', '-o', default='./downloads',
                       help='Output directory for downloads')
    parser.add_argument('--quality', '-q', default='best',
                       choices=['480p', '720p', '1080p', 'best'],
                       help='Video quality preference')
    parser.add_argument('--format', '-f', default='mp4',
                       choices=['mp4', 'webm', 'mkv'],
                       help='Output format preference')
    parser.add_argument('--info-only', action='store_true',
                       help='Only extract video information, do not download')
    parser.add_argument('--list-formats', action='store_true',
                       help='List all available formats for the video')
    parser.add_argument('--diagnostics', action='store_true',
                       help='Run comprehensive diagnostic tests')
    parser.add_argument('--debug-level', choices=['none', 'min', 'max'], default='max',
                       help='Debug output level (default: max)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging (equivalent to --debug-level max)')
    
    args = parser.parse_args()
    
    # Handle verbose flag
    if args.verbose:
        args.debug_level = 'max'
    
    # Create custom configuration based on arguments
    config = {
        'output_dir': args.output_dir,
        'output_template': '%(uploader)s - %(title)s.%(ext)s',
        'format_selector': f'best[ext={args.format}]/best',  # Simplified default
        'video_quality': args.quality,
        'audio_quality': 'best',
        'prefer_free_formats': True,
        'extract_subtitles': True,
        'auto_subtitles': True,
        'embed_subtitles': False,
        'download_thumbnail': True,
        'embed_thumbnail': False,
        'retries': 3,
        'fragment_retries': 5,
        'concurrent_fragments': 4,
        'merge_output_format': args.format,
        'keep_video': True,
        'verbose': args.debug_level != 'none',
        'log_level': 'DEBUG' if args.debug_level == 'max' else 'INFO'
    }
    
    # Initialize downloader with debug level
    downloader = VideoDownloader(config, debug_level=args.debug_level)
    
    try:
        if args.debug_level != 'none':
            print(f"{'='*70}")
            print(f"🎬 IBM Video Downloader v2.0 (Debug Level: {args.debug_level.upper()})")
            print(f"{'='*70}")
            print(f"📋 URL: {args.url}")
            print(f"📁 Output Directory: {args.output_dir}")
            print(f"🎯 Quality: {args.quality}")
            print(f"📄 Format: {args.format}")
            print(f"🔍 Debug Level: {args.debug_level}")
            print(f"{'='*70}")
        
        # Run diagnostics if requested
        if args.diagnostics:
            print("\n🔍 RUNNING COMPREHENSIVE DIAGNOSTICS:")
            print("="*50)
            diagnostics = downloader.run_diagnostic_tests(args.url)
            
            print(f"\n📊 DIAGNOSTIC RESULTS:")
            print(f"✅ URL Accessible: {diagnostics.get('url_accessible', False)}")
            print(f"✅ Metadata Extraction: {diagnostics.get('metadata_extraction', False)}")
            print(f"✅ Format Detection: {diagnostics.get('format_detection', False)}")
            print(f"📊 Format Count: {diagnostics.get('format_count', 0)}")
            print(f"🎯 HLS Detected: {diagnostics.get('hls_detected', False)}")
            if diagnostics.get('recommended_format'):
                print(f"🎯 Recommended Format: {diagnostics['recommended_format']}")
            
            if diagnostics.get('issues_found'):
                print(f"\n⚠️  ISSUES FOUND:")
                for issue in diagnostics['issues_found']:
                    print(f"  - {issue}")
            
            print("\n" + "="*50)
            return
        
        # List formats if requested
        if args.list_formats:
            print("\n🔍 LISTING AVAILABLE FORMATS:")
            print("="*50)
            try:
                downloader.list_available_formats(args.url)
            except Exception as e:
                print(f"❌ Could not list formats: {str(e)}")
                print("🔧 Trying diagnostic approach...")
                diagnostics = downloader.run_diagnostic_tests(args.url)
                if diagnostics.get('available_formats'):
                    print(f"\n📋 FORMATS FOUND VIA DIAGNOSTICS:")
                    for i, fmt in enumerate(diagnostics['available_formats']):
                        print(f"{i+1:2d}. Format ID: {fmt['id']}")
                        print(f"    Extension: {fmt['ext']}")
                        print(f"    Height: {fmt['height']}p" if fmt['height'] else "    Height: N/A")
                        print(f"    Video Codec: {fmt['vcodec']}")
                        print(f"    Audio Codec: {fmt['acodec']}")
                        print(f"    HLS Format: {fmt['is_hls']}")
                        print()
            return
        
        # Extract video information
        try:
            video_info = downloader.get_video_info(args.url)
        except Exception as e:
            print(f"❌ Failed to extract video information: {str(e)}")
            print("🔧 Trying diagnostic fallback...")
            diagnostics = downloader.run_diagnostic_tests(args.url)
            if not diagnostics.get('url_accessible'):
                print("❌ URL is not accessible. Please check the URL and try again.")
                sys.exit(1)
            video_info = {'title': 'Unknown', 'duration': 'Unknown', 'uploader': 'Unknown'}
        
        if args.info_only:
            print(f"\n📋 VIDEO INFORMATION:")
            print(f"Title: {video_info.get('title', 'N/A')}")
            print(f"Duration: {video_info.get('duration', 'N/A')} seconds")
            print(f"Uploader: {video_info.get('uploader', 'N/A')}")
            description = video_info.get('description', 'N/A')
            if description and len(description) > 200:
                description = description[:200] + "..."
            print(f"Description: {description}")
            return
        
        # Download video
        print(f"\n🚀 STARTING DOWNLOAD...")
        success = downloader.download_video(args.url)
        
        # Save progress report
        downloader.save_progress_report()
        
        if success:
            print(f"\n{'='*70}")
            print("✅ DOWNLOAD COMPLETED SUCCESSFULLY!")
            print(f"📁 Files saved to: {args.output_dir}")
            print(f"{'='*70}")
        else:
            print(f"\n{'='*70}")
            print("❌ DOWNLOAD FAILED")
            print("🔧 Troubleshooting suggestions:")
            print("  1. Try: --diagnostics (to run full diagnostic tests)")
            print("  2. Try: --list-formats (to see available formats)")
            print("  3. Try: --debug-level max (for detailed debugging)")
            print("  4. Try: different --quality settings (best, 720p, 480p)")
            print("  5. Check the log files in downloads/logs/ for details")
            print(f"{'='*70}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Download interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        print("🔧 Try using --diagnostics to debug the issue.")
        if args.debug_level == 'none':
            print("🔧 Or use --debug-level max for detailed error information.")
        sys.exit(1)


if __name__ == "__main__":
    main()
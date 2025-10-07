#!/usr/bin/env python3
"""
IBM Video Downloader using yt-dlp - FIXED VERSION
Advanced video downloading script with enhanced HLS handling and comprehensive logging.

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
        self.force_audio_combination = False
        self.optimal_format_found = None  # Store the format that diagnostics confirms works
        
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration with popular settings."""
        return {
            # Output settings
            'output_dir': './downloads',
            'output_template': '%(uploader)s - %(title)s.%(ext)s',
            
            # Quality settings - will be overridden by diagnostics for HLS
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
        
        # Emoji mapping based on level
        emoji_map = {
            'debug': '🔍',
            'info': 'ℹ️',
            'warning': '⚠️',
            'error': '❌',
            'success': '✅',
            'progress': '⏳'
        }
        
        emoji = emoji_map.get(level, 'ℹ️')
        level_upper = level.upper()
        
        if level == 'debug':
            self.logger.debug(f"{emoji} DEBUG: {message}")
        elif level == 'info':
            self.logger.info(f"{emoji} INFO: {message}")
        elif level == 'warning':
            self.logger.warning(f"{emoji} WARNING: {message}")
        elif level == 'error':
            self.logger.error(f"{emoji} ERROR: {message}")
        elif level == 'success':
            self.logger.info(f"{emoji} SUCCESS: {message}")
        elif level == 'progress':
            self.logger.info(f"{emoji} PROGRESS: {message}")

    def run_diagnostic_tests(self, url: str) -> Dict[str, Any]:
        """Run incremental diagnostic tests to isolate issues."""
        self.debug_print("=" * 70, 'info')
        self.debug_print("STARTING COMPREHENSIVE DIAGNOSTIC TESTS", 'info')
        self.debug_print("=" * 70, 'info')
        
        diagnostics = {
            'url_accessible': False,
            'metadata_extraction': False,
            'format_detection': False,
            'format_count': 0,
            'hls_detected': False,
            'hls_separated_streams': False,  # NEW: Track if streams are separated
            'available_formats': [],
            'recommended_format': None,
            'tested_working_format': None,  # NEW: Track which format was actually tested
            'issues_found': [],
            'fallback_safe': False  # NEW: Can we use generic selectors?
        }
        
        try:
            # Test 1: Basic URL accessibility
            self.debug_print("", 'info')
            self.debug_print("TEST 1: Checking URL accessibility", 'info')
            self.debug_print("-" * 70, 'info')
            ydl_opts_basic = {'quiet': True, 'no_warnings': True}
            with yt_dlp.YoutubeDL(ydl_opts_basic) as ydl:
                try:
                    info = ydl.extract_info(url, download=False)
                    diagnostics['url_accessible'] = True
                    self.debug_print("URL is accessible and can be parsed", 'success')
                except Exception as e:
                    diagnostics['issues_found'].append(f"URL not accessible: {str(e)}")
                    self.debug_print(f"URL not accessible: {str(e)}", 'error')
                    return diagnostics
            
            # Test 2: Metadata extraction
            self.debug_print("", 'info')
            self.debug_print("TEST 2: Testing metadata extraction", 'info')
            self.debug_print("-" * 70, 'info')
            if info.get('title'):
                diagnostics['metadata_extraction'] = True
                self.debug_print(f"Video title: '{info.get('title')}'", 'success')
                self.debug_print(f"Duration: {info.get('duration', 'Unknown')} seconds", 'info')
                self.debug_print(f"Uploader: {info.get('uploader', 'Unknown')}", 'info')
            else:
                diagnostics['issues_found'].append("No metadata found")
                self.debug_print("No metadata found in video info", 'error')
            
            # Test 3: Format detection and analysis
            self.debug_print("", 'info')
            self.debug_print("TEST 3: Analyzing available formats", 'info')
            self.debug_print("-" * 70, 'info')
            formats = info.get('formats', [])
            diagnostics['format_count'] = len(formats)
            
            if formats:
                diagnostics['format_detection'] = True
                self.debug_print(f"Found {len(formats)} total formats", 'success')
                
                # Analyze format types
                format_details = []
                hls_formats = []
                video_only_formats = []
                audio_only_formats = []
                combined_formats = []
                
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
                        
                        # Categorize HLS streams
                        if height and vcodec != 'none' and acodec == 'none':
                            video_only_formats.append(format_info)
                        elif vcodec == 'none' and acodec != 'none':
                            audio_only_formats.append(format_info)
                        elif height and vcodec != 'none' and acodec != 'none':
                            combined_formats.append(format_info)
                
                diagnostics['available_formats'] = format_details
                diagnostics['video_only_count'] = len(video_only_formats)
                diagnostics['audio_only_count'] = len(audio_only_formats)
                diagnostics['combined_count'] = len(combined_formats)
                
                if diagnostics['hls_detected']:
                    self.debug_print(f"HLS streaming detected: {len(hls_formats)} HLS formats", 'info')
                    self.debug_print(f"  - Video-only streams: {len(video_only_formats)}", 'debug')
                    self.debug_print(f"  - Audio-only streams: {len(audio_only_formats)}", 'debug')
                    self.debug_print(f"  - Combined (video+audio) streams: {len(combined_formats)}", 'debug')
                    
                    # Determine if streams are separated (CRITICAL for IBM videos)
                    if video_only_formats and audio_only_formats and not combined_formats:
                        diagnostics['hls_separated_streams'] = True
                        self.debug_print("CRITICAL: HLS streams are SEPARATED (video-only + audio-only)", 'warning')
                        self.debug_print("This means generic selectors like 'best' will NOT work", 'warning')
                        diagnostics['fallback_safe'] = False
                    elif combined_formats:
                        diagnostics['fallback_safe'] = True
                        self.debug_print("HLS streams are COMBINED (video+audio together)", 'success')
                    
                    # Determine recommended format based on stream separation
                    if combined_formats:
                        # Use best combined format if available
                        best_combined = max(combined_formats, key=lambda x: x['height'] or 0)
                        diagnostics['recommended_format'] = best_combined['id']
                        self.debug_print(f"Recommended format: {best_combined['id']} (combined, {best_combined['height']}p)", 'success')
                    elif video_only_formats and audio_only_formats:
                        # Recommend video+audio combination (CRITICAL for IBM)
                        best_video = max(video_only_formats, key=lambda x: x['height'] or 0)
                        best_audio = audio_only_formats[0]  # Usually equivalent
                        combined_recommendation = f"{best_video['id']}+{best_audio['id']}"
                        diagnostics['recommended_format'] = combined_recommendation
                        self.debug_print(f"Recommended format combination: {combined_recommendation}", 'success')
                        self.debug_print(f"  - Video: {best_video['id']} ({best_video['height']}p, {best_video['vcodec']})", 'info')
                        self.debug_print(f"  - Audio: {best_audio['id']} ({best_audio['acodec']})", 'info')
                    elif video_only_formats:
                        # Only video available (no audio warning)
                        best_video = max(video_only_formats, key=lambda x: x['height'] or 0)
                        diagnostics['recommended_format'] = best_video['id']
                        diagnostics['issues_found'].append("No audio streams detected - video only")
                        self.debug_print(f"WARNING: Only video streams available: {best_video['id']} (NO AUDIO)", 'warning')
                else:
                    # Non-HLS formats, generic selectors should work
                    diagnostics['fallback_safe'] = True
                    self.debug_print("Non-HLS video detected, generic selectors should work", 'info')
                
                # Debug format details
                if self.debug_level == 'max':
                    self.debug_print("", 'debug')
                    self.debug_print("Detailed format list:", 'debug')
                    for i, fmt in enumerate(format_details):
                        self.debug_print(f"  [{i+1}] {fmt['id']}: {fmt['ext']}, " +
                                       (f"{fmt['height']}p, " if fmt['height'] else "") +
                                       f"vcodec={fmt['vcodec']}, acodec={fmt['acodec']}, " +
                                       f"HLS={fmt['is_hls']}", 'debug')
                
            else:
                diagnostics['issues_found'].append("No formats found in metadata")
                self.debug_print("No formats found in video metadata", 'error')
            
            # Test 4: Format selector validation (CRITICAL TEST)
            self.debug_print("", 'info')
            self.debug_print("TEST 4: Testing format selectors", 'info')
            self.debug_print("-" * 70, 'info')
            
            if diagnostics['recommended_format']:
                # Test the recommended format
                self.debug_print(f"Testing recommended format: '{diagnostics['recommended_format']}'", 'progress')
                try:
                    test_opts = {
                        'format': diagnostics['recommended_format'],
                        'quiet': True,
                        'no_warnings': True,
                        'simulate': True
                    }
                    with yt_dlp.YoutubeDL(test_opts) as test_ydl:
                        test_ydl.extract_info(url, download=False)
                    diagnostics['tested_working_format'] = diagnostics['recommended_format']
                    self.debug_print(f"Recommended format '{diagnostics['recommended_format']}' works!", 'success')
                except Exception as e:
                    self.debug_print(f"Recommended format failed: {str(e)}", 'error')
                    diagnostics['issues_found'].append(f"Recommended format failed: {str(e)}")
                
                # Test generic selectors (to show they DON'T work for separated HLS)
                if diagnostics['hls_separated_streams']:
                    self.debug_print("Testing generic 'best' selector (expected to FAIL for separated HLS)", 'progress')
                    try:
                        test_opts = {
                            'format': 'best',
                            'quiet': True,
                            'no_warnings': True,
                            'simulate': True
                        }
                        with yt_dlp.YoutubeDL(test_opts) as test_ydl:
                            test_ydl.extract_info(url, download=False)
                        self.debug_print("Generic 'best' works (unexpected!)", 'warning')
                        diagnostics['fallback_safe'] = True
                    except Exception as e:
                        self.debug_print(f"Generic 'best' failed as expected: {str(e)[:100]}...", 'info')
                        self.debug_print("This confirms we MUST use explicit format combination", 'warning')
                        diagnostics['fallback_safe'] = False
        
        except Exception as e:
            diagnostics['issues_found'].append(f"Diagnostic test failed: {str(e)}")
            self.debug_print(f"Diagnostic test failed: {str(e)}", 'error')
        
        # Summary
        self.debug_print("", 'info')
        self.debug_print("=" * 70, 'info')
        self.debug_print("DIAGNOSTIC SUMMARY", 'info')
        self.debug_print("=" * 70, 'info')
        self.debug_print(f"URL Accessible: {diagnostics['url_accessible']}", 'info')
        self.debug_print(f"Metadata Extraction: {diagnostics['metadata_extraction']}", 'info')
        self.debug_print(f"Format Detection: {diagnostics['format_detection']}", 'info')
        self.debug_print(f"Total Formats: {diagnostics['format_count']}", 'info')
        self.debug_print(f"HLS Detected: {diagnostics['hls_detected']}", 'info')
        self.debug_print(f"HLS Separated Streams: {diagnostics['hls_separated_streams']}", 'info')
        self.debug_print(f"Generic Selectors Safe: {diagnostics['fallback_safe']}", 'info')
        if diagnostics.get('tested_working_format'):
            self.debug_print(f"Verified Working Format: {diagnostics['tested_working_format']}", 'success')
        if diagnostics.get('issues_found'):
            self.debug_print(f"Issues Found: {len(diagnostics['issues_found'])}", 'warning')
            for issue in diagnostics['issues_found']:
                self.debug_print(f"  - {issue}", 'warning')
        self.debug_print("=" * 70, 'info')
        
        # Store diagnostics
        self.diagnostic_data = diagnostics
        
        # Store the optimal format if found
        if diagnostics.get('tested_working_format'):
            self.optimal_format_found = diagnostics['tested_working_format']
        
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
                    f"⬇️ Downloading: {percent:.1f}% | "
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
            self.logger.info(f"✅ Download completed: {os.path.basename(filename)}")
            
        elif d['status'] == 'error':
            self.logger.error(f"❌ Download error: {d.get('error', 'Unknown error')}")
    
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
                
                return info
                
        except Exception as e:
            self.logger.error(f"Failed to extract video info: {str(e)}")
            raise
    
    def download_video(self, url: str) -> bool:
        """Download video with configured parameters and enhanced diagnostics."""
        self.debug_print("=" * 70, 'info')
        self.debug_print("STARTING DOWNLOAD PROCESS", 'info')
        self.debug_print("=" * 70, 'info')
        
        # Ensure output directory exists
        output_dir = Path(self.config['output_dir'])
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Run comprehensive diagnostics first
        self.debug_print("Running pre-download diagnostics...", 'progress')
        diagnostics = self.run_diagnostic_tests(url)
        
        if not diagnostics['url_accessible']:
            self.debug_print("URL not accessible, aborting download", 'error')
            return False
        
        if not diagnostics['format_detection']:
            self.debug_print("No formats detected, aborting download", 'error')
            return False
        
        # CRITICAL: Determine format strategy based on diagnostics
        self.debug_print("", 'info')
        self.debug_print("DETERMINING DOWNLOAD STRATEGY", 'info')
        self.debug_print("-" * 70, 'info')
        
        format_options = []
        
        # If we have a tested working format, prioritize it
        if diagnostics.get('tested_working_format'):
            format_options.append(diagnostics['tested_working_format'])
            self.debug_print(f"Priority #1: Tested working format: {diagnostics['tested_working_format']}", 'success')
        
        # Handle HLS separated streams (IBM video case)
        if diagnostics.get('hls_separated_streams'):
            self.debug_print("Detected HLS with separated streams (IBM/Ustream pattern)", 'warning')
            self.debug_print("Building format options for video+audio combination", 'info')
            
            video_only_formats = [
                f for f in diagnostics.get('available_formats', []) 
                if f.get('is_hls') and f.get('height') and f.get('vcodec') != 'none' and f.get('acodec') == 'none'
            ]
            audio_only_formats = [
                f for f in diagnostics.get('available_formats', []) 
                if f.get('is_hls') and f.get('vcodec') == 'none' and f.get('acodec') != 'none'
            ]
            
            if video_only_formats and audio_only_formats:
                # Sort by quality
                video_only_formats.sort(key=lambda x: x.get('height', 0), reverse=True)
                
                # Add top quality combinations
                for video in video_only_formats[:3]:  # Top 3 video qualities
                    for audio in audio_only_formats[:1]:  # Best audio
                        combo = f"{video['id']}+{audio['id']}"
                        if combo not in format_options:
                            format_options.append(combo)
                            self.debug_print(f"Format option: {combo} ({video['height']}p)", 'debug')
            
            # DO NOT add generic selectors for separated HLS
            self.debug_print("Skipping generic selectors (they won't work for separated HLS)", 'warning')
        
        # For combined HLS or non-HLS, generic selectors are safe
        elif diagnostics.get('fallback_safe'):
            self.debug_print("Generic selectors are safe for this video", 'info')
            format_options.extend([
                'best+bestaudio/best',
                'best[ext=mp4]+bestaudio[ext=mp4]/best',
                'best',
            ])
        
        # Remove duplicates while preserving order
        format_options = list(dict.fromkeys(format_options))
        
        if not format_options:
            self.debug_print("No valid format options found!", 'error')
            return False
        
        self.debug_print(f"Total format options to try: {len(format_options)}", 'info')
        for i, fmt in enumerate(format_options):
            self.debug_print(f"  Option {i+1}: {fmt}", 'debug')
        
        # Configure yt-dlp options
        base_ydl_opts = {
            # Output settings
            'outtmpl': str(output_dir / self.config['output_template']),
            
            # Download settings
            'retries': self.config['retries'],
            'fragment_retries': self.config['fragment_retries'],
            'concurrent_fragment_downloads': self.config['concurrent_fragments'],
            
            # CRITICAL: Add sleep between downloads to avoid 403 errors
            'sleep_interval': 2,  # Wait 2 seconds between fragments
            'max_sleep_interval': 5,  # Random sleep up to 5 seconds
            
            # Keep partial downloads in case of failure
            'keepvideo': True,
            'nopart': False,  # Keep .part files
            
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
        # NOTE: For HLS video+audio merging, yt-dlp handles this automatically
        # when using format selector like "video+audio". No post-processor needed.
        # Only add post-processors for format conversion if specifically requested
        postprocessors = []
        
        # Check if post-processing is disabled
        if self.config.get('skip_postprocessing'):
            self.debug_print("Post-processing disabled by user", 'info')
        else:
            # Only add format converter if user wants a specific output format
            # and it differs from the source format
            if self.config.get('merge_output_format') and self.config['merge_output_format'] != 'mp4':
                self.debug_print(f"Adding format converter to {self.config['merge_output_format']}", 'info')
                postprocessors.append({
                    'key': 'FFmpegVideoConvertor',
                    'preferedformat': self.config['merge_output_format'],
                })
        
        if postprocessors:
            base_ydl_opts['postprocessors'] = postprocessors
        
        # Try each format option
        self.debug_print("", 'info')
        self.debug_print("ATTEMPTING DOWNLOAD", 'info')
        self.debug_print("-" * 70, 'info')
        
        for i, format_selector in enumerate(format_options):
            try:
                self.debug_print(f"", 'progress')
                self.debug_print(f"Attempt {i+1}/{len(format_options)}: Format '{format_selector}'", 'progress')
                
                ydl_opts = base_ydl_opts.copy()
                ydl_opts['format'] = format_selector
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                
                self.debug_print("", 'success')
                self.debug_print(f"Download completed successfully with format: {format_selector}", 'success')
                self.debug_print("=" * 70, 'success')
                return True
                
            except yt_dlp.DownloadError as e:
                error_msg = str(e)
                self.debug_print(f"Format '{format_selector}' failed: {error_msg[:150]}...", 'warning')
                
                # Check if it's a format-specific error
                if "Requested format is not available" in error_msg:
                    self.debug_print("  Reason: Format not available (trying next option)", 'debug')
                    continue
                elif "No video formats found" in error_msg:
                    self.debug_print("  Reason: No video formats found (trying next option)", 'debug')
                    continue
                else:
                    self.debug_print(f"  Reason: Other download error", 'warning')
                    continue
                    
            except Exception as e:
                import traceback
                error_details = traceback.format_exc()
                self.debug_print(f"Unexpected error with format '{format_selector}':", 'error')
                self.debug_print(f"Error type: {type(e).__name__}", 'error')
                self.debug_print(f"Error message: {str(e)}", 'error')
                if self.debug_level == 'max':
                    self.debug_print(f"Full traceback:\n{error_details}", 'debug')
                continue
        
        # All formats failed
        self.debug_print("", 'error')
        self.debug_print("ALL FORMAT OPTIONS FAILED", 'error')
        self.debug_print("=" * 70, 'error')
        
        # Provide diagnostic summary
        self.debug_print("FAILURE ANALYSIS:", 'error')
        self.debug_print(f"  - URL accessible: {diagnostics.get('url_accessible', False)}", 'info')
        self.debug_print(f"  - Formats found: {diagnostics.get('format_count', 0)}", 'info')
        self.debug_print(f"  - HLS detected: {diagnostics.get('hls_detected', False)}", 'info')
        self.debug_print(f"  - HLS separated streams: {diagnostics.get('hls_separated_streams', False)}", 'info')
        self.debug_print(f"  - Format attempts: {len(format_options)}", 'info')
        if diagnostics.get('issues_found'):
            self.debug_print(f"  - Known issues:", 'warning')
            for issue in diagnostics['issues_found']:
                self.debug_print(f"    * {issue}", 'warning')
        
        return False
    
    def save_progress_report(self):
        """Save progress report to file."""
        if not self.progress_data and not self.diagnostic_data:
            return
            
        report_file = Path(self.config['output_dir']) / 'logs' / 'session_report.json'
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'config': self.config,
            'progress_data': self.progress_data,
            'diagnostic_data': self.diagnostic_data,
            'optimal_format_found': self.optimal_format_found
        }
        
        try:
            with open(report_file, 'w') as f:
                json.dump(report_data, f, indent=2, default=str)
            self.debug_print(f"Session report saved: {report_file}", 'info')
        except Exception as e:
            self.debug_print(f"Failed to save session report: {str(e)}", 'error')


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
    parser.add_argument('--no-postprocess', action='store_true',
                       help='Skip all post-processing (use if post-processors cause errors)')
    parser.add_argument('--video-only', action='store_true',
                       help='Download video-only stream (skip audio if getting 403 errors)')
    parser.add_argument('--external-downloader', default=None,
                       choices=['aria2c', 'ffmpeg', 'curl', 'wget'],
                       help='Use external downloader for better reliability')
    
    args = parser.parse_args()
    
    # Handle verbose flag
    if args.verbose:
        args.debug_level = 'max'
    
    # Create custom configuration based on arguments
    config = {
        'output_dir': args.output_dir,
        'output_template': '%(uploader)s - %(title)s.%(ext)s',
        'format_selector': f'best[ext={args.format}]/best',
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
        'merge_output_format': args.format if not args.no_postprocess else None,
        'keep_video': True,
        'verbose': args.debug_level != 'none',
        'log_level': 'DEBUG' if args.debug_level == 'max' else 'INFO',
        'skip_postprocessing': args.no_postprocess
    }
    
    # Initialize downloader with debug level
    downloader = VideoDownloader(config, debug_level=args.debug_level)
    
    try:
        if args.debug_level != 'none':
            print(f"\n{'='*70}")
            print(f"IBM Video Downloader v2.1 (FIXED - Debug: {args.debug_level.upper()})")
            print(f"{'='*70}")
            print(f"URL: {args.url}")
            print(f"Output Directory: {args.output_dir}")
            print(f"Quality: {args.quality}")
            print(f"Format: {args.format}")
            print(f"{'='*70}\n")
        
        # Run diagnostics if requested
        if args.diagnostics:
            diagnostics = downloader.run_diagnostic_tests(args.url)
            return
        
        # List formats if requested
        if args.list_formats:
            try:
                downloader.list_available_formats(args.url)
            except Exception:
                downloader.run_diagnostic_tests(args.url)
            return
        
        # Extract video information
        try:
            video_info = downloader.get_video_info(args.url)
        except Exception:
            diagnostics = downloader.run_diagnostic_tests(args.url)
            if not diagnostics.get('url_accessible'):
                print("URL is not accessible. Please check the URL and try again.")
                sys.exit(1)
            video_info = {'title': 'Unknown', 'duration': 'Unknown', 'uploader': 'Unknown'}
        
        if args.info_only:
            print(f"\nVIDEO INFORMATION:")
            print(f"Title: {video_info.get('title', 'N/A')}")
            print(f"Duration: {video_info.get('duration', 'N/A')} seconds")
            print(f"Uploader: {video_info.get('uploader', 'N/A')}")
            return
        
        # Download video
        print(f"\nSTARTING DOWNLOAD...\n")
        success = downloader.download_video(args.url)
        
        # Save progress report
        downloader.save_progress_report()
        
        if success:
            print(f"\n{'='*70}")
            print("DOWNLOAD COMPLETED SUCCESSFULLY!")
            print(f"Files saved to: {args.output_dir}")
            
            # Check for downloaded files
            video_files = list(Path(args.output_dir).glob("*.mp4"))
            if video_files:
                video_file = video_files[0]
                file_size = video_file.stat().st_size / (1024**3)
                print(f"Video: {video_file.name} ({file_size:.2f} GB)")
                
                print(f"\nTo play the video:")
                print(f"  macOS: open '{video_file}'")
                print(f"  or use: vlc '{video_file}'")
            
            print(f"{'='*70}")
        else:
            print(f"\n{'='*70}")
            print("DOWNLOAD FAILED")
            print("Troubleshooting:")
            print("  1. Run: --diagnostics")
            print("  2. Check log files in downloads/logs/")
            print(f"{'='*70}")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nDownload interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {str(e)}")
        if args.debug_level == 'none':
            print("Try using --debug-level max for detailed error information.")
        sys.exit(1)


if __name__ == "__main__":
    main()
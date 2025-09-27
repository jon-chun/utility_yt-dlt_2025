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
    
    def __init__(self, config: Dict[str, Any] = None):
        """Initialize the downloader with configuration."""
        self.config = config or self.get_default_config()
        self.setup_logging()
        self.progress_data = {}
        
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
        """Setup comprehensive logging system."""
        log_dir = Path(self.config['output_dir']) / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = log_dir / f'download_{timestamp}.log'
        
        # Configure logging
        logging.basicConfig(
            level=getattr(logging, self.config['log_level']),
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        
        self.logger = logging.getLogger(__name__)
        self.logger.info(f"Logging initialized. Log file: {log_file}")
        self.logger.info(f"Configuration: {json.dumps(self.config, indent=2)}")
    
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
        """Determine optimal format selector based on available formats."""
        try:
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
                self.logger.info(f"Adjusting format selector for max available resolution: {max_height}p")
                
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
            self.logger.warning(f"Could not determine optimal format, using fallback: {str(e)}")
            return 'best'
    
    def download_video(self, url: str) -> bool:
        """Download video with configured parameters."""
        self.logger.info(f"Starting download process for: {url}")
        
        # Ensure output directory exists
        output_dir = Path(self.config['output_dir'])
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine optimal format selector
        try:
            optimal_format = self.get_optimal_format_selector(url, self.config['video_quality'])
            self.logger.info(f"Using format selector: {optimal_format}")
        except Exception as e:
            self.logger.warning(f"Could not determine optimal format, using configured default: {str(e)}")
            optimal_format = self.config['format_selector']
        
        # Configure yt-dlp options
        ydl_opts = {
            # Output settings
            'outtmpl': str(output_dir / self.config['output_template']),
            
            # Quality settings - use optimal format
            'format': optimal_format,
            
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
            'quiet': not self.config['verbose'],
            'no_warnings': False,
            
            # Error handling
            'ignoreerrors': False,
        }
        
        # Add post-processors if needed
        if self.config['merge_output_format']:
            ydl_opts['postprocessors'] = [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': self.config['merge_output_format'],
            }]
        
        try:
            self.logger.info("Initializing yt-dlp...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                self.logger.info("Starting download...")
                ydl.download([url])
                
            self.logger.info("Download completed successfully!")
            return True
            
        except yt_dlp.DownloadError as e:
            self.logger.error(f"Download failed: {str(e)}")
            
            # Try with fallback format selector
            self.logger.info("Attempting download with fallback format selector...")
            ydl_opts['format'] = 'best'
            
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                self.logger.info("Download completed with fallback format!")
                return True
            except Exception as fallback_error:
                self.logger.error(f"Fallback download also failed: {str(fallback_error)}")
                return False
            
        except Exception as e:
            self.logger.error(f"Unexpected download error: {str(e)}")
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
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
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
        'verbose': args.verbose,
        'log_level': 'DEBUG' if args.verbose else 'INFO'
    }
    
    # Initialize downloader
    downloader = VideoDownloader(config)
    
    try:
        print(f"{'='*60}")
        print(f"IBM Video Downloader")
        print(f"URL: {args.url}")
        print(f"Output Directory: {args.output_dir}")
        print(f"Quality: {args.quality}")
        print(f"Format: {args.format}")
        print(f"{'='*60}")
        
        # List formats if requested
        if args.list_formats:
            downloader.list_available_formats(args.url)
            return
        
        # Extract video information
        video_info = downloader.get_video_info(args.url)
        
        if args.info_only:
            print("\nVideo Information:")
            print(f"Title: {video_info.get('title', 'N/A')}")
            print(f"Duration: {video_info.get('duration', 'N/A')} seconds")
            print(f"Uploader: {video_info.get('uploader', 'N/A')}")
            print(f"Description: {video_info.get('description', 'N/A')[:200]}...")
            return
        
        # Download video
        success = downloader.download_video(args.url)
        
        # Save progress report
        downloader.save_progress_report()
        
        if success:
            print(f"\n{'='*60}")
            print("Download completed successfully!")
            print(f"Files saved to: {args.output_dir}")
            print(f"{'='*60}")
        else:
            print("Download failed. Check logs for details.")
            print("Try using --list-formats to see available options.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nDownload interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        print("Try using --list-formats to debug format issues.")
        sys.exit(1)


if __name__ == "__main__":
    main()
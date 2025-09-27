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
            
            # Quality settings (popular defaults)
            'format_selector': 'best[height<=1080][ext=mp4]/best[ext=mp4]/best',
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
                
                # Log available formats
                if 'formats' in info:
                    self.logger.info(f"Available formats: {len(info['formats'])}")
                    for fmt in info['formats'][:5]:  # Show first 5 formats
                        quality_info = f"{fmt.get('format_id', 'N/A')} - {fmt.get('ext', 'N/A')}"
                        if fmt.get('height'):
                            quality_info += f" - {fmt['height']}p"
                        if fmt.get('filesize'):
                            quality_info += f" - {self._format_bytes(fmt['filesize'])}"
                        self.logger.info(f"  Format: {quality_info}")
                
                return info
                
        except Exception as e:
            self.logger.error(f"Failed to extract video info: {str(e)}")
            raise
    
    def download_video(self, url: str) -> bool:
        """Download video with configured parameters."""
        self.logger.info(f"Starting download process for: {url}")
        
        # Ensure output directory exists
        output_dir = Path(self.config['output_dir'])
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Configure yt-dlp options
        ydl_opts = {
            # Output settings
            'outtmpl': str(output_dir / self.config['output_template']),
            
            # Quality settings
            'format': self.config['format_selector'],
            
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
            
        except Exception as e:
            self.logger.error(f"Download failed: {str(e)}")
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
    parser.add_argument('--quality', '-q', default='1080p',
                       choices=['480p', '720p', '1080p', 'best'],
                       help='Video quality preference')
    parser.add_argument('--format', '-f', default='mp4',
                       choices=['mp4', 'webm', 'mkv'],
                       help='Output format preference')
    parser.add_argument('--info-only', action='store_true',
                       help='Only extract video information, do not download')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Create custom configuration based on arguments
    config = {
        'output_dir': args.output_dir,
        'output_template': '%(uploader)s - %(title)s.%(ext)s',
        'format_selector': f'best[height<={args.quality[:-1]}][ext={args.format}]/best[ext={args.format}]/best' if args.quality != 'best' else f'best[ext={args.format}]/best',
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
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nDownload interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
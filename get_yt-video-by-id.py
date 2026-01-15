#!/usr/bin/env python3
"""
YouTube Video Downloader by ID
Downloads YouTube videos with configurable quality, size, and subtitle language.

Requirements:
- yt-dlp (pip install yt-dlp)
- Deno JavaScript runtime (brew install deno) - required for YouTube JS challenges
- curl_cffi 0.11-0.13 (pip install "curl_cffi>=0.11,<0.14") - for impersonation
"""

import argparse
import sys
import traceback
from pathlib import Path

try:
    import yt_dlp
except ImportError:
    print("Error: yt-dlp not installed. Run: pip install yt-dlp")
    sys.exit(1)

# Check for ImpersonateTarget (optional, for curl_cffi support)
try:
    from yt_dlp.networking.impersonate import ImpersonateTarget
    HAS_IMPERSONATE = True
except ImportError:
    HAS_IMPERSONATE = False


# Resolution limits based on quality and size combinations
RESOLUTION_LIMITS = {
    ('low', 'low'): 360,
    ('low', 'medium'): 480,
    ('low', 'high'): 720,
    ('medium', 'low'): 480,
    ('medium', 'medium'): 720,
    ('medium', 'high'): 1080,
    ('high', 'low'): 720,
    ('high', 'medium'): 1080,
    ('high', 'high'): None,  # Best available
}


def get_format_selector(quality: str, size: str) -> str:
    """Build format selector string based on quality and size."""
    max_height = RESOLUTION_LIMITS.get((quality, size), 720)

    if max_height is None:
        # Best available - with extensive fallbacks
        return 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/bestvideo+bestaudio/best[ext=mp4]/best'
    else:
        # Height-limited with multiple fallbacks for YouTube's format restrictions
        return (
            f'bestvideo[height<={max_height}][ext=mp4]+bestaudio[ext=m4a]/'
            f'bestvideo[height<={max_height}]+bestaudio/'
            f'best[height<={max_height}][ext=mp4]/'
            f'best[height<={max_height}]/'
            f'bestvideo+bestaudio/'
            f'best[ext=mp4]/'
            f'best'
        )


def download_video(
    video_id: str,
    quality: str = 'low',
    size: str = 'low',
    language: str = 'en',
    output_dir: str = './downloads',
    use_cookies: bool = False
) -> bool:
    """
    Download a YouTube video by ID.

    Args:
        video_id: YouTube video ID
        quality: Video quality ('low', 'medium', 'high')
        size: Video size/resolution ('low', 'medium', 'high')
        language: Subtitle language code (default: 'en')
        output_dir: Output directory for downloads
        use_cookies: Whether to use browser cookies (for age-restricted content)

    Returns:
        True if download succeeded, False otherwise
    """
    url = f'https://www.youtube.com/watch?v={video_id}'
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    format_selector = get_format_selector(quality, size)

    ydl_opts = {
        'format': format_selector,
        'outtmpl': str(output_path / '%(title)s.%(ext)s'),
        'merge_output_format': 'mp4',

        # Subtitles
        'writesubtitles': True,
        'writeautomaticsub': True,
        'subtitleslangs': [language],
        'subtitlesformat': 'vtt',

        # Thumbnail
        'writethumbnail': True,

        # Network settings
        'retries': 5,
        'fragment_retries': 10,
        'concurrent_fragment_downloads': 4,
        'socket_timeout': 30,

        # YouTube-specific: use web_embedded which doesn't require PO tokens
        # This is the recommended workaround for 403 errors (Jan 2026)
        # Note: won't work for age-restricted or membership content
        'extractor_args': {
            'youtube': {
                'player_client': ['web_embedded', 'web'],
            }
        },

        # Enable remote components for JS challenge solver (required as of Nov 2025)
        'remote_components': ['ejs:github'],

        # Progress
        'progress_hooks': [progress_hook],
        'quiet': False,
        'no_warnings': False,
    }

    # Add impersonation if curl_cffi is available
    if HAS_IMPERSONATE:
        try:
            ydl_opts['impersonate'] = ImpersonateTarget.from_str('chrome-131:macos-14')
        except Exception:
            pass  # Skip if impersonation target not available

    # Add cookies for age-restricted content
    if use_cookies:
        ydl_opts['cookiesfrombrowser'] = ('chrome',)

    print(f"{'='*60}")
    print("YouTube Video Downloader")
    print(f"{'='*60}")
    print(f"Video ID: {video_id}")
    print(f"URL: {url}")
    print(f"Quality: {quality}")
    print(f"Size: {size}")
    print(f"Subtitles: {language}")
    print(f"Output: {output_dir}")
    print(f"Format: {format_selector}")
    print(f"Impersonation: {'enabled' if HAS_IMPERSONATE else 'disabled'}")
    print(f"Cookies: {'enabled' if use_cookies else 'disabled'}")
    print(f"{'='*60}")

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        print(f"\n{'='*60}")
        print("Download completed successfully!")
        print(f"Files saved to: {output_dir}")
        print(f"{'='*60}")
        return True
    except yt_dlp.utils.DownloadError as e:
        print(f"\nDownload error: {e}")
        return False
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        traceback.print_exc()
        return False


def progress_hook(d: dict):
    """Progress callback for yt-dlp."""
    if d['status'] == 'downloading':
        percent = d.get('_percent_str', 'N/A')
        speed = d.get('_speed_str', 'N/A')
        eta = d.get('_eta_str', 'N/A')
        print(f"\rDownloading: {percent} | Speed: {speed} | ETA: {eta}", end='', flush=True)
    elif d['status'] == 'finished':
        print(f"\nFinished downloading: {d.get('filename', 'Unknown')}")


def list_formats(video_id: str):
    """List available formats for a video."""
    url = f'https://www.youtube.com/watch?v={video_id}'
    print(f"Listing formats for: {url}\n")

    ydl_opts = {
        'quiet': True,
        'extractor_args': {
            'youtube': {
                'player_client': ['web_embedded', 'web'],
            }
        },
        'remote_components': ['ejs:github'],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            formats = info.get('formats', [])

            if not formats:
                print("No formats available.")
                return

            print(f"{'ID':<15} {'EXT':<6} {'RESOLUTION':<12} {'VCODEC':<15} {'ACODEC':<15}")
            print("-" * 70)
            for f in formats:
                fid = f.get('format_id', 'N/A')
                ext = f.get('ext', 'N/A')
                res = f"{f.get('width', '?')}x{f.get('height', '?')}" if f.get('height') else 'audio only'
                vcodec = (f.get('vcodec') or 'none')[:14]
                acodec = (f.get('acodec') or 'none')[:14]
                print(f"{fid:<15} {ext:<6} {res:<12} {vcodec:<15} {acodec:<15}")
    except Exception as e:
        print(f"Error listing formats: {e}")


def main():
    parser = argparse.ArgumentParser(
        description='Download YouTube videos by ID with configurable quality and size'
    )
    parser.add_argument(
        'video_id',
        nargs='?',
        default='L7gv9aGB7VY',
        help='YouTube video ID (default: L7gv9aGB7VY)'
    )
    parser.add_argument(
        '-q', '--quality',
        choices=['low', 'medium', 'high'],
        default='low',
        help='Video quality (default: low)'
    )
    parser.add_argument(
        '-s', '--size',
        choices=['low', 'medium', 'high'],
        default='low',
        help='Video size/resolution (default: low)'
    )
    parser.add_argument(
        '-l', '--language',
        default='en',
        help='Subtitle language code (default: en)'
    )
    parser.add_argument(
        '-o', '--output-dir',
        default='./downloads',
        help='Output directory (default: ./downloads)'
    )
    parser.add_argument(
        '--list-formats',
        action='store_true',
        help='List available formats without downloading'
    )
    parser.add_argument(
        '--cookies',
        action='store_true',
        help='Use Chrome browser cookies (for age-restricted content)'
    )

    args = parser.parse_args()

    if args.list_formats:
        list_formats(args.video_id)
        return

    success = download_video(
        video_id=args.video_id,
        quality=args.quality,
        size=args.size,
        language=args.language,
        output_dir=args.output_dir,
        use_cookies=args.cookies
    )

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

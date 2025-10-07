#!/usr/bin/env python3
"""
IBM Video Downloader using yt-dlp
Advanced video downloading script with configurable parameters and comprehensive logging.

Author: AI Research Team (revised)
Dependencies: yt-dlp, requests (optional)
"""

import os
import sys
import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import argparse
import re

try:
    import yt_dlp
    from yt_dlp.utils import DownloadError
except ImportError:
    print("Error: yt-dlp not installed. Run: pip install yt-dlp")
    sys.exit(1)


REDACT_KEYS = {"Cookie", "cookie", "Authorization", "authorization"}


def redact(d: Dict[str, Any]) -> Dict[str, Any]:
    """Redact sensitive values (shallow)."""
    if not isinstance(d, dict):
        return d
    out = {}
    for k, v in d.items():
        if any(k.endswith(x) or k == x for x in REDACT_KEYS):
            out[k] = "***REDACTED***"
        else:
            out[k] = v
    return out


class VideoDownloader:
    """Advanced video downloader with comprehensive logging and progress tracking."""

    def __init__(self, config: Dict[str, Any] = None, debug_level: str = 'max'):
        self.config = config or self.get_default_config()
        self.debug_level = debug_level.lower()
        self.config['debug_level'] = self.debug_level
        self.setup_logging()
        self.progress_data: Dict[str, Any] = {}
        self.diagnostic_data: Dict[str, Any] = {}
        self.force_audio_combination = False
        self.fail_reasons: List[str] = []

    def get_default_config(self) -> Dict[str, Any]:
        return {
            # Output settings
            'output_dir': './downloads',
            'output_template': '%(uploader)s - %(title)s.%(ext)s',

            # Quality / format selection
            'format_selector': 'best[ext=mp4]/best',
            'video_quality': 'best',
            'audio_quality': 'best',

            # Download preferences
            'prefer_free_formats': True,
            'extract_subtitles': True,
            'auto_subtitles': True,
            'embed_subtitles': False,
            'download_thumbnail': True,
            'embed_thumbnail': False,

            # Network / extractor settings (strengthened)
            'retries': 3,
            'fragment_retries': 5,
            'concurrent_fragments': 4,
            'extractor_retries': 5,
            'socket_timeout': 30,
            'geo_bypass_country': 'US',
            'hls_prefer_native': True,   # often more tolerant for IBM/Ustream
            'hls_use_mpegts': True,      # better for discontinuities

            # Post-processing
            'merge_output_format': 'mp4',
            'keep_video': True,

            # Optional cookies / headers
            'cookies': None,
            'cookies_from_browser': None,
            'http_headers': {
                # IBM Video/Ustream endpoints care about these:
                # (The actual page URL is safest as Referer)
                'Referer': 'https://video.ibm.com/',
                'Origin': 'https://video.ibm.com',
                'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                              '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            },

            # Logging
            'verbose': True,
            'log_level': 'INFO'
        }

    def setup_logging(self):
        log_dir = Path(self.config['output_dir']) / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        log_file = log_dir / f'download_{timestamp}.log'

        if self.debug_level == 'none':
            log_level = logging.WARNING
            console_level = logging.ERROR
        elif self.debug_level == 'min':
            log_level = logging.INFO
            console_level = logging.INFO
        else:
            log_level = logging.DEBUG
            console_level = logging.DEBUG

        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ],
            force=True
        )
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(log_level)
        self.logger.info(f"🔧 Debug level: {self.debug_level}")
        self.logger.info(f"📝 Log file: {log_file}")
        self.logger.debug(f"🧩 Effective Configuration:\n{json.dumps(self._safe_config_snapshot(), indent=2)}")

    def _safe_config_snapshot(self) -> Dict[str, Any]:
        cfg = dict(self.config)
        cfg['http_headers'] = redact(cfg.get('http_headers', {}))
        return cfg

    def debug_print(self, message: str, level: str = 'info'):
        if self.debug_level == 'none':
            return
        if self.debug_level == 'min' and level == 'debug':
            return
        prefix = {
            'debug': "🔍 DEBUG:",
            'info': "ℹ️  INFO:",
            'warning': "⚠️  WARNING:",
            'error': "❌ ERROR:"
        }.get(level, "ℹ️  INFO:")
        getattr(self.logger, level if level in ('debug', 'info', 'warning', 'error') else 'info')(f"{prefix} {message}")

    # ---------- Diagnostics ----------

    def _base_ydl_opts(self, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Centralize yt-dlp options so all paths use the same network/extractor settings."""
        opts = {
            'retries': self.config['retries'],
            'fragment_retries': self.config['fragment_retries'],
            'concurrent_fragment_downloads': self.config['concurrent_fragments'],
            'extractor_retries': self.config.get('extractor_retries', 3),
            'socket_timeout': self.config.get('socket_timeout', 20),
            'geo_bypass_country': self.config.get('geo_bypass_country', 'US'),
            'http_headers': self.config.get('http_headers') or {},
            'hls_prefer_native': self.config.get('hls_prefer_native', True),
            'hls_use_mpegts': self.config.get('hls_use_mpegts', True),
            'quiet': not self.config['verbose'] or self.debug_level == 'none',
            'no_warnings': self.debug_level == 'none',
        }
        if self.config.get('cookies'):
            opts['cookiefile'] = self.config['cookies']
        if self.config.get('cookies_from_browser'):
            opts['cookiesfrombrowser'] = self.config['cookies_from_browser']

        if extra:
            opts.update(extra)
        return opts

    def run_diagnostic_tests(self, url: str) -> Dict[str, Any]:
        self.debug_print("Starting comprehensive diagnostic tests", 'info')
        diagnostics = {
            'url_accessible': False,
            'metadata_extraction': False,
            'format_detection': False,
            'format_count': 0,
            'hls_detected': False,
            'available_formats': [],
            'recommended_format': None,
            'issues_found': [],
            'test_selectors': {}
        }

        try:
            # Test 1: URL accessibility / metadata
            self.debug_print("Test 1: Checking URL accessibility & metadata", 'info')
            ydl_opts_basic = self._base_ydl_opts({'quiet': True, 'no_warnings': True})
            info = None
            with yt_dlp.YoutubeDL(ydl_opts_basic) as ydl:
                try:
                    info = ydl.extract_info(url, download=False)
                    diagnostics['url_accessible'] = True
                    self.debug_print("✅ URL is accessible", 'info')
                except Exception as e:
                    diagnostics['issues_found'].append(f"URL not accessible: {str(e)}")
                    self.debug_print(f"URL not accessible: {str(e)}", 'error')
                    return diagnostics

            # Test 2: Metadata fields
            self.debug_print("Test 2: Testing metadata extraction", 'info')
            if info and info.get('title'):
                diagnostics['metadata_extraction'] = True
                self.debug_print(f"✅ Metadata extracted: {info.get('title')}", 'info')
            else:
                diagnostics['issues_found'].append("No metadata found")
                self.debug_print("No metadata found", 'warning')

            # Test 3: Formats
            self.debug_print("Test 3: Analyzing available formats", 'info')
            formats = (info or {}).get('formats', []) or []
            diagnostics['format_count'] = len(formats)
            if formats:
                diagnostics['format_detection'] = True
                self.debug_print(f"✅ Found {len(formats)} formats", 'info')

                fmtz = []
                hls_formats, video_only, audio_only, combined = [], [], [], []
                for fmt in formats:
                    fid = fmt.get('format_id', 'unknown')
                    ext = fmt.get('ext', 'unknown')
                    height = fmt.get('height')
                    vcodec = fmt.get('vcodec', 'unknown')
                    acodec = fmt.get('acodec', 'unknown')
                    is_hls = str(fid).startswith('hls-') or (fmt.get('protocol') == 'm3u8' or fmt.get('protocol') == 'm3u8_native')
                    rec = {
                        'id': fid,
                        'ext': ext,
                        'height': height,
                        'vcodec': vcodec,
                        'acodec': acodec,
                        'is_hls': is_hls
                    }
                    fmtz.append(rec)

                    if is_hls:
                        hls_formats.append(rec)
                        if height and vcodec != 'none' and (acodec in (None, 'none')):
                            video_only.append(rec)
                        elif (not height) and (vcodec == 'none') and acodec and acodec != 'none':
                            audio_only.append(rec)
                        elif height and vcodec != 'none' and acodec and acodec != 'none':
                            combined.append(rec)

                diagnostics['available_formats'] = fmtz
                diagnostics['hls_detected'] = len(hls_formats) > 0
                diagnostics['video_only_count'] = len(video_only)
                diagnostics['audio_only_count'] = len(audio_only)
                diagnostics['combined_count'] = len(combined)

                if diagnostics['hls_detected']:
                    self.debug_print(f"🎯 HLS detected: {len(hls_formats)} HLS formats found", 'info')
                    self.debug_print(f"   - Video-only streams: {len(video_only)}", 'info')
                    self.debug_print(f"   - Audio-only streams: {len(audio_only)}", 'info')
                    self.debug_print(f"   - Combined streams: {len(combined)}", 'info')

                    if combined:
                        best_combined = max(combined, key=lambda x: x.get('height') or 0)
                        diagnostics['recommended_format'] = best_combined['id']
                        self.debug_print(f"🎯 Recommended combined format: {best_combined['id']} ({best_combined.get('height')}p)", 'info')
                    elif video_only and audio_only:
                        best_video = max(video_only, key=lambda x: x.get('height') or 0)
                        best_audio = audio_only[0]
                        sel = f"{best_video['id']}+{best_audio['id']}"
                        diagnostics['recommended_format'] = sel
                        self.debug_print(f"🎯 Recommended video+audio combination: {sel}", 'info')
                    elif video_only:
                        best_video = max(video_only, key=lambda x: x.get('height') or 0)
                        diagnostics['recommended_format'] = best_video['id']
                        diagnostics['issues_found'].append("No audio streams detected - video only")
                        self.debug_print(f"Video-only format (no audio): {best_video['id']}", 'warning')
            else:
                diagnostics['issues_found'].append("No formats found in metadata")
                self.debug_print("No formats found", 'error')

            # Test 4: Validate a few selectors (simulate)
            self.debug_print("Test 4: Testing format selectors (simulate)", 'info')
            to_test = [sel for sel in [
                diagnostics.get('recommended_format'),
                'bestvideo+bestaudio/best',
                'best',
                'worst'
            ] if sel]
            for selector in to_test:
                test_opts = self._base_ydl_opts({'format': selector, 'simulate': True, 'quiet': True, 'no_warnings': True})
                ok = True
                err = None
                try:
                    with yt_dlp.YoutubeDL(test_opts) as ydl:
                        ydl.extract_info(url, download=False)
                    self.debug_print(f"✅ Selector works: {selector}", 'info')
                except Exception as e:
                    ok = False
                    err = str(e)
                    self.debug_print(f"Selector FAILED: {selector} -> {err}", 'warning')
                diagnostics['test_selectors'][selector] = {'ok': ok, 'error': err}

        except Exception as e:
            diagnostics['issues_found'].append(f"Diagnostic test failed: {str(e)}")
            self.debug_print(f"Diagnostic test failed: {str(e)}", 'error')

        self.diagnostic_data = diagnostics
        self._write_network_debug(url, phase="diagnostics")
        return diagnostics

    # ---------- Progress / Utilities ----------

    def progress_hook(self, d: Dict[str, Any]):
        if d['status'] == 'downloading':
            filename = d.get('filename', 'Unknown')
            if 'total_bytes' in d and d['total_bytes']:
                percent = (d['downloaded_bytes'] / d['total_bytes']) * 100
            else:
                percent = 0.0
            speed = d.get('speed', 0)
            eta = d.get('eta', 0)
            self.logger.info(
                f"⬇️  Downloading: {percent:.1f}% | "
                f"Speed: {self._format_bytes(speed)}/s | "
                f"ETA: {eta}s | "
                f"File: {os.path.basename(filename)}"
            )
            self.progress_data[filename] = {
                'percent': percent,
                'speed': speed,
                'eta': eta,
                'downloaded': d.get('downloaded_bytes'),
                'total': d.get('total_bytes')
            }
        elif d['status'] == 'finished':
            filename = d.get('filename', 'Unknown')
            self.logger.info(f"✅ Download finished: {os.path.basename(filename)}")
        elif d['status'] == 'error':
            self.logger.error(f"❌ Download error: {d.get('error', 'Unknown error')}")

    def _format_bytes(self, bytes_val: Optional[float]) -> str:
        if bytes_val is None:
            return "N/A"
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_val < 1024.0:
                return f"{bytes_val:.1f}{unit}"
            bytes_val /= 1024.0
        return f"{bytes_val:.1f}TB"

    # ---------- Info & Formats ----------

    def list_available_formats(self, url: str) -> List[Dict[str, Any]]:
        self.logger.info(f"📋 Listing available formats for: {url}")
        ydl_opts = self._base_ydl_opts({'extract_flat': False})

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = info.get('formats', []) or []
        except DownloadError as e:
            self.logger.error(f"Extractor says no formats: {str(e)}")
            self.logger.info("🔧 Falling back to diagnostics-derived formats…")
            diags = self.run_diagnostic_tests(url)
            formats = self._formats_from_diags(diags)
        except Exception as e:
            self.logger.error(f"Failed to list formats: {str(e)}")
            self.logger.info("🔧 Falling back to diagnostics-derived formats…")
            diags = self.run_diagnostic_tests(url)
            formats = self._formats_from_diags(diags)

        self._pretty_print_formats(formats)
        return formats

    def _formats_from_diags(self, diagnostics: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Convert our diagnostic entries into yt-dlp-like rows for printing
        fmt_list = []
        for f in diagnostics.get('available_formats', []):
            fmt_list.append({
                'format_id': f['id'],
                'ext': f.get('ext', 'mp4'),
                'height': f.get('height'),
                'vcodec': f.get('vcodec', 'unknown'),
                'acodec': f.get('acodec', 'unknown'),
            })
        return fmt_list

    def _pretty_print_formats(self, formats: List[Dict[str, Any]]):
        self.logger.info(f"📊 Total available formats (after fallback if any): {len(formats)}")
        print(f"\n{'='*80}")
        print("AVAILABLE FORMATS (Extractor + Diagnostics Fallback):")
        print(f"{'='*80}")
        if not formats:
            print("  (No formats found)")
            return
        for i, fmt in enumerate(formats):
            fid = fmt.get('format_id') or fmt.get('id', 'N/A')
            ext = fmt.get('ext', 'N/A')
            height = fmt.get('height')
            vcodec = fmt.get('vcodec', 'N/A')
            acodec = fmt.get('acodec', 'N/A')
            print(f"{i+1:2d}. Format ID: {fid}")
            print(f"    Extension: {ext}")
            if height:
                print(f"    Height: {height}p")
            else:
                print(f"    Height: N/A")
            print(f"    Video Codec: {vcodec}")
            print(f"    Audio Codec: {acodec}")
            print()

    def get_video_info(self, url: str) -> Dict[str, Any]:
        self.logger.info(f"🔎 Extracting video information for: {url}")
        ydl_opts = self._base_ydl_opts({'extract_flat': False})
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
        # Short, high-signal log lines:
        self.logger.info(f"🎞️  Title: {info.get('title', 'N/A')}")
        self.logger.info(f"⏱️  Duration: {info.get('duration', 'N/A')} s")
        self.logger.info(f"👤 Uploader: {info.get('uploader', 'N/A')}")
        self.logger.info(f"🧮 Formats: {len(info.get('formats', []) or [])}")
        return info

    # ---------- Format Selection ----------

    def get_optimal_format_selector(self, url: str, preferred_quality: str = "best") -> str:
        try:
            self.debug_print("Select optimal format via diagnostics", 'info')
            diagnostics = self.run_diagnostic_tests(url)

            if not diagnostics.get('format_detection'):
                self.debug_print("No formats detected, using fallback 'bestvideo+bestaudio/best'", 'warning')
                return 'bestvideo+bestaudio/best'

            if diagnostics.get('hls_detected'):
                fmts = diagnostics.get('available_formats', [])
                video_streams = [f for f in fmts if f.get('height') and f.get('vcodec') != 'none']
                audio_streams = [f for f in fmts if (not f.get('height')) and f.get('vcodec') == 'none' and f.get('acodec') != 'none']
                combined_streams = [f for f in fmts if f.get('height') and f.get('acodec') not in (None, 'none')]

                if combined_streams:
                    best_combined = max(combined_streams, key=lambda x: x.get('height') or 0)
                    sel = best_combined['id']
                    self.debug_print(f"Using combined HLS stream: {sel}", 'info')
                    return sel
                elif video_streams and audio_streams:
                    best_video = max(video_streams, key=lambda x: x.get('height') or 0)
                    best_audio = audio_streams[0]
                    sel = f"{best_video['id']}+{best_audio['id']}"
                    self.debug_print(f"Combining HLS video+audio: {sel}", 'info')
                    return sel
                elif video_streams:
                    best_video = max(video_streams, key=lambda x: x.get('height') or 0)
                    self.debug_print(f"Only video streams present, selecting: {best_video['id']} (⚠️ may be silent)", 'warning')
                    return best_video['id']

            # Non-HLS or no height info
            info = self.get_video_info(url)
            formats = info.get('formats', []) or []
            if not formats:
                return 'bestvideo+bestaudio/best'

            exts = [f.get('ext') for f in formats if f.get('ext')]
            height_vals = [f.get('height') for f in formats if f.get('height')]

            ext_priority = ['mp4', 'webm', 'mkv', 'flv']
            best_ext = next((e for e in ext_priority if e in exts), None)

            if height_vals:
                max_h = max(height_vals)
                if preferred_quality == "best":
                    return f"bestvideo[ext={best_ext}]+bestaudio/best" if best_ext else "bestvideo+bestaudio/best"
                else:
                    try:
                        pref_h = int(preferred_quality.replace('p', ''))
                        target = min(pref_h, max_h)
                        if best_ext:
                            return f"bestvideo[height<={target}][ext={best_ext}]+bestaudio/best"
                        return f"bestvideo[height<={target}]+bestaudio/best"
                    except ValueError:
                        return f"bestvideo[ext={best_ext}]+bestaudio/best" if best_ext else "bestvideo+bestaudio/best"
            else:
                return f"bestvideo[ext={best_ext}]+bestaudio/best" if best_ext else "bestvideo+bestaudio/best"
        except Exception as e:
            self.debug_print(f"Could not determine optimal format: {str(e)}", 'warning')
            return 'bestvideo+bestaudio/best'

    # ---------- Download ----------

    def download_video(self, url: str) -> bool:
        self.debug_print(f"Starting download for: {url}", 'info')

        output_dir = Path(self.config['output_dir'])
        output_dir.mkdir(parents=True, exist_ok=True)

        self.debug_print("Pre-download diagnostics", 'info')
        diagnostics = self.run_diagnostic_tests(url)

        if not diagnostics.get('url_accessible'):
            self.debug_print("URL not accessible, aborting", 'error')
            return False

        # Determine optimal selector and full fallback chain
        try:
            optimal_format = diagnostics.get('recommended_format') or self.get_optimal_format_selector(url, self.config['video_quality'])
        except Exception as e:
            self.debug_print(f"Optimal format derivation failed, using default: {str(e)}", 'warning')
            optimal_format = self.config['format_selector']

        format_options: List[str] = []

        if diagnostics.get('hls_detected'):
            v_only = [f for f in diagnostics.get('available_formats', []) if f.get('is_hls') and f.get('height') and f.get('vcodec') != 'none' and (f.get('acodec') in (None, 'none'))]
            a_only = [f for f in diagnostics.get('available_formats', []) if f.get('is_hls') and (not f.get('height')) and f.get('vcodec') == 'none' and f.get('acodec') not in (None, 'none')]
            combined = [f for f in diagnostics.get('available_formats', []) if f.get('is_hls') and f.get('height') and f.get('acodec') not in (None, 'none')]

            if combined:
                combined.sort(key=lambda x: x.get('height', 0), reverse=True)
                format_options.extend([f['id'] for f in combined[:3]])

            if v_only and a_only:
                v_only.sort(key=lambda x: x.get('height', 0), reverse=True)
                for v in v_only[:3]:
                    for a in a_only[:2]:
                        format_options.append(f"{v['id']}+{a['id']}")

            if v_only:
                format_options.extend([f['id'] for f in v_only[:2]])  # may be silent

        # Generic fallbacks (ordered)
        format_options.extend([
            optimal_format,
            'bestvideo+bestaudio/best',
            'best[ext=mp4]+bestaudio[ext=mp4]/best',
            'bestvideo/best',
            'best',
            'worst'
        ])

        # Dedup in-order
        seen = set()
        uniq_options = []
        for sel in format_options:
            if sel and sel not in seen:
                uniq_options.append(sel)
                seen.add(sel)
        format_options = uniq_options

        self.debug_print(f"Format options to try (first 6): {format_options[:6]}{' ...' if len(format_options)>6 else ''}", 'debug')

        # Base yt-dlp options
        ydl_base = self._base_ydl_opts({
            'outtmpl': str(output_dir / self.config['output_template']),
            'merge_output_format': self.config['merge_output_format'],
            'keepvideo': self.config['keep_video'],
            'writesubtitles': self.config['extract_subtitles'],
            'writeautomaticsub': self.config['auto_subtitles'],
            'embedsubtitles': self.config['embed_subtitles'],
            'writethumbnail': self.config['download_thumbnail'],
            'embedthumbnail': self.config['embed_thumbnail'],
            'progress_hooks': [self.progress_hook],
            'ignoreerrors': False
        })

        # Post-processors
        postprocessors = []
        if self.config['merge_output_format']:
            postprocessors.append({'key': 'FFmpegVideoConvertor', 'preferedformat': self.config['merge_output_format']})
        if diagnostics.get('hls_detected'):
            self.debug_print("Adding FFmpeg remux for HLS compatibility", 'info')
            postprocessors.append({'key': 'FFmpegVideoRemux', 'preferedformat': self.config['merge_output_format'] or 'mp4'})
        if postprocessors:
            ydl_base['postprocessors'] = postprocessors

        # Try formats in order
        for i, selector in enumerate(format_options, 1):
            try:
                self.debug_print(f"[{i}/{len(format_options)}] Try selector: {selector}", 'info')
                ydl_opts = dict(ydl_base)
                ydl_opts['format'] = selector
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
                self.debug_print(f"✅ Download OK with: {selector}", 'info')
                self._write_network_debug(url, phase="download_ok", extra={'selector': selector})
                return True
            except DownloadError as e:
                msg = str(e)
                self.fail_reasons.append(f"{selector}: {msg}")
                # Make common failures explicit in logs:
                if "Requested format is not available" in msg:
                    self.debug_print(f"Selector failed (not available): {selector}", 'warning')
                    continue
                elif "No video formats found" in msg:
                    self.debug_print(f"No formats found via selector: {selector}", 'warning')
                    continue
                else:
                    self.debug_print(f"Serious download error ({selector}): {msg}", 'error')
                    continue
            except Exception as e:
                self.fail_reasons.append(f"{selector}: {str(e)}")
                self.debug_print(f"Unexpected error ({selector}): {str(e)}", 'error')
                continue

        # Last-ditch fallback
        self.debug_print("All selectors failed, trying final naive fallback", 'warning')
        try:
            final_opts = self._base_ydl_opts({
                'outtmpl': str(output_dir / self.config['output_template']),
                'quiet': False,
                'no_warnings': False,
            })
            with yt_dlp.YoutubeDL(final_opts) as ydl:
                ydl.download([url])
            self.debug_print("✅ Final naive fallback succeeded", 'info')
            self._write_network_debug(url, phase="download_ok_fallback")
            return True
        except Exception as final_error:
            self.debug_print(f"Final fallback failed: {str(final_error)}", 'error')
            self._dump_failure_summary(diagnostics, format_options)
            self._write_network_debug(url, phase="download_failed", extra={'final_error': str(final_error)})
            return False

    # ---------- Verification / Reports ----------

    def verify_video_file(self, file_path: Path) -> Dict[str, Any]:
        verification = {
            'exists': False,
            'playable': False,
            'duration': None,
            'size_mb': 0,
            'issues': []
        }
        try:
            if file_path.exists():
                verification['exists'] = True
                verification['size_mb'] = file_path.stat().st_size / (1024**2)
                try:
                    import subprocess
                    result = subprocess.run(
                        ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', str(file_path)],
                        capture_output=True, text=True, timeout=30
                    )
                    if result.returncode == 0:
                        probe_data = json.loads(result.stdout)
                        if 'format' in probe_data:
                            verification['playable'] = True
                            verification['duration'] = float(probe_data['format'].get('duration', 0))
                    else:
                        verification['issues'].append("ffprobe non-zero exit")
                except (subprocess.TimeoutExpired, FileNotFoundError, json.JSONDecodeError):
                    verification['issues'].append("ffprobe unavailable or parse error")
                except Exception as e:
                    verification['issues'].append(f"ffprobe error: {str(e)}")
            else:
                verification['issues'].append("File not found")
        except Exception as e:
            verification['issues'].append(f"File access error: {str(e)}")
        return verification

    def save_progress_report(self):
        if not self.progress_data and not self.diagnostic_data:
            return
        report_file = Path(self.config['output_dir']) / 'logs' / 'session_report.json'
        report = {
            'timestamp': datetime.now().isoformat(),
            'config': self._safe_config_snapshot(),
            'progress_data': self.progress_data,
            'diagnostic_data': self.diagnostic_data,
            'fail_reasons': self.fail_reasons
        }
        try:
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            self.debug_print(f"Session report saved: {report_file}", 'info')
        except Exception as e:
            self.debug_print(f"Failed to save session report: {str(e)}", 'error')

    def _dump_failure_summary(self, diagnostics: Dict[str, Any], format_options: List[str]):
        self.debug_print("📊 Download failure summary:", 'error')
        self.debug_print(f"  - URL accessible: {diagnostics.get('url_accessible', False)}", 'error')
        self.debug_print(f"  - Formats found: {diagnostics.get('format_count', 0)}", 'error')
        self.debug_print(f"  - HLS detected: {diagnostics.get('hls_detected', False)}", 'error')
        self.debug_print(f"  - Selectors tried: {len(format_options)}", 'error')
        for fr in self.fail_reasons[-10:]:
            self.debug_print(f"  - Reason: {fr}", 'error')

    def _write_network_debug(self, url: str, phase: str, extra: Optional[Dict[str, Any]] = None):
        """Write a concise network/debug bundle to logs/network_debug.json (append)."""
        try:
            log_dir = Path(self.config['output_dir']) / 'logs'
            log_dir.mkdir(parents=True, exist_ok=True)
            p = log_dir / 'network_debug.json'
            payload = {
                'timestamp': datetime.now().isoformat(),
                'phase': phase,
                'url': url,
                'yt_dlp_opts': redact(self._base_ydl_opts()),
                'diagnostics_summary': {
                    'format_count': self.diagnostic_data.get('format_count'),
                    'hls_detected': self.diagnostic_data.get('hls_detected'),
                    'recommended_format': self.diagnostic_data.get('recommended_format'),
                    'issues_found': self.diagnostic_data.get('issues_found'),
                }
            }
            if extra:
                payload['extra'] = extra
            # Append as JSONL
            with p.open('a') as f:
                f.write(json.dumps(payload) + "\n")
        except Exception as e:
            self.debug_print(f"Could not write network debug: {str(e)}", 'warning')

    # ---------- CLI ----------

def main():
    parser = argparse.ArgumentParser(description='Download IBM videos using yt-dlp (robust)')
    parser.add_argument('url', nargs='?', default='https://video.ibm.com/recorded/134516112', help='Video URL to download')
    parser.add_argument('--output-dir', '-o', default='./downloads', help='Output directory for downloads')
    parser.add_argument('--quality', '-q', default='best', choices=['480p', '720p', '1080p', 'best'], help='Video quality preference')
    parser.add_argument('--format', '-f', default='mp4', choices=['mp4', 'webm', 'mkv'], help='Output container preference')
    parser.add_argument('--info-only', action='store_true', help='Only extract video information, do not download')
    parser.add_argument('--list-formats', action='store_true', help='List all available formats for the video')
    parser.add_argument('--diagnostics', action='store_true', help='Run comprehensive diagnostic tests')
    parser.add_argument('--fix-audio', action='store_true', help='Force video+audio combination for HLS streams')
    parser.add_argument('--debug-level', choices=['none', 'min', 'max'], default='max', help='Debug output level')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging (same as --debug-level max)')

    # New: network/extractor helpers
    parser.add_argument('--cookies', help='Path to Netscape cookies.txt file')
    parser.add_argument('--cookies-from-browser', dest='cookies_from_browser', help='Use cookies from a browser (e.g. chrome, firefox)')
    parser.add_argument('--referer', help='Override Referer header (defaults to https://video.ibm.com/)')
    parser.add_argument('--origin', help='Override Origin header (defaults to https://video.ibm.com)')
    parser.add_argument('--user-agent', help='Override User-Agent header')

    args = parser.parse_args()
    if args.verbose:
        args.debug_level = 'max'
    force_audio_combination = args.fix_audio

    # Build config
    headers = {
        'Referer': args.referer or 'https://video.ibm.com/',
        'Origin': args.origin or 'https://video.ibm.com',
        'User-Agent': args.user_agent or 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 '
                                         '(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

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
        'merge_output_format': args.format,
        'keep_video': True,
        'verbose': args.debug_level != 'none',
        'log_level': 'DEBUG' if args.debug_level == 'max' else 'INFO',
        # strengthened defaults:
        'extractor_retries': 5,
        'socket_timeout': 30,
        'geo_bypass_country': 'US',
        'hls_prefer_native': True,
        'hls_use_mpegts': True,
        # cookies / headers
        'cookies': args.cookies,
        'cookies_from_browser': args.cookies_from_browser,
        'http_headers': headers,
    }

    downloader = VideoDownloader(config, debug_level=args.debug_level)
    if force_audio_combination:
        downloader.force_audio_combination = True

    try:
        print(f"{'='*70}")
        print(f"🎬 IBM Video Downloader v2.1 (Debug: {args.debug_level.upper()})")
        print(f"{'='*70}")
        print(f"📋 URL: {args.url}")
        print(f"📁 Output Directory: {args.output_dir}")
        print(f"🎯 Quality: {args.quality}")
        print(f"📄 Container: {args.format}")
        print(f"🔊 Force Audio Combine: {'ON' if force_audio_combination else 'OFF'}")
        if args.cookies:
            print(f"🍪 Cookies file: {args.cookies}")
        if args.cookies_from_browser:
            print(f"🍪 Cookies from browser: {args.cookies_from_browser}")
        print(f"{'='*70}")

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
            if diagnostics.get('test_selectors'):
                print("\n🧪 Selector Checks (simulate):")
                for sel, res in diagnostics['test_selectors'].items():
                    status = "OK" if res['ok'] else f"FAIL: {res['error']}"
                    print(f"  - {sel}: {status}")
            if diagnostics.get('issues_found'):
                print(f"\n⚠️  ISSUES FOUND:")
                for issue in diagnostics['issues_found']:
                    print(f"  - {issue}")
            print("\n" + "="*50)
            return

        if args.list_formats:
            print("\n🔍 LISTING AVAILABLE FORMATS (with fallback):")
            print("="*50)
            downloader.list_available_formats(args.url)
            return

        # Info only
        try:
            info = downloader.get_video_info(args.url)
        except Exception as e:
            print(f"❌ Failed to extract video info: {str(e)}")
            print("🔧 Trying diagnostic fallback...")
            diagnostics = downloader.run_diagnostic_tests(args.url)
            if not diagnostics.get('url_accessible'):
                print("❌ URL not accessible. Check the URL or headers/cookies and retry.")
                sys.exit(1)
            info = {'title': 'Unknown', 'duration': 'Unknown', 'uploader': 'Unknown'}

        if args.info_only:
            print(f"\n📋 VIDEO INFORMATION:")
            print(f"Title: {info.get('title', 'N/A')}")
            print(f"Duration: {info.get('duration', 'N/A')} seconds")
            print(f"Uploader: {info.get('uploader', 'N/A')}")
            description = info.get('description', 'N/A')
            if description and isinstance(description, str) and len(description) > 200:
                description = description[:200] + "..."
            print(f"Description: {description}")
            return

        print(f"\n🚀 STARTING DOWNLOAD…")
        success = downloader.download_video(args.url)
        downloader.save_progress_report()

        if success:
            print(f"\n{'='*70}")
            print("✅ DOWNLOAD COMPLETED SUCCESSFULLY!")
            print(f"📁 Files saved to: {args.output_dir}")

            video_files = sorted(Path(args.output_dir).glob("*.mp4")) + \
                          sorted(Path(args.output_dir).glob("*.mkv")) + \
                          sorted(Path(args.output_dir).glob("*.webm"))
            if video_files:
                video_file = video_files[-1]
                file_size_gb = video_file.stat().st_size / (1024**3)
                print(f"🎥 Video: {video_file.name} ({file_size_gb:.2f} GB)")

                diags = downloader.diagnostic_data or {}
                if diags.get('hls_detected'):
                    if diags.get('video_only_count', 0) > 0 and diags.get('audio_only_count', 0) > 0:
                        print(f"🔊 Audio Status: Video+Audio combined automatically")
                    elif diags.get('video_only_count', 0) > 0 and diags.get('audio_only_count', 0) == 0:
                        print(f"⚠️  Audio Status: No audio detected (video-only HLS stream)")

                print(f"🎬 To play the video:")
                print(f"   macOS: open '{video_file}'")
                print(f"   Linux: vlc '{video_file}' or mpv '{video_file}'")
                print(f"   Windows: start \"{video_file}\"")
                print(f"   Universal: Use VLC or mpv")
                if diags.get('hls_detected'):
                    print(f"ℹ️  Note: HLS-derived files typically play best in VLC/mpv")
            print(f"{'='*70}")
        else:
            print(f"\n{'='*70}")
            print("❌ DOWNLOAD FAILED")
            print("🔧 Troubleshooting suggestions:")
            print("  1) Add headers: --referer https://video.ibm.com/  --origin https://video.ibm.com")
            print("  2) Try cookies: --cookies cookies.txt  or  --cookies-from-browser chrome")
            print("  3) Run: --diagnostics (to see selectors and HLS audio-groups)")
            print("  4) Use explicit selectors via --quality (e.g., 720p) or edit format logic")
            print("  5) Check logs/network_debug.json and downloads/logs/*.log")
            print(f"{'='*70}")
            sys.exit(1)

    except KeyboardInterrupt:
        print("\n🛑 Download interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {str(e)}")
        print("🔧 Try: --diagnostics and consider adding --cookies or --referer/--origin headers.")
        if args.debug_level == 'none':
            print("🔧 Or use --debug-level max for detailed info.")
        sys.exit(1)


if __name__ == "__main__":
    main()

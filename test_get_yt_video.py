#!/usr/bin/env python3
"""
Tests for get_yt-video-by-id.py
"""

import pytest
import sys
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module under test
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from importlib import import_module

# Import functions from the script (handling hyphen in filename)
import importlib.util
spec = importlib.util.spec_from_file_location("yt_video", "get_yt-video-by-id.py")
yt_video = importlib.util.module_from_spec(spec)
spec.loader.exec_module(yt_video)

get_format_selector = yt_video.get_format_selector
RESOLUTION_LIMITS = yt_video.RESOLUTION_LIMITS
download_video = yt_video.download_video


class TestResolutionLimits:
    """Test that RESOLUTION_LIMITS has correct values."""

    def test_all_quality_size_combinations_exist(self):
        """All 9 quality/size combinations should be defined."""
        qualities = ['low', 'medium', 'high']
        sizes = ['low', 'medium', 'high']

        for q in qualities:
            for s in sizes:
                assert (q, s) in RESOLUTION_LIMITS, f"Missing ({q}, {s})"

    def test_low_quality_low_size(self):
        assert RESOLUTION_LIMITS[('low', 'low')] == 360

    def test_low_quality_medium_size(self):
        assert RESOLUTION_LIMITS[('low', 'medium')] == 480

    def test_low_quality_high_size(self):
        assert RESOLUTION_LIMITS[('low', 'high')] == 720

    def test_medium_quality_low_size(self):
        assert RESOLUTION_LIMITS[('medium', 'low')] == 480

    def test_medium_quality_medium_size(self):
        assert RESOLUTION_LIMITS[('medium', 'medium')] == 720

    def test_medium_quality_high_size(self):
        assert RESOLUTION_LIMITS[('medium', 'high')] == 1080

    def test_high_quality_low_size(self):
        assert RESOLUTION_LIMITS[('high', 'low')] == 720

    def test_high_quality_medium_size(self):
        assert RESOLUTION_LIMITS[('high', 'medium')] == 1080

    def test_high_quality_high_size_is_best(self):
        """high/high should be None (best available)."""
        assert RESOLUTION_LIMITS[('high', 'high')] is None


class TestFormatSelector:
    """Test format selector string generation."""

    def test_low_low_format_selector(self):
        """Low/low should limit to 360p."""
        selector = get_format_selector('low', 'low')
        assert '360' in selector
        assert 'bestvideo' in selector
        assert 'bestaudio' in selector

    def test_medium_medium_format_selector(self):
        """Medium/medium should limit to 720p."""
        selector = get_format_selector('medium', 'medium')
        assert '720' in selector

    def test_high_high_format_selector(self):
        """High/high should not have height limit."""
        selector = get_format_selector('high', 'high')
        # Should not contain specific height limits
        assert 'height<=' not in selector
        # Should prefer mp4
        assert 'ext=mp4' in selector
        # Should have fallbacks
        assert 'best' in selector

    def test_format_selector_has_fallbacks(self):
        """All selectors should have multiple fallback options."""
        for (q, s) in RESOLUTION_LIMITS.keys():
            selector = get_format_selector(q, s)
            # Should have multiple fallback options separated by /
            assert selector.count('/') >= 1, f"({q}, {s}) should have fallbacks"

    def test_format_selector_prefers_mp4(self):
        """Format selectors should prefer mp4 format."""
        selector = get_format_selector('low', 'low')
        assert 'ext=mp4' in selector

    def test_format_selector_includes_audio(self):
        """Format selectors should include audio."""
        selector = get_format_selector('low', 'low')
        assert 'bestaudio' in selector or 'best' in selector


class TestDownloadVideoFunction:
    """Test download_video function (without actual downloading)."""

    def test_download_video_creates_output_dir(self):
        """download_video should create output directory if it doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = os.path.join(tmpdir, 'new_dir', 'nested')

            # Mock YoutubeDL to avoid actual download
            with patch.object(yt_video.yt_dlp, 'YoutubeDL') as mock_ydl:
                mock_instance = MagicMock()
                mock_ydl.return_value.__enter__ = MagicMock(return_value=mock_instance)
                mock_ydl.return_value.__exit__ = MagicMock(return_value=False)

                download_video(
                    video_id='test123',
                    output_dir=output_dir
                )

            # Directory should be created
            assert os.path.exists(output_dir)

    def test_download_video_builds_correct_url(self):
        """download_video should build correct YouTube URL from video ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(yt_video.yt_dlp, 'YoutubeDL') as mock_ydl:
                mock_instance = MagicMock()
                mock_ydl.return_value.__enter__ = MagicMock(return_value=mock_instance)
                mock_ydl.return_value.__exit__ = MagicMock(return_value=False)

                download_video(
                    video_id='abc123xyz',
                    output_dir=tmpdir
                )

                # Check that download was called with correct URL
                mock_instance.download.assert_called_once()
                args = mock_instance.download.call_args[0][0]
                assert 'https://www.youtube.com/watch?v=abc123xyz' in args

    def test_download_video_uses_correct_format_selector(self):
        """download_video should use format selector based on quality/size."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(yt_video.yt_dlp, 'YoutubeDL') as mock_ydl:
                mock_instance = MagicMock()
                mock_ydl.return_value.__enter__ = MagicMock(return_value=mock_instance)
                mock_ydl.return_value.__exit__ = MagicMock(return_value=False)

                download_video(
                    video_id='test',
                    quality='medium',
                    size='high',
                    output_dir=tmpdir
                )

                # Check the format option passed to YoutubeDL
                call_args = mock_ydl.call_args[0][0]
                assert '1080' in call_args['format']

    def test_download_video_returns_true_on_success(self):
        """download_video should return True on successful download."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(yt_video.yt_dlp, 'YoutubeDL') as mock_ydl:
                mock_instance = MagicMock()
                mock_ydl.return_value.__enter__ = MagicMock(return_value=mock_instance)
                mock_ydl.return_value.__exit__ = MagicMock(return_value=False)

                result = download_video(
                    video_id='test',
                    output_dir=tmpdir
                )

                assert result is True

    def test_download_video_returns_false_on_error(self):
        """download_video should return False on download error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(yt_video.yt_dlp, 'YoutubeDL') as mock_ydl:
                mock_instance = MagicMock()
                mock_instance.download.side_effect = yt_video.yt_dlp.utils.DownloadError('Test error')
                mock_ydl.return_value.__enter__ = MagicMock(return_value=mock_instance)
                mock_ydl.return_value.__exit__ = MagicMock(return_value=False)

                result = download_video(
                    video_id='test',
                    output_dir=tmpdir
                )

                assert result is False

    def test_download_video_sets_subtitle_language(self):
        """download_video should set subtitle language in options."""
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(yt_video.yt_dlp, 'YoutubeDL') as mock_ydl:
                mock_instance = MagicMock()
                mock_ydl.return_value.__enter__ = MagicMock(return_value=mock_instance)
                mock_ydl.return_value.__exit__ = MagicMock(return_value=False)

                download_video(
                    video_id='test',
                    language='es',
                    output_dir=tmpdir
                )

                call_args = mock_ydl.call_args[0][0]
                assert 'es' in call_args['subtitleslangs']


class TestIntegration:
    """Integration tests (require network, run with --run-integration)."""

    @pytest.mark.integration
    def test_real_download_short_video(self):
        """Test downloading a real short video."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Use a very short public domain video
            result = download_video(
                video_id='L7gv9aGB7VY',  # Default test video
                quality='low',
                size='low',
                output_dir=tmpdir
            )

            assert result is True

            # Check that files were created
            files = list(Path(tmpdir).glob('*'))
            assert len(files) > 0

            # Should have at least a video file
            video_files = list(Path(tmpdir).glob('*.mp4'))
            assert len(video_files) >= 1


if __name__ == '__main__':
    pytest.main([__file__, '-v'])

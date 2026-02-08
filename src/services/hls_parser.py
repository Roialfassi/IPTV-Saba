"""
HLS Parser - Parse HLS master playlists to extract quality variants.

This module handles parsing of HLS (HTTP Live Streaming) master playlists
to extract available quality variants (resolutions, bitrates).
"""
import re
import logging
from dataclasses import dataclass
from typing import List, Optional
from urllib.parse import urljoin
import requests

logger = logging.getLogger(__name__)


@dataclass
class QualityVariant:
    """
    Represents a single quality variant from an HLS master playlist.

    Attributes:
        resolution: Video resolution (e.g., "1920x1080")
        bandwidth: Stream bandwidth in bits per second
        url: URL to the variant playlist
        name: Human-readable name (e.g., "1080p", "720p HD")
        codecs: Optional codec information
    """
    resolution: str
    bandwidth: int
    url: str
    name: str
    codecs: str = ""

    @property
    def height(self) -> int:
        """Extract height from resolution string."""
        if "x" in self.resolution:
            try:
                return int(self.resolution.split("x")[1])
            except (ValueError, IndexError):
                return 0
        return 0

    @property
    def display_name(self) -> str:
        """Get a user-friendly display name."""
        return self.name or self.resolution or f"{self.bandwidth // 1000}kbps"


class HLSParser:
    """
    Parser for HLS (HTTP Live Streaming) master playlists.

    Extracts quality variants from #EXT-X-STREAM-INF tags.
    """

    # Regex patterns for parsing
    STREAM_INF_PATTERN = re.compile(
        r'#EXT-X-STREAM-INF:(.+?)[\r\n]+(.+?)[\r\n]',
        re.MULTILINE
    )
    BANDWIDTH_PATTERN = re.compile(r'BANDWIDTH=(\d+)')
    RESOLUTION_PATTERN = re.compile(r'RESOLUTION=(\d+x\d+)')
    CODECS_PATTERN = re.compile(r'CODECS="([^"]+)"')
    NAME_PATTERN = re.compile(r'NAME="([^"]+)"')

    @staticmethod
    def is_hls_url(url: str) -> bool:
        """
        Check if a URL points to an HLS playlist.

        Args:
            url: The URL to check.

        Returns:
            True if the URL appears to be an HLS playlist.
        """
        if not url:
            return False
        url_lower = url.lower()
        return url_lower.endswith('.m3u8') or '.m3u8?' in url_lower

    def parse_master_playlist(self, url: str, timeout: int = 10) -> List[QualityVariant]:
        """
        Parse an HLS master playlist and extract quality variants.

        Args:
            url: URL to the master playlist.
            timeout: Request timeout in seconds.

        Returns:
            List of QualityVariant objects, sorted by bandwidth (highest first).
        """
        variants = []

        try:
            # Fetch the playlist
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            content = response.text

            # Check if this is a master playlist (contains #EXT-X-STREAM-INF)
            if '#EXT-X-STREAM-INF' not in content:
                logger.debug(f"Not a master playlist (no variants): {url}")
                return variants

            # Parse each variant
            matches = self.STREAM_INF_PATTERN.findall(content)
            for attrs, variant_url in matches:
                variant = self._parse_variant(attrs, variant_url, url)
                if variant:
                    variants.append(variant)

            # Sort by bandwidth (highest first)
            variants.sort(key=lambda v: v.bandwidth, reverse=True)

            logger.info(f"Parsed {len(variants)} quality variants from {url}")

        except requests.RequestException as e:
            logger.error(f"Failed to fetch HLS playlist: {e}")
        except Exception as e:
            logger.error(f"Error parsing HLS playlist: {e}")

        return variants

    def _parse_variant(self, attrs: str, variant_url: str, base_url: str) -> Optional[QualityVariant]:
        """
        Parse a single variant from its attributes line.

        Args:
            attrs: The attribute string from #EXT-X-STREAM-INF
            variant_url: The URL line following the attributes
            base_url: Base URL for resolving relative URLs

        Returns:
            QualityVariant object or None if parsing fails.
        """
        try:
            # Extract bandwidth (required)
            bandwidth_match = self.BANDWIDTH_PATTERN.search(attrs)
            if not bandwidth_match:
                return None
            bandwidth = int(bandwidth_match.group(1))

            # Extract resolution (optional)
            resolution = ""
            resolution_match = self.RESOLUTION_PATTERN.search(attrs)
            if resolution_match:
                resolution = resolution_match.group(1)

            # Extract codecs (optional)
            codecs = ""
            codecs_match = self.CODECS_PATTERN.search(attrs)
            if codecs_match:
                codecs = codecs_match.group(1)

            # Extract name (optional)
            name = ""
            name_match = self.NAME_PATTERN.search(attrs)
            if name_match:
                name = name_match.group(1)

            # Generate name if not provided
            if not name:
                name = self._generate_quality_name(resolution, bandwidth)

            # Resolve relative URL
            full_url = urljoin(base_url, variant_url.strip())

            return QualityVariant(
                resolution=resolution,
                bandwidth=bandwidth,
                url=full_url,
                name=name,
                codecs=codecs
            )

        except Exception as e:
            logger.warning(f"Failed to parse variant: {e}")
            return None

    def _generate_quality_name(self, resolution: str, bandwidth: int) -> str:
        """
        Generate a human-readable quality name.

        Args:
            resolution: Resolution string (e.g., "1920x1080")
            bandwidth: Bandwidth in bps

        Returns:
            Human-readable name like "1080p HD" or "720p"
        """
        if resolution:
            try:
                height = int(resolution.split("x")[1])
                if height >= 2160:
                    return "4K UHD"
                elif height >= 1440:
                    return "1440p QHD"
                elif height >= 1080:
                    return "1080p HD"
                elif height >= 720:
                    return "720p HD"
                elif height >= 480:
                    return "480p SD"
                elif height >= 360:
                    return "360p"
                else:
                    return f"{height}p"
            except (ValueError, IndexError):
                pass

        # Fall back to bandwidth
        kbps = bandwidth // 1000
        if kbps >= 5000:
            return f"High ({kbps}kbps)"
        elif kbps >= 2000:
            return f"Medium ({kbps}kbps)"
        else:
            return f"Low ({kbps}kbps)"


# Singleton instance
_hls_parser: Optional[HLSParser] = None


def get_hls_parser() -> HLSParser:
    """Get the HLS parser singleton instance."""
    global _hls_parser
    if _hls_parser is None:
        _hls_parser = HLSParser()
    return _hls_parser

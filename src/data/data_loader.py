import json
import sys
import hashlib
from enum import Enum
from src.model.group_model import Group
from src.model.channel_model import Channel
import requests
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Union, Pattern, Callable, Any
import re
from urllib.parse import urlparse
import os
import logging
import io
import codecs
import chardet
from collections import defaultdict
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot, QThread
import time

from src.utils.url_utils import redact_url

# Logging is configured centrally in iptv_app.py; just get a module logger.
logger = logging.getLogger(__name__)


class StreamType(Enum):
    """Enumeration of stream types."""
    LIVE = "live"
    VOD = "vod"
    SERIES = "series"
    UNKNOWN = "unknown"


class LoadResult(Enum):
    """Outcome of a cache-aware load (see DataLoader.load_smart)."""
    LOADED = "loaded"                # validated against the source (HTTP 200 or 304)
    CACHE_FRESH = "cache_fresh"      # served from cache within TTL, no network used
    CACHE_OFFLINE = "cache_offline"  # network unavailable, served the cached copy
    FAILED = "failed"                # no data could be loaded


class DataLoader:
    """
    Parser for M3U playlists that organizes channels into groups.
    Supports loading from URLs, local files, or string content.
    
    Features:
    - Streaming download with parallel parsing
    - Retry logic with exponential backoff
    - Progress reporting via callbacks
    - Stream type detection
    - Memory-optimized string interning for group names
    - Fast channel lookup with name index
    """

    # ==================== Class-Level Constants ====================
    
    # Pre-compiled regex patterns for better performance (reused across all parsing)
    ATTR_PATTERN = re.compile(r'([\w-]+)="([^"]*)"')
    ALT_ATTR_PATTERN = re.compile(r'([\w-]+)=([^ "]+)')
    NAME_PATTERN = re.compile(r'#EXTINF:.*?,(.*)$')
    
    # Stream type detection patterns
    VOD_EXTENSIONS = frozenset(['.mp4', '.mkv', '.avi', '.mov', '.wmv', '.flv', '.webm', '.m4v'])
    SERIES_PATTERNS = re.compile(r'[sS]\d{1,2}[eE]\d{1,2}|season\s*\d+|episode\s*\d+', re.IGNORECASE)
    
    # Default HTTP headers to avoid being blocked
    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    
    # Retry configuration
    MAX_RETRIES = 3
    INITIAL_RETRY_DELAY = 1.0  # seconds
    MAX_RETRY_DELAY = 30.0  # seconds
    BACKOFF_MULTIPLIER = 2.0

    # Special aggregate group names
    SPECIAL_GROUP_ALL = "All Channels"
    SPECIAL_GROUP_LIVE = "All Livestreams"
    SPECIAL_GROUP_VOD = "All VODs"
    SPECIAL_GROUP_NAMES = frozenset([SPECIAL_GROUP_ALL, SPECIAL_GROUP_LIVE, SPECIAL_GROUP_VOD])

    # Cache configuration
    CACHE_METADATA_FILE = "cache_metadata.json"

    # ==================== Exception Classes ====================
    
    class ParseError(Exception):
        """Exception raised for parsing errors."""
        def __init__(self, message: str, line_number: int = None, line_content: str = None):
            self.line_number = line_number
            self.line_content = line_content
            detailed_msg = message
            if line_number is not None:
                detailed_msg += f" (line {line_number})"
            if line_content is not None:
                detailed_msg += f": '{line_content[:50]}...'" if len(line_content) > 50 else f": '{line_content}'"
            super().__init__(detailed_msg)

    class SourceError(Exception):
        """Exception raised for source retrieval errors."""
        def __init__(self, message: str, source: str = None, status_code: int = None):
            self.source = source
            self.status_code = status_code
            detailed_msg = message
            if status_code is not None:
                detailed_msg += f" (HTTP {status_code})"
            if source is not None:
                # Redact credentials before they reach the message/logs.
                detailed_msg += f" [Source: {redact_url(source)}]"
            super().__init__(detailed_msg)

    class NetworkError(Exception):
        """Exception raised for network-related errors."""
        def __init__(self, message: str, url: str = None, retry_count: int = None):
            self.url = url
            self.retry_count = retry_count
            detailed_msg = message
            if retry_count is not None:
                detailed_msg += f" (after {retry_count} retries)"
            super().__init__(detailed_msg)

    # ==================== Initialization ====================
    
    def __init__(self, default_group_name: str = "Ungrouped", cache_dir: str = None):
        """
        Initialize the M3U parser.

        Args:
            default_group_name: Name for channels without a specified group
            cache_dir: Optional directory for HTTP 304 caching (ETag/Last-Modified)
        """
        self._groups: Dict[str, Group] = {}
        self._channels: List[Channel] = []
        self._channel_index: Dict[str, Channel] = {}  # Fast lookup by lowercase name
        self.default_group_name = default_group_name
        
        # String interning cache for memory optimization
        self._interned_strings: Dict[str, str] = {}
        
        # Progress tracking
        self._progress_callback: Optional[Callable[[int, int, str], None]] = None

        # HTTP 304 cache directory
        self._cache_dir: Optional[str] = cache_dir
        if cache_dir:
            os.makedirs(cache_dir, exist_ok=True)

        # Reuse one Session across the conditional GET + streaming download so
        # the TCP/TLS connection (and keep-alive) is pooled instead of being
        # re-established on every request. Default headers live on the session;
        # per-request conditional headers (If-None-Match/If-Modified-Since) are
        # merged on top and take precedence.
        self._session = requests.Session()
        self._session.headers.update(self.DEFAULT_HEADERS)

    def close(self) -> None:
        """Release the pooled HTTP connections held by the session."""
        try:
            self._session.close()
        except Exception as e:
            logger.debug(f"Error closing HTTP session: {e}")

    # ==================== Properties ====================
    
    @property
    def groups(self) -> Dict[str, Group]:
        """Get all channel groups as a dictionary keyed by group name."""
        return self._groups

    @property
    def channels(self) -> List[Channel]:
        """Get all channels across all groups."""
        return self._channels

    # ==================== String Interning ====================
    
    def _intern_string(self, s: str) -> str:
        """
        Intern a string to reduce memory usage for repeated values.
        This is particularly effective for group names that repeat across many channels.
        
        Args:
            s: String to intern
            
        Returns:
            Interned string (same content, shared memory)
        """
        if s not in self._interned_strings:
            self._interned_strings[s] = s
        return self._interned_strings[s]

    # ==================== Stream Type Detection ====================
    
    @classmethod
    def detect_stream_type(cls, url: str, name: str = "", metadata: Dict[str, str] = None) -> StreamType:
        """
        Detect the type of stream based on URL, name, and metadata.
        
        Args:
            url: The stream URL
            name: The channel/content name
            metadata: Optional metadata dictionary from M3U
            
        Returns:
            StreamType enum value
        """
        if not url:
            return StreamType.UNKNOWN
            
        url_lower = url.lower()
        
        # Check for VOD extensions
        parsed = urlparse(url_lower)
        path = parsed.path
        if any(path.endswith(ext) for ext in cls.VOD_EXTENSIONS):
            # Check if it's part of a series
            if cls.SERIES_PATTERNS.search(name) or cls.SERIES_PATTERNS.search(path):
                return StreamType.SERIES
            return StreamType.VOD
        
        # Check metadata for type hints
        if metadata:
            # Common M3U attributes that indicate content type
            content_type = metadata.get('type', '').lower()
            if content_type in ('movie', 'vod'):
                return StreamType.VOD
            elif content_type in ('series', 'show'):
                return StreamType.SERIES
            elif content_type in ('live', 'channel'):
                return StreamType.LIVE
                
            # Check group-title for hints
            group = metadata.get('group-title', '').lower()
            if any(kw in group for kw in ['movie', 'vod', 'film']):
                return StreamType.VOD
            elif any(kw in group for kw in ['series', 'show', 'episode']):
                return StreamType.SERIES
        
        # Check for series patterns in name
        if cls.SERIES_PATTERNS.search(name):
            return StreamType.SERIES
        
        # Check URL patterns
        if any(kw in url_lower for kw in ['/movie/', '/vod/', '/film/']):
            return StreamType.VOD
        elif any(kw in url_lower for kw in ['/series/', '/show/', '/episode/']):
            return StreamType.SERIES
        elif any(kw in url_lower for kw in ['/live/', 'live.m3u8', '.ts']):
            return StreamType.LIVE
        
        # Default to LIVE for streaming formats
        if any(url_lower.endswith(ext) for ext in ['.m3u8', '.ts', '.mpd']):
            return StreamType.LIVE
            
        return StreamType.UNKNOWN

    # ==================== HTTP Request with Retry ====================
    
    def _request_with_retry(
        self, 
        url: str, 
        stream: bool = False, 
        timeout: int = 30,
        extra_headers: Dict[str, str] = None,
        allow_304: bool = False
    ) -> requests.Response:
        """
        Make an HTTP GET request with exponential backoff retry logic.
        
        Args:
            url: URL to request
            stream: Whether to stream the response
            timeout: Request timeout in seconds
            extra_headers: Additional headers (e.g. If-None-Match, If-Modified-Since)
            allow_304: If True, return 304 responses instead of raising
            
        Returns:
            requests.Response object
            
        Raises:
            NetworkError: If all retries fail
        """
        last_exception = None
        delay = self.INITIAL_RETRY_DELAY
        # Honored from a 429 Retry-After header; overrides backoff for one wait.
        retry_after: Optional[float] = None

        for attempt in range(self.MAX_RETRIES):
            try:
                # Default headers come from the pooled session; pass only the
                # per-request conditional headers (they override the session's).
                response = self._session.get(
                    url,
                    headers=extra_headers or None,
                    stream=stream,
                    timeout=timeout
                )

                # Allow 304 Not Modified to pass through without raising
                if allow_304 and response.status_code == 304:
                    logger.info(f"Server returned 304 Not Modified for {redact_url(url)}")
                    return response

                response.raise_for_status()
                return response

            except requests.exceptions.Timeout as e:
                last_exception = e
                logger.warning(f"Request timeout (attempt {attempt + 1}/{self.MAX_RETRIES}): {redact_url(url)}")

            except requests.exceptions.ConnectionError as e:
                last_exception = e
                logger.warning(f"Connection error (attempt {attempt + 1}/{self.MAX_RETRIES}): {redact_url(url)}")

            except requests.exceptions.HTTPError as e:
                # Don't retry on client errors (4xx) except 429 (rate limit)
                if e.response is not None and 400 <= e.response.status_code < 500:
                    if e.response.status_code == 429:
                        # Rate limited - prefer the server's Retry-After hint,
                        # falling back to exponential backoff if it is absent.
                        retry_after = self._parse_retry_after(
                            e.response.headers.get('Retry-After')
                        )
                        if retry_after is not None:
                            logger.warning(
                                f"Rate limited (attempt {attempt + 1}/{self.MAX_RETRIES}); "
                                f"honoring Retry-After={retry_after:.1f}s"
                            )
                        else:
                            logger.warning(
                                f"Rate limited (attempt {attempt + 1}/{self.MAX_RETRIES}); backing off"
                            )
                    else:
                        raise self.SourceError(
                            f"HTTP client error",
                            source=url,
                            status_code=e.response.status_code
                        )
                last_exception = e
                logger.warning(f"HTTP error (attempt {attempt + 1}/{self.MAX_RETRIES}): {e}")

            except requests.exceptions.RequestException as e:
                last_exception = e
                logger.warning(f"Request error (attempt {attempt + 1}/{self.MAX_RETRIES}): {e}")

            # Wait before retry. A 429 Retry-After (this round only) wins over
            # the exponential backoff schedule.
            if attempt < self.MAX_RETRIES - 1:
                wait = retry_after if retry_after is not None else delay
                wait = min(wait, self.MAX_RETRY_DELAY)
                logger.info(f"Retrying in {wait:.1f} seconds...")
                time.sleep(wait)
                retry_after = None  # consume the hint; backoff resumes next round
                delay = min(delay * self.BACKOFF_MULTIPLIER, self.MAX_RETRY_DELAY)
        
        # All retries exhausted
        raise self.NetworkError(
            f"Failed to fetch URL after {self.MAX_RETRIES} attempts: {last_exception}",
            url=url,
            retry_count=self.MAX_RETRIES
        )

    @staticmethod
    def _parse_retry_after(value: Optional[str]) -> Optional[float]:
        """
        Parse an HTTP ``Retry-After`` header into a delay in seconds.

        The header is either a number of seconds ("120") or an HTTP date
        ("Wed, 21 Oct 2025 07:28:00 GMT"). Returns the non-negative delay in
        seconds, or None if the value is missing or unparseable (so the caller
        falls back to its own backoff).
        """
        if not value:
            return None
        value = value.strip()
        # Form 1: delta-seconds.
        try:
            return max(0.0, float(value))
        except ValueError:
            pass
        # Form 2: HTTP-date.
        try:
            retry_dt = parsedate_to_datetime(value)
            if retry_dt is None:
                return None
            if retry_dt.tzinfo is None:
                retry_dt = retry_dt.replace(tzinfo=timezone.utc)
            return max(0.0, (retry_dt - datetime.now(timezone.utc)).total_seconds())
        except (TypeError, ValueError):
            return None

    # ==================== Progress Reporting ====================
    
    def _report_progress(self, current: int, total: int, message: str = ""):
        """
        Report progress to the registered callback.
        
        Args:
            current: Current progress value
            total: Total expected value (0 if unknown)
            message: Optional status message
        """
        if self._progress_callback:
            try:
                self._progress_callback(current, total, message)
            except Exception as e:
                logger.warning(f"Progress callback error: {e}")

    # ==================== HTTP 304 Cache Methods ====================
    
    def _get_url_hash(self, url: str) -> str:
        """Generate a stable hash key from a URL for cache file naming."""
        return hashlib.md5(url.encode('utf-8')).hexdigest()

    def _get_cache_file_path(self, url: str) -> str:
        """Get the JSON cache file path for a given URL."""
        return os.path.join(self._cache_dir, f"{self._get_url_hash(url)}.json")

    def _get_cache_metadata_path(self) -> str:
        """Get the path to the cache metadata JSON file."""
        return os.path.join(self._cache_dir, self.CACHE_METADATA_FILE)

    def _load_cache_metadata(self) -> Dict:
        """Load the cache metadata file (ETag / Last-Modified per URL)."""
        path = self._get_cache_metadata_path()
        if os.path.isfile(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to read cache metadata: {e}")
        return {}

    def _get_conditional_headers(self, url: str) -> Dict[str, str]:
        """
        Build If-None-Match / If-Modified-Since headers from cached metadata.
        Returns an empty dict if no cached headers exist for this URL.
        """
        metadata = self._load_cache_metadata()
        entry = metadata.get(self._get_url_hash(url), {})
        headers = {}
        if entry.get('etag'):
            headers['If-None-Match'] = entry['etag']
        if entry.get('last_modified'):
            headers['If-Modified-Since'] = entry['last_modified']
        return headers

    def _save_to_cache(self, url: str, response: requests.Response) -> None:
        """
        Save the parsed data as JSON and store ETag/Last-Modified from the response.
        Called after a successful 200 download so future requests can use 304.
        """
        try:
            # Save parsed channel data as JSON
            cache_path = self._get_cache_file_path(url)
            self.save_to_json(cache_path)

            # Save response headers for conditional requests
            metadata = self._load_cache_metadata()
            metadata[self._get_url_hash(url)] = {
                'url': url,
                'etag': response.headers.get('ETag', ''),
                'last_modified': response.headers.get('Last-Modified', ''),
                'cached_at': time.time()
            }
            with open(self._get_cache_metadata_path(), 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)

            logger.info(f"Saved cache for URL (ETag={response.headers.get('ETag', 'none')})")
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")

    def _cache_file_exists(self, url: str) -> bool:
        """True if a parsed cache file exists on disk for this URL."""
        return bool(self._cache_dir) and os.path.isfile(self._get_cache_file_path(url))

    def get_cache_age(self, url: str) -> Optional[float]:
        """
        Age of the cached copy for a URL, in seconds, or None if there is no
        cache (or no recorded timestamp). Based on the URL-keyed metadata.
        """
        if not self._cache_dir:
            return None
        entry = self._load_cache_metadata().get(self._get_url_hash(url), {})
        cached_at = entry.get('cached_at')
        if not isinstance(cached_at, (int, float)):
            return None
        return max(0.0, time.time() - cached_at)

    # ==================== Main Loading Methods ====================

    def _load_cache_with_progress(
        self,
        cache_path: str,
        progress_callback: Callable[[int, int, str], None],
        message: str
    ) -> bool:
        """Load a parsed cache file, emitting a couple of progress messages."""
        self._progress_callback = progress_callback
        try:
            self._report_progress(0, 0, message)
            ok = self.load_from_json(cache_path)
            if ok:
                self._report_progress(
                    100, 100,
                    f"Loaded {len(self._channels)} channels in {len(self._groups)} groups from cache"
                )
            return ok
        finally:
            self._progress_callback = None

    def load_smart(
        self,
        url: str,
        progress_callback: Callable[[int, int, str], None] = None,
        ttl_seconds: Optional[float] = None
    ) -> 'LoadResult':
        """
        Unified, URL-keyed, cache-aware load. This is the single entry point
        callers should use for a profile playlist.

        Policy:
          1. Offline fast-path: if ``ttl_seconds`` is given and a cached copy
             exists that is younger than ``ttl_seconds``, load it WITHOUT any
             network request. Default ``ttl_seconds=None`` always validates so
             playlist changes are picked up promptly.
          2. Primary path: a conditional GET (If-None-Match / If-Modified-Since).
             The server returns 304 when the playlist is unchanged (cheap, no
             body) and the cache is reused; a 200 streams and re-parses. Either
             way the result is ``LOADED``.
          3. If the network is unreachable, fall back to the cached copy
             (``CACHE_OFFLINE``) when one exists, otherwise ``FAILED``.

        The cache is keyed by URL, so editing a profile's URL transparently
        switches to a different cache entry (no stale data from the old URL).

        Args:
            url: Playlist URL (http/https), local file path, or M3U content.
            progress_callback: Optional callback(current, total, message).
            ttl_seconds: Optional offline fast-path window; None = always validate.

        Returns:
            LoadResult describing how the data was obtained.
        """
        parsed = urlparse(url)
        is_remote = parsed.scheme in ('http', 'https')

        # Local files / inline content have no cache layer — parse directly.
        if not is_remote:
            ok = self.load(url, progress_callback=progress_callback)
            return LoadResult.LOADED if ok else LoadResult.FAILED

        cache_path = self._get_cache_file_path(url) if self._cache_dir else None
        have_cache = bool(cache_path) and os.path.isfile(cache_path)

        # 1. Offline fast-path within TTL — skip the network entirely.
        if ttl_seconds is not None and have_cache:
            age = self.get_cache_age(url)
            if age is not None and age < ttl_seconds:
                if self._load_cache_with_progress(cache_path, progress_callback, "Loading from cache..."):
                    logger.info(f"Cache fresh (age {age / 3600:.1f}h < TTL); skipped network")
                    return LoadResult.CACHE_FRESH
                logger.warning("Fresh cache unreadable; validating against network instead")

        # 2. Primary path: conditional GET (handles 304 + cache save internally).
        try:
            if self.load(url, progress_callback=progress_callback):
                return LoadResult.LOADED
            logger.warning("Network load returned no data; attempting cache fallback")
        except Exception as e:
            logger.warning(f"Network load failed: {type(e).__name__}: {e}; attempting cache fallback")

        # 3. Offline fallback — serve the cached copy if we have one.
        if have_cache and self._load_cache_with_progress(
            cache_path, progress_callback, "Network unavailable, loading cached copy..."
        ):
            logger.info("Served cached copy after network failure")
            return LoadResult.CACHE_OFFLINE

        return LoadResult.FAILED

    def load(
        self,
        source: str,
        use_optimized: bool = True,
        progress_callback: Callable[[int, int, str], None] = None
    ) -> bool:
        """
        Load and parse M3U data from various sources.

        Args:
            source: URL, file path, or M3U content string
            use_optimized: Use optimized streaming parser (default True)
            progress_callback: Optional callback function(current, total, message)
                              for progress reporting

        Returns:
            True if parsing was successful, False otherwise
        """
        self._progress_callback = progress_callback
        
        try:
            self._report_progress(0, 0, "Starting load...")
            
            # Use optimized streaming parser for URLs
            parsed_url = urlparse(source)
            if use_optimized and parsed_url.scheme in ('http', 'https'):
                logger.info("Using optimized streaming parser for faster loading")
                result = self._load_and_parse_streaming(source)
            else:
                # Fall back to traditional method for files and direct content
                self._report_progress(0, 0, "Fetching content...")
                content = self._get_content(source)
                if not content:
                    return False
                result = self._parse(content)
            
            # Create special aggregate groups after any successful load
            if result:
                self._create_special_groups()
            
            return result
            
        except self.ParseError as e:
            logger.error(f"Parse error: {e}")
            return False
        except self.SourceError as e:
            logger.error(f"Source error: {e}")
            return False
        except self.NetworkError as e:
            logger.error(f"Network error: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error loading source: {type(e).__name__}: {e}")
            return False
        finally:
            self._progress_callback = None

    def _get_content(self, source: str) -> Optional[str]:
        """
        Extract M3U content from URL, file path, or string.

        Args:
            source: URL, file path, or M3U content string

        Returns:
            M3U content as string or None if retrieval failed

        Raises:
            SourceError: If source cannot be retrieved
        """
        # Check if source is a URL
        parsed_url = urlparse(source)
        if parsed_url.scheme in ('http', 'https'):
            try:
                response = self._request_with_retry(source, stream=False)

                # Detect encoding
                encoding = response.encoding
                if not encoding or encoding.lower() == 'iso-8859-1':
                    detected = chardet.detect(response.content)
                    encoding = detected['encoding'] if detected['confidence'] > 0.7 else 'utf-8'

                return response.content.decode(encoding, errors='replace')
            except self.NetworkError:
                raise
            except Exception as e:
                raise self.SourceError(
                    f"Failed to fetch M3U content: {type(e).__name__}: {e}",
                    source=source
                )

        # Check if source is a local file
        if os.path.isfile(source):
            try:
                self._report_progress(0, 0, f"Reading file: {os.path.basename(source)}")
                with open(source, 'rb') as f:
                    content = f.read()

                # Detect encoding
                detected = chardet.detect(content)
                encoding = detected['encoding'] if detected['confidence'] > 0.7 else 'utf-8'

                return content.decode(encoding, errors='replace')
            except IOError as e:
                raise self.SourceError(
                    f"Failed to read file: {e}",
                    source=source
                )
            except UnicodeDecodeError as e:
                raise self.SourceError(
                    f"Encoding error reading file: {e}",
                    source=source
                )

        # Treat source as direct content if it starts with M3U header
        if "#EXTM3U" in source[:50]:
            return source

        raise self.SourceError(
            "Invalid source: not a URL, file path, or M3U content",
            source=source[:100] if len(source) > 100 else source
        )

    # ==================== M3U Parsing ====================
    
    def _parse(self, content: str) -> bool:
        """
        Parse M3U content and organize channels into groups.

        Args:
            content: M3U content as string

        Returns:
            True if parsing was successful, False otherwise

        Raises:
            ParseError: If content cannot be parsed
        """
        # Clear existing data
        self._groups = {}
        self._channels = []
        self._channel_index = {}

        # Cache for group instances to avoid dictionary lookups
        group_cache = {}

        # Optimize line splitting for large files. Strip a leading BOM if
        # present — str.strip() does NOT remove U+FEFF, so the header check
        # below would otherwise reject BOM-prefixed playlists.
        content = content.lstrip('﻿').replace('\r\n', '\n').replace('\r', '\n')
        lines = content.split('\n')
        total_lines = len(lines)

        # Check for valid M3U header
        if not lines or not lines[0].strip().startswith("#EXTM3U"):
            raise self.ParseError(
                "Invalid M3U format: missing #EXTM3U header",
                line_number=1,
                line_content=lines[0] if lines else ""
            )

        self._report_progress(0, total_lines, "Parsing M3U content...")
        
        i = 1
        channels_parsed = 0
        last_progress_report = 0
        
        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines
            if not line:
                i += 1
                continue

            try:
                # Process info line
                if line.startswith("#EXTINF:"):
                    metadata = self._parse_extinf(line)

                    # Look for the stream URL in subsequent lines
                    i += 1
                    while i < len(lines) and (not lines[i].strip() or lines[i].strip().startswith('#')):
                        # Skip empty lines and tags we don't need to process
                        i += 1

                    if i < len(lines) and lines[i].strip() and not lines[i].strip().startswith('#'):
                        stream_url = lines[i].strip()
                        self._add_channel_from_metadata(metadata, stream_url, group_cache)
                        channels_parsed += 1

                        # Report progress every 100 channels
                        if channels_parsed - last_progress_report >= 100:
                            self._report_progress(i, total_lines, f"Parsed {channels_parsed} channels...")
                            last_progress_report = channels_parsed
                            
            except Exception as e:
                # Log the error but continue parsing
                logger.warning(f"Error parsing line {i}: {type(e).__name__}: {e}")

            i += 1

        self._report_progress(total_lines, total_lines, f"Completed: {len(self._channels)} channels in {len(self._groups)} groups")
        return len(self._channels) > 0

    def _parse_extinf(self, line: str) -> Dict[str, str]:
        """
        Parse the EXTINF line to extract metadata.

        Args:
            line: EXTINF line from M3U file

        Returns:
            Dictionary of metadata attributes
        """
        metadata = {}

        # Extract the channel name (after the comma)
        name_match = self.NAME_PATTERN.search(line)
        if name_match:
            metadata['name'] = name_match.group(1).strip()

        # Extract attributes within quotes
        for match in self.ATTR_PATTERN.finditer(line):
            key, value = match.groups()
            metadata[key] = value.strip()

        # Handle alternative attribute formats (without quotes)
        for match in self.ALT_ATTR_PATTERN.finditer(line):
            key, value = match.groups()
            if key not in metadata:  # Don't override quoted values
                metadata[key] = value.strip()

        return metadata

    def _add_channel_from_metadata(
        self,
        metadata: Dict[str, str],
        stream_url: str,
        group_cache: Dict[str, Group],
    ) -> None:
        """
        Build a Channel from parsed EXTINF metadata + its stream URL and
        register it in the groups dict, the flat channel list and the
        lowercase-name index. Shared by the file and streaming parsers so the
        two paths stay in sync.

        ``group_cache`` is a caller-owned dict that memoizes Group lookups for
        the duration of a single parse. This is single-threaded by design, so
        channels keep their original playlist order and no locking is needed.
        """
        stream_type = self.detect_stream_type(
            stream_url, metadata.get('name', ''), metadata
        )
        channel = Channel(
            name=metadata.get('name', f"Channel_{len(self._channels) + 1}"),
            stream_url=stream_url,
            tvg_id=metadata.get('tvg-id', ''),
            tvg_logo=metadata.get('tvg-logo', ''),
            channel_type=stream_type.value,
        )

        # Intern the group name (it repeats across many channels) and
        # resolve/create the Group, memoizing the lookup via group_cache.
        group_name = self._intern_string(
            metadata.get('group-title', self.default_group_name)
        )
        group = group_cache.get(group_name)
        if group is None:
            group = self._groups.get(group_name)
            if group is None:
                group = Group(name=group_name)
                self._groups[group_name] = group
            group_cache[group_name] = group

        group.channels.append(channel)
        self._channels.append(channel)
        self._channel_index[channel.name.lower()] = channel

    # ==================== Optimized Streaming Parser ====================
    
    def _load_and_parse_streaming(self, url: str) -> bool:
        """
        Stream the M3U over HTTP and parse it incrementally as bytes arrive.

        The download is the bottleneck (network-bound); parsing each line is
        cheap pure-Python work, so it is done inline on this thread. That keeps
        channels in playlist order and needs no locks. Supports HTTP 304
        (serve cache) and writes the cache after a successful 200.

        Args:
            url: The URL to download from

        Returns:
            True if parsing was successful, False otherwise
        """
        try:
            # Clear existing data
            self._groups = {}
            self._channels = []
            self._channel_index = {}

            # Build conditional headers for HTTP 304 support
            conditional_headers = self._get_conditional_headers(url) if self._cache_dir else {}

            # Make streaming request with retry (supports 304 Not Modified)
            self._report_progress(0, 0, "Connecting to server...")
            logger.info(f"Starting streaming download from {redact_url(url)}")
            response = self._request_with_retry(
                url, stream=True, 
                extra_headers=conditional_headers,
                allow_304=bool(conditional_headers)
            )

            # Handle 304 Not Modified — load from cache
            if response.status_code == 304:
                logger.info("✓ Server returned 304 Not Modified — loading from cache")
                self._report_progress(0, 0, "Content unchanged, loading from cache...")
                cache_path = self._get_cache_file_path(url)
                if os.path.isfile(cache_path):
                    if self.load_from_json(cache_path):
                        self._report_progress(
                            100, 100,
                            f"Loaded from cache: {len(self._channels)} channels in {len(self._groups)} groups"
                        )
                        return True
                # Cache file missing/corrupt — fall through to full re-download
                logger.warning("Cache file not found despite 304, re-downloading...")
                response = self._request_with_retry(url, stream=True)

            # Per-parse memoization of Group lookups. Single-threaded, so no
            # locks are needed and channel order is preserved.
            group_cache = {}

            # Statistics
            start_time = time.time()
            bytes_downloaded = 0

            # Try to get content length for progress reporting
            content_length = int(response.headers.get('content-length', 0))

            # Detect encoding from first chunk
            self._report_progress(0, content_length, "Detecting encoding...")
            first_chunk = next(response.iter_content(8192), b'')
            if not first_chunk:
                raise self.SourceError("Empty response from server", source=url)

            detected = chardet.detect(first_chunk)
            encoding = detected['encoding'] if detected['confidence'] > 0.7 else 'utf-8'
            logger.debug(f"Detected encoding: {encoding} (confidence: {detected.get('confidence', 0):.2f})")

            # Incremental decoder so multibyte characters that straddle a chunk
            # boundary are decoded correctly — a per-chunk decode would corrupt
            # any character split across two chunks.
            decoder = codecs.getincrementaldecoder(encoding)(errors='replace')

            # Process data in chunks with streaming parser. Strip a leading BOM
            # if present — str.strip() does NOT remove U+FEFF, so the header
            # check below would otherwise reject BOM-prefixed playlists.
            line_buffer = decoder.decode(first_chunk).lstrip('﻿')
            bytes_downloaded += len(first_chunk)

            # Validate M3U header
            if not line_buffer.strip().startswith("#EXTM3U"):
                raise self.ParseError(
                    "Invalid M3U format: missing #EXTM3U header",
                    line_number=1,
                    line_content=line_buffer[:50]
                )

            # Parsing state. current_extinf holds the most recent EXTINF
            # metadata until its stream-URL line arrives.
            current_extinf = None
            lines_processed = 0
            last_progress_time = time.time()

            def process_buffer(final: bool = False):
                """Pull complete lines out of line_buffer and parse them inline."""
                nonlocal line_buffer, current_extinf, lines_processed, last_progress_time

                # On the final flush, append a newline so a trailing line with
                # no line break still gets processed.
                if final and line_buffer and not line_buffer.endswith('\n'):
                    line_buffer += '\n'

                # Process complete lines
                while '\n' in line_buffer:
                    line, line_buffer = line_buffer.split('\n', 1)
                    line = line.strip()

                    if not line:
                        continue

                    lines_processed += 1

                    # Process EXTINF line
                    if line.startswith("#EXTINF:"):
                        current_extinf = self._parse_extinf(line)

                    # The line after an EXTINF is its stream URL
                    elif current_extinf and not line.startswith('#'):
                        self._add_channel_from_metadata(current_extinf, line, group_cache)
                        current_extinf = None

                # Report progress periodically (every 0.5 seconds)
                current_time = time.time()
                if current_time - last_progress_time >= 0.5:
                    self._report_progress(
                        bytes_downloaded,
                        content_length,
                        f"Downloaded {bytes_downloaded / 1024 / 1024:.1f} MB, {len(self._channels)} channels..."
                    )
                    last_progress_time = current_time

            # Parse the first chunk already buffered, then stream the rest.
            process_buffer()

            chunk_size = 65536  # 64KB chunks for optimal performance
            for chunk in response.iter_content(chunk_size):
                if chunk:
                    bytes_downloaded += len(chunk)
                    decoded_chunk = decoder.decode(chunk)
                    if decoded_chunk:
                        line_buffer += decoded_chunk
                        process_buffer()

            # Flush any bytes the incremental decoder held back, then any
            # remaining buffered line.
            tail = decoder.decode(b'', final=True)
            if tail:
                line_buffer += tail
            process_buffer(final=True)

            elapsed_time = time.time() - start_time
            speed_mbps = (bytes_downloaded / 1024 / 1024) / elapsed_time if elapsed_time > 0 else 0
            logger.info(
                f"Streaming load complete: {len(self._channels)} channels in "
                f"{len(self._groups)} groups, {bytes_downloaded / 1024 / 1024:.2f} MB "
                f"in {elapsed_time:.2f}s ({speed_mbps:.2f} MB/s, {lines_processed} lines)"
            )

            self._report_progress(
                bytes_downloaded,
                bytes_downloaded,
                f"Complete: {len(self._channels)} channels in {len(self._groups)} groups"
            )

            # Save to cache for future 304 support
            if self._cache_dir and len(self._channels) > 0:
                self._save_to_cache(url, response)

            return len(self._channels) > 0

        except self.NetworkError:
            raise
        except self.ParseError:
            raise
        except requests.RequestException as e:
            raise self.NetworkError(
                f"Network error during streaming download: {type(e).__name__}: {e}",
                url=url
            )
        except Exception as e:
            logger.error(f"Error in streaming parser: {type(e).__name__}: {e}")
            raise self.ParseError(f"Streaming parsing error: {type(e).__name__}: {e}")

    # ==================== Special Aggregate Groups ====================
    
    def _create_special_groups(self):
        """
        Create special aggregate groups after parsing:
        - All Channels: every loaded channel
        - All Livestreams: channels detected as LIVE
        - All VODs: channels detected as VOD
        
        These are always regenerated (not saved to cache) so they stay in sync.
        """
        if not self._channels:
            return
        
        # Remove any stale special groups first (in case of reload)
        for name in [self.SPECIAL_GROUP_ALL, self.SPECIAL_GROUP_LIVE, self.SPECIAL_GROUP_VOD]:
            self._groups.pop(name, None)
        
        # All Channels — a copy of every channel
        all_group = Group(name=self.SPECIAL_GROUP_ALL)
        all_group.channels = self._channels  # Direct reference, no copy needed
        self._groups[self.SPECIAL_GROUP_ALL] = all_group
        
        # All Livestreams
        live_channels = [ch for ch in self._channels if ch.channel_type == StreamType.LIVE.value]
        if live_channels:
            live_group = Group(name=self.SPECIAL_GROUP_LIVE)
            live_group.channels = live_channels
            self._groups[self.SPECIAL_GROUP_LIVE] = live_group
        
        # All VODs
        vod_channels = [ch for ch in self._channels if ch.channel_type == StreamType.VOD.value]
        if vod_channels:
            vod_group = Group(name=self.SPECIAL_GROUP_VOD)
            vod_group.channels = vod_channels
            self._groups[self.SPECIAL_GROUP_VOD] = vod_group
        
        logger.info(
            f"Created special groups: "
            f"{self.SPECIAL_GROUP_ALL} ({len(all_group.channels)}), "
            f"{self.SPECIAL_GROUP_LIVE} ({len(live_channels)}), "
            f"{self.SPECIAL_GROUP_VOD} ({len(vod_channels)})"
        )


    # ==================== Channel/Group Lookup Methods ====================
    
    def get_group(self, name: str) -> Optional[Group]:
        """
        Find a specific group by exact name.

        Args:
            name: Group name to find

        Returns:
            Group object or None if not found
        """
        return self._groups.get(name)

    def get_channel_by_name(self, channel_name: str) -> Optional[Channel]:
        """
        Find a channel by name across all groups.
        Uses indexed lookup for O(1) performance.

        Args:
            channel_name: Channel name to find

        Returns:
            Channel object or None if not found
        """
        return self._channel_index.get(channel_name.lower())

    def find_groups(self, pattern: Union[str, Pattern]) -> List[Group]:
        """
        Find groups matching a name pattern.

        Args:
            pattern: String or compiled regex pattern to match against group names

        Returns:
            List of matching Group objects
        """
        if isinstance(pattern, str):
            pattern = re.compile(pattern, re.IGNORECASE)

        return [group for group in self._groups.values()
                if pattern.search(group.name)]

    def search_channels(self, pattern: Union[str, Pattern],
                        search_fields: List[str] = None) -> List[Channel]:
        """
        Search for channels by name, ID, or other fields.

        Args:
            pattern: String or compiled regex pattern to match
            search_fields: List of Channel fields to search in (defaults to name and tvg_id)

        Returns:
            List of matching Channel objects
        """
        if search_fields is None:
            search_fields = ['name', 'tvg_id']

        if isinstance(pattern, str):
            pattern = re.compile(pattern, re.IGNORECASE)

        results = []

        for channel in self._channels:
            for field in search_fields:
                if hasattr(channel, field):
                    value = getattr(channel, field)
                    if value and pattern.search(value):
                        results.append(channel)
                        break

        return results

    def get_channels_by_type(self, stream_type: StreamType) -> List[Channel]:
        """
        Get all channels of a specific stream type.
        
        Args:
            stream_type: StreamType enum value
            
        Returns:
            List of matching Channel objects
        """
        return [ch for ch in self._channels if ch.channel_type == stream_type.value]

    # ==================== Utility Methods ====================
    
    def print_groups(self):
        """
        Print all groups and their channel counts to the console.
        """
        if not self._groups:
            print("No groups loaded.")
            return

        print(f"Total: {len(self._groups)} groups, {len(self._channels)} channels")
        print("-" * 50)

        for name, group in sorted(self._groups.items()):
            print(f"{name}: {len(group.channels)} channels")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about the loaded data.
        
        Returns:
            Dictionary with statistics
        """
        type_counts = {}
        for ch in self._channels:
            t = ch.channel_type or 'unknown'
            type_counts[t] = type_counts.get(t, 0) + 1
            
        return {
            'total_channels': len(self._channels),
            'total_groups': len(self._groups),
            'channels_by_type': type_counts,
            'interned_strings': len(self._interned_strings),
        }

    # ==================== JSON Serialization ====================
    
    def save_to_json(self, file_path: str) -> bool:
        """
        Save the loaded groups and channels to a JSON file.

        Args:
            file_path: Path where the JSON file will be saved

        Returns:
            True if saving was successful, False otherwise
        """
        try:
            # Create a serializable representation of the data
            data = {
                "groups": [],
                "default_group_name": self.default_group_name,
                "version": "2.1",  # Bumped: special groups no longer saved to cache
                "statistics": self.get_statistics()
            }

            # Build the groups array with their channels (skip special aggregate groups)
            for group_name, group in self._groups.items():
                if group_name in self.SPECIAL_GROUP_NAMES:
                    continue
                group_data = {
                    "name": group.name,
                    "channels": []
                }

                for channel in group.channels:
                    channel_data = {
                        "name": channel.name,
                        "stream_url": channel.stream_url,
                        "tvg_id": channel.tvg_id,
                        "tvg_logo": channel.tvg_logo,
                        "channel_type": channel.channel_type
                    }
                    group_data["channels"].append(channel_data)

                data["groups"].append(group_data)

            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            logger.info(f"Saved {len(self._channels)} channels to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving to JSON: {type(e).__name__}: {e}")
            return False

    def load_from_json(self, file_path: str) -> bool:
        """
        Load groups and channels from a JSON file.

        Args:
            file_path: Path to the JSON file to load

        Returns:
            True if loading was successful, False otherwise
        """
        try:
            # Clear existing data
            self._groups = {}
            self._channels = []
            self._channel_index = {}

            # Read JSON file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Reject old cache versions that may contain duplicate special groups.
            # Compare numerically — string compare is wrong (e.g. "2.10" < "2.9").
            cache_version = data.get("version", "1.0")
            try:
                version_tuple = tuple(int(p) for p in str(cache_version).split("."))
            except ValueError:
                version_tuple = (0,)
            if version_tuple < (2, 1):
                logger.info(f"Stale cache version {cache_version}, forcing fresh load")
                return False

            # Set default group name if provided
            if "default_group_name" in data:
                self.default_group_name = data["default_group_name"]

            # Process groups and channels
            for group_data in data.get("groups", []):
                group_name = self._intern_string(group_data.get("name", "Unknown"))
                group = Group(name=group_name)

                # Process channels in the group
                for channel_data in group_data.get("channels", []):
                    channel = Channel(
                        name=channel_data.get("name", "Unknown"),
                        stream_url=channel_data.get("stream_url", ""),
                        tvg_id=channel_data.get("tvg_id", ""),
                        tvg_logo=channel_data.get("tvg_logo", ""),
                        channel_type=channel_data.get("channel_type", "")
                    )
                    group.channels.append(channel)
                    self._channels.append(channel)
                    self._channel_index[channel.name.lower()] = channel

                self._groups[group_name] = group

            # Recreate special aggregate groups from loaded data
            self._create_special_groups()

            logger.info(f"Loaded {len(self._channels)} channels from {file_path}")
            return len(self._channels) > 0
        except FileNotFoundError:
            logger.error(f"JSON file not found: {file_path}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON format in {file_path}: {e}")
            return False
        except Exception as e:
            logger.error(f"Error loading from JSON: {type(e).__name__}: {e}")
            return False


if __name__ == "__main__":
    # Test the DataLoader with progress callback
    def progress_handler(current: int, total: int, message: str):
        if total > 0:
            percent = (current / total) * 100
            print(f"\r[{percent:5.1f}%] {message}", end="", flush=True)
        else:
            print(f"\r{message}", end="", flush=True)
    
    roi_url = "https://iptv-org.github.io/iptv/countries/il.m3u?type=m3u_plus&output=ts"
    print("Loading class...")
    loader = DataLoader()
    print("Loading data...")
    try:
        success = loader.load(roi_url, progress_callback=progress_handler)
        print()  # New line after progress
        if success:
            print(f"\nLoaded {len(loader.channels)} channels in {len(loader.groups)} groups")
            
            # Print statistics
            stats = loader.get_statistics()
            print(f"\nStatistics:")
            print(f"  - Channels by type: {stats['channels_by_type']}")
            print(f"  - Interned strings: {stats['interned_strings']}")
            
            # Test fast lookup
            if loader.channels:
                test_name = loader.channels[0].name
                start = time.time()
                for _ in range(10000):
                    loader.get_channel_by_name(test_name)
                elapsed = time.time() - start
                print(f"  - 10,000 lookups in {elapsed*1000:.2f}ms")
            
            loader.print_groups()
    except Exception as e:
        print(f"\nAn error occurred: {type(e).__name__}: {e}")

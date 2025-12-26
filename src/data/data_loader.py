import json
import sys
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
import chardet
from collections import defaultdict
from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot, QThread
import threading
from queue import Queue
import concurrent.futures
import time

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class StreamType(Enum):
    """Enumeration of stream types."""
    LIVE = "live"
    VOD = "vod"
    SERIES = "series"
    UNKNOWN = "unknown"


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
                # Truncate long URLs
                display_source = source[:80] + "..." if len(source) > 80 else source
                detailed_msg += f" [Source: {display_source}]"
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
    
    def __init__(self, default_group_name: str = "Ungrouped"):
        """
        Initialize the M3U parser.

        Args:
            default_group_name: Name for channels without a specified group
        """
        self._groups: Dict[str, Group] = {}
        self._channels: List[Channel] = []
        self._channel_index: Dict[str, Channel] = {}  # Fast lookup by lowercase name
        self.default_group_name = default_group_name
        
        # String interning cache for memory optimization
        self._interned_strings: Dict[str, str] = {}
        
        # Progress tracking
        self._progress_callback: Optional[Callable[[int, int, str], None]] = None

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
        timeout: int = 30
    ) -> requests.Response:
        """
        Make an HTTP GET request with exponential backoff retry logic.
        
        Args:
            url: URL to request
            stream: Whether to stream the response
            timeout: Request timeout in seconds
            
        Returns:
            requests.Response object
            
        Raises:
            NetworkError: If all retries fail
        """
        last_exception = None
        delay = self.INITIAL_RETRY_DELAY
        
        for attempt in range(self.MAX_RETRIES):
            try:
                response = requests.get(
                    url, 
                    headers=self.DEFAULT_HEADERS,
                    stream=stream, 
                    timeout=timeout
                )
                response.raise_for_status()
                return response
                
            except requests.exceptions.Timeout as e:
                last_exception = e
                logger.warning(f"Request timeout (attempt {attempt + 1}/{self.MAX_RETRIES}): {url}")
                
            except requests.exceptions.ConnectionError as e:
                last_exception = e
                logger.warning(f"Connection error (attempt {attempt + 1}/{self.MAX_RETRIES}): {url}")
                
            except requests.exceptions.HTTPError as e:
                # Don't retry on client errors (4xx) except 429 (rate limit)
                if e.response is not None and 400 <= e.response.status_code < 500:
                    if e.response.status_code == 429:
                        # Rate limited - wait longer
                        delay = min(delay * 2, self.MAX_RETRY_DELAY)
                        logger.warning(f"Rate limited (attempt {attempt + 1}/{self.MAX_RETRIES}), waiting {delay}s")
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
            
            # Wait before retry (exponential backoff)
            if attempt < self.MAX_RETRIES - 1:
                logger.info(f"Retrying in {delay:.1f} seconds...")
                time.sleep(delay)
                delay = min(delay * self.BACKOFF_MULTIPLIER, self.MAX_RETRY_DELAY)
        
        # All retries exhausted
        raise self.NetworkError(
            f"Failed to fetch URL after {self.MAX_RETRIES} attempts: {last_exception}",
            url=url,
            retry_count=self.MAX_RETRIES
        )

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

    # ==================== Main Loading Methods ====================
    
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
                return self._load_and_parse_streaming(source)

            # Fall back to traditional method for files and direct content
            self._report_progress(0, 0, "Fetching content...")
            content = self._get_content(source)
            if not content:
                return False

            return self._parse(content)
            
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

        # Optimize line splitting for large files
        content = content.replace('\r\n', '\n').replace('\r', '\n')
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
                        
                        # Detect stream type
                        stream_type = self.detect_stream_type(
                            stream_url, 
                            metadata.get('name', ''),
                            metadata
                        )

                        # Create channel with parsed metadata
                        channel = Channel(
                            name=metadata.get('name', f"Channel_{len(self._channels) + 1}"),
                            stream_url=stream_url,
                            tvg_id=metadata.get('tvg-id', ''),
                            tvg_logo=metadata.get('tvg-logo', ''),
                            channel_type=stream_type.value
                        )

                        # Add channel to appropriate group using cache for performance
                        # Use string interning for memory optimization
                        group_name = self._intern_string(
                            metadata.get('group-title', self.default_group_name)
                        )

                        if group_name not in group_cache:
                            if group_name not in self._groups:
                                self._groups[group_name] = Group(name=group_name)
                            group_cache[group_name] = self._groups[group_name]

                        group_cache[group_name].channels.append(channel)
                        self._channels.append(channel)
                        
                        # Update channel index for fast lookup
                        self._channel_index[channel.name.lower()] = channel
                        
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

    # ==================== Optimized Streaming Parser ====================
    
    def _load_and_parse_streaming(self, url: str) -> bool:
        """
        Optimized streaming loader that downloads and parses M3U in parallel chunks.
        This significantly improves loading speed by:
        1. Streaming download (processing data as it arrives)
        2. Incremental parsing (parsing lines immediately)
        3. Parallel processing (using thread pool for channel creation)

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

            # Shared data structures with thread safety
            groups_lock = threading.Lock()
            channels_lock = threading.Lock()
            group_cache = {}

            # Statistics
            start_time = time.time()
            bytes_downloaded = 0

            # Make streaming request with retry
            self._report_progress(0, 0, "Connecting to server...")
            logger.info(f"Starting optimized streaming download from {url}")
            response = self._request_with_retry(url, stream=True)

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

            # Process data in chunks with streaming parser
            line_buffer = first_chunk.decode(encoding, errors='replace')
            bytes_downloaded += len(first_chunk)

            # Validate M3U header
            if not line_buffer.strip().startswith("#EXTM3U"):
                raise self.ParseError(
                    "Invalid M3U format: missing #EXTM3U header",
                    line_number=1,
                    line_content=line_buffer[:50]
                )

            # Queue for parallel processing
            channel_queue = Queue()
            processing_complete = threading.Event()

            # Worker function for parallel channel processing
            def process_channel_worker():
                while not processing_complete.is_set() or not channel_queue.empty():
                    try:
                        item = channel_queue.get(timeout=0.1)
                        if item is None:  # Poison pill
                            break

                        metadata, stream_url = item
                        
                        # Detect stream type
                        stream_type = self.detect_stream_type(
                            stream_url,
                            metadata.get('name', ''),
                            metadata
                        )

                        # Create channel
                        channel = Channel(
                            name=metadata.get('name', f"Channel_{len(self._channels) + 1}"),
                            stream_url=stream_url,
                            tvg_id=metadata.get('tvg-id', ''),
                            tvg_logo=metadata.get('tvg-logo', ''),
                            channel_type=stream_type.value
                        )

                        # Add to appropriate group (thread-safe)
                        # Use string interning for memory optimization
                        group_name = self._intern_string(
                            metadata.get('group-title', self.default_group_name)
                        )

                        with groups_lock:
                            if group_name not in group_cache:
                                if group_name not in self._groups:
                                    self._groups[group_name] = Group(name=group_name)
                                group_cache[group_name] = self._groups[group_name]

                            group_cache[group_name].channels.append(channel)

                        with channels_lock:
                            self._channels.append(channel)
                            self._channel_index[channel.name.lower()] = channel

                        channel_queue.task_done()
                    except Exception:
                        pass

            # Start worker threads (4 workers for parallel processing)
            num_workers = 4
            workers = []
            for _ in range(num_workers):
                worker = threading.Thread(target=process_channel_worker, daemon=True)
                worker.start()
                workers.append(worker)

            # Parse incrementally as chunks arrive
            current_extinf = None
            lines_processed = 0
            last_progress_time = time.time()

            def process_lines(text_chunk):
                nonlocal line_buffer, current_extinf, lines_processed, bytes_downloaded, last_progress_time

                line_buffer += text_chunk

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

                    # Process stream URL
                    elif current_extinf and not line.startswith('#'):
                        stream_url = line
                        # Queue for parallel processing
                        channel_queue.put((current_extinf, stream_url))
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

            # Process first chunk
            process_lines("")

            # Stream remaining chunks
            chunk_size = 65536  # 64KB chunks for optimal performance
            for chunk in response.iter_content(chunk_size):
                if chunk:
                    bytes_downloaded += len(chunk)
                    decoded_chunk = chunk.decode(encoding, errors='replace')
                    process_lines(decoded_chunk)

            # Process any remaining buffered data
            if line_buffer.strip():
                process_lines("\n")

            # Wait for all queued items to be processed
            self._report_progress(bytes_downloaded, content_length, "Finalizing...")
            logger.debug("Waiting for worker threads to complete processing...")
            channel_queue.join()

            # Signal workers to stop
            processing_complete.set()
            for _ in range(num_workers):
                channel_queue.put(None)  # Poison pill for each worker

            # Wait for workers to finish
            for worker in workers:
                worker.join(timeout=5)

            elapsed_time = time.time() - start_time
            speed_mbps = (bytes_downloaded / 1024 / 1024) / elapsed_time if elapsed_time > 0 else 0

            logger.info(f"✓ Optimized loading complete:")
            logger.info(f"  - Downloaded: {bytes_downloaded / 1024 / 1024:.2f} MB")
            logger.info(f"  - Time: {elapsed_time:.2f} seconds")
            logger.info(f"  - Speed: {speed_mbps:.2f} MB/s")
            logger.info(f"  - Lines processed: {lines_processed}")
            logger.info(f"  - Channels loaded: {len(self._channels)}")
            logger.info(f"  - Groups: {len(self._groups)}")

            self._report_progress(
                bytes_downloaded, 
                bytes_downloaded,
                f"Complete: {len(self._channels)} channels in {len(self._groups)} groups"
            )

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
                "version": "2.0",  # Version for future compatibility
                "statistics": self.get_statistics()
            }

            # Build the groups array with their channels
            for group_name, group in self._groups.items():
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

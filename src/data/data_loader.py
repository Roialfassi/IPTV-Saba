import json

from src.model.group_model import Group
from src.model.channel_model import Channel
import requests
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Union, Pattern, Callable
import re
from urllib.parse import urlparse
import os
import logging
import io
try:
    import chardet
    CHARDET_AVAILABLE = True
except ImportError:
    CHARDET_AVAILABLE = False
from collections import defaultdict
from PyQt5.QtCore import pyqtSignal, QObject, pyqtSlot, QThread
import threading
from queue import Queue
import concurrent.futures
import time

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class DataLoader:
    """
    Parser for M3U playlists that organizes channels into groups.
    Supports loading from URLs, local files, or string content.
    """

    class ParseError(Exception):
        """Exception raised for parsing errors."""
        pass

    class SourceError(Exception):
        """Exception raised for source retrieval errors."""
        pass

    def __init__(self, default_group_name: str = "Ungrouped"):
        """
        Initialize the M3U parser.

        Args:
            default_group_name: Name for channels without a specified group
        """
        self._groups: Dict[str, Group] = {}
        self._channels: List[Channel] = []
        self.default_group_name = default_group_name

    @property
    def groups(self) -> Dict[str, Group]:
        """Get all channel groups as a dictionary keyed by group name."""
        return self._groups

    @property
    def channels(self) -> List[Channel]:
        """Get all channels across all groups."""
        return self._channels

    def _detect_encoding(self, content: bytes) -> str:
        """
        Detect encoding of byte content.
        Falls back to UTF-8 if chardet is not available.

        Args:
            content: Byte content to detect encoding for

        Returns:
            Encoding name (e.g., 'utf-8', 'iso-8859-1')
        """
        if CHARDET_AVAILABLE:
            detected = chardet.detect(content)
            if detected and detected.get('confidence', 0) > 0.7:
                return detected['encoding']
        # Fallback to UTF-8 if chardet unavailable or low confidence
        return 'utf-8'

    def load(self, source: str, use_optimized: bool = True) -> bool:
        """
        Load and parse M3U data from various sources.

        Args:
            source: URL, file path, or M3U content string
            use_optimized: Use optimized streaming parser (default True)

        Returns:
            True if parsing was successful, False otherwise
        """
        try:
            # Use optimized streaming parser for URLs
            parsed_url = urlparse(source)
            if use_optimized and parsed_url.scheme in ('http', 'https'):
                logger.info("Using optimized streaming parser for faster loading")
                return self._load_and_parse_streaming(source)

            # Fall back to traditional method for files and direct content
            content = self._get_content(source)
            if not content:
                return False

            return self._parse(content)
        except (self.ParseError, self.SourceError) as e:
            logging.error(f"Error loading source: {e}")
            return False
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return False

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
                response = requests.get(source, timeout=30)
                response.raise_for_status()

                # Detect encoding
                encoding = response.encoding
                if not encoding or encoding.lower() == 'iso-8859-1':
                    encoding = self._detect_encoding(response.content)

                return response.content.decode(encoding, errors='replace')
            except requests.RequestException as e:
                raise self.SourceError(f"Failed to fetch M3U from URL: {e}")

        # Check if source is a local file
        if os.path.isfile(source):
            try:
                with open(source, 'rb') as f:
                    content = f.read()

                # Detect encoding
                encoding = self._detect_encoding(content)

                return content.decode(encoding, errors='replace')
            except (IOError, UnicodeDecodeError) as e:
                raise self.SourceError(f"Failed to read M3U from file: {e}")

        # Treat source as direct content if it starts with M3U header
        if "#EXTM3U" in source[:20]:
            return source

        raise self.SourceError("Invalid source: not a URL, file path, or M3U content")

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

        # Cache for group instances to avoid dictionary lookups
        group_cache = {}

        # Pre-compile regex patterns for better performance
        attr_pattern = re.compile(r'([\w-]+)="([^"]*)"')
        alt_attr_pattern = re.compile(r'([\w-]+)=([^ "]+)')
        name_pattern = re.compile(r'#EXTINF:.*?,(.*?)$')

        # Optimize line splitting for large files
        content = content.replace('\r\n', '\n').replace('\r', '\n')
        lines = content.split('\n')

        # Check for valid M3U header
        if not lines or not lines[0].strip().startswith("#EXTM3U"):
            raise self.ParseError("Invalid M3U format: missing #EXTM3U header")

        i = 1
        while i < len(lines):
            line = lines[i].strip()

            # Skip empty lines
            if not line:
                i += 1
                continue

            try:
                # Process info line
                if line.startswith("#EXTINF:"):
                    metadata = self._parse_extinf(line, name_pattern, attr_pattern, alt_attr_pattern)

                    # Look for the stream URL in subsequent lines
                    i += 1
                    while i < len(lines) and (not lines[i].strip() or lines[i].strip().startswith('#')):
                        # Skip empty lines and tags we don't need to process
                        i += 1

                    if i < len(lines) and lines[i].strip() and not lines[i].strip().startswith('#'):
                        stream_url = lines[i].strip()

                        # Create channel with parsed metadata
                        channel = Channel(
                            name=metadata.get('name', f"Channel_{len(self._channels) + 1}"),
                            stream_url=stream_url,
                            tvg_id=metadata.get('tvg-id', ''),
                            tvg_logo=metadata.get('tvg-logo', '')
                        )

                        # Add channel to appropriate group using cache for performance
                        group_name = metadata.get('group-title', self.default_group_name)

                        if group_name not in group_cache:
                            if group_name not in self._groups:
                                self._groups[group_name] = Group(name=group_name)
                            group_cache[group_name] = self._groups[group_name]

                        group_cache[group_name].channels.append(channel)
                        self._channels.append(channel)
            except Exception as e:
                # Log the error but continue parsing
                logger.warning(f"Error parsing line {i}: {e}")

            i += 1

        return len(self._channels) > 0

    def _parse_extinf(self, line: str, name_pattern: Pattern, attr_pattern: Pattern,
                      alt_attr_pattern: Pattern) -> Dict[str, str]:
        """
        Parse the EXTINF line to extract metadata.

        Args:
            line: EXTINF line from M3U file
            name_pattern: Compiled regex for extracting channel name
            attr_pattern: Compiled regex for extracting quoted attributes
            alt_attr_pattern: Compiled regex for extracting unquoted attributes

        Returns:
            Dictionary of metadata attributes
        """
        metadata = {}

        # Extract the channel name (after the comma)
        name_match = name_pattern.search(line)
        if name_match:
            metadata['name'] = name_match.group(1).strip()

        # Extract attributes within quotes
        for match in attr_pattern.finditer(line):
            key, value = match.groups()
            metadata[key] = value.strip()

        # Handle alternative attribute formats (without quotes)
        for match in alt_attr_pattern.finditer(line):
            key, value = match.groups()
            if key not in metadata:  # Don't override quoted values
                metadata[key] = value.strip()

        return metadata

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

            # Shared data structures with thread safety
            groups_lock = threading.Lock()
            channels_lock = threading.Lock()
            group_cache = {}

            # Pre-compile regex patterns for better performance
            attr_pattern = re.compile(r'([\w-]+)="([^"]*)"')
            alt_attr_pattern = re.compile(r'([\w-]+)=([^ "]+)')
            name_pattern = re.compile(r'#EXTINF:.*?,(.*?)$')

            # Statistics
            start_time = time.time()
            bytes_downloaded = 0

            # Make streaming request
            logger.info(f"Starting optimized streaming download from {url}")
            response = requests.get(url, stream=True, timeout=30)
            response.raise_for_status()

            # Detect encoding from first chunk
            first_chunk = next(response.iter_content(8192), b'')
            if not first_chunk:
                raise self.SourceError("Empty response from server")

            encoding = self._detect_encoding(first_chunk)
            logger.debug(f"Detected encoding: {encoding}")

            # Process data in chunks with streaming parser
            line_buffer = first_chunk.decode(encoding, errors='replace')
            bytes_downloaded += len(first_chunk)

            # Validate M3U header
            if not line_buffer.strip().startswith("#EXTM3U"):
                raise self.ParseError("Invalid M3U format: missing #EXTM3U header")

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

                        # Create channel
                        channel = Channel(
                            name=metadata.get('name', f"Channel_{len(self._channels) + 1}"),
                            stream_url=stream_url,
                            tvg_id=metadata.get('tvg-id', ''),
                            tvg_logo=metadata.get('tvg-logo', '')
                        )

                        # Add to appropriate group (thread-safe)
                        group_name = metadata.get('group-title', self.default_group_name)

                        with groups_lock:
                            if group_name not in group_cache:
                                if group_name not in self._groups:
                                    self._groups[group_name] = Group(name=group_name)
                                group_cache[group_name] = self._groups[group_name]

                            group_cache[group_name].channels.append(channel)

                        with channels_lock:
                            self._channels.append(channel)

                        channel_queue.task_done()
                    except:
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

            def process_lines(text_chunk):
                nonlocal line_buffer, current_extinf, lines_processed

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
                        current_extinf = self._parse_extinf(line, name_pattern, attr_pattern, alt_attr_pattern)

                    # Process stream URL
                    elif current_extinf and not line.startswith('#'):
                        stream_url = line
                        # Queue for parallel processing
                        channel_queue.put((current_extinf, stream_url))
                        current_extinf = None

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

            return len(self._channels) > 0

        except requests.RequestException as e:
            logger.error(f"Network error during streaming download: {e}")
            raise self.SourceError(f"Failed to fetch M3U from URL: {e}")
        except Exception as e:
            logger.error(f"Error in streaming parser: {e}")
            raise self.ParseError(f"Parsing error: {e}")

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

        Args:
            channel_name: Channel name to find

        Returns:
            Channel object or None if not found
        """
        for channel in self._channels:
            if channel.name.lower() == channel_name.lower():
                return channel
        return None

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
                "default_group_name": self.default_group_name
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
                        "tvg_logo": channel.tvg_logo
                    }
                    group_data["channels"].append(channel_data)

                data["groups"].append(group_data)

            # Write to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)

            return True
        except Exception as e:
            logger.error(f"Error saving to JSON: {e}")
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

            # Read JSON file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Set default group name if provided
            if "default_group_name" in data:
                self.default_group_name = data["default_group_name"]

            # Process groups and channels
            for group_data in data.get("groups", []):
                group_name = group_data.get("name", "Unknown")
                group = Group(name=group_name)

                # Process channels in the group
                for channel_data in group_data.get("channels", []):
                    channel = Channel(
                        name=channel_data.get("name", "Unknown"),
                        stream_url=channel_data.get("stream_url", ""),
                        tvg_id=channel_data.get("tvg_id", ""),
                        tvg_logo=channel_data.get("tvg_logo", "")
                    )
                    group.channels.append(channel)
                    self._channels.append(channel)

                self._groups[group_name] = group

            return len(self._channels) > 0
        except Exception as e:
            logger.error(f"Error loading from JSON: {e}")
            return False

if __name__ == "__main__":
    # Test the DataLoader
    roi_url = "https://iptv-org.github.io/iptv/countries/il.m3u?type=m3u_plus&output=ts"  # Replace with your actual URL
    print("loading class")
    loader = DataLoader()
    print("loading data")
    try:
        success = loader.load(roi_url)
        if success:
            print(f"Loaded {len(loader.channels)} channels in {len(loader.groups)} groups")
            # Print all groups
            loader.print_groups()
    except Exception as e:
        print(f"An error occurred: {e}")

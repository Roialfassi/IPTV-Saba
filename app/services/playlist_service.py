"""M3U/M3U8 Playlist parser and manager."""
import re
import logging
import requests
from typing import List, Dict
from pathlib import Path

from app.models.channel import Channel

logger = logging.getLogger(__name__)


class PlaylistService:
    """Parse and manage M3U playlists."""

    def __init__(self):
        self.channels: List[Channel] = []
        self.groups: Dict[str, List[Channel]] = {}

    def load_from_url(self, url: str) -> bool:
        """Load playlist from URL."""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            content = response.text
            return self._parse_m3u(content)
        except Exception as e:
            logger.error(f"Failed to load playlist: {e}")
            return False

    def load_from_file(self, filepath: Path) -> bool:
        """Load playlist from file."""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            return self._parse_m3u(content)
        except Exception as e:
            logger.error(f"Failed to load playlist file: {e}")
            return False

    def _parse_m3u(self, content: str) -> bool:
        """Parse M3U content."""
        try:
            self.channels.clear()
            self.groups.clear()

            lines = content.split('\n')
            i = 0

            while i < len(lines):
                line = lines[i].strip()

                if line.startswith('#EXTINF:'):
                    channel = self._parse_extinf(line, lines, i)
                    if channel:
                        self.channels.append(channel)

                        if channel.group not in self.groups:
                            self.groups[channel.group] = []
                        self.groups[channel.group].append(channel)

                i += 1

            logger.info(f"Loaded {len(self.channels)} channels in {len(self.groups)} groups")
            return True

        except Exception as e:
            logger.error(f"Failed to parse M3U: {e}")
            return False

    def _parse_extinf(self, extinf_line: str, lines: List[str], current_index: int) -> Optional[Channel]:
        """Parse EXTINF line and extract channel info."""
        try:
            tvg_id = self._extract_attribute(extinf_line, 'tvg-id')
            tvg_name = self._extract_attribute(extinf_line, 'tvg-name')
            tvg_logo = self._extract_attribute(extinf_line, 'tvg-logo')
            group = self._extract_attribute(extinf_line, 'group-title') or "Unknown"

            name_match = re.search(r',(.+)$', extinf_line)
            name = name_match.group(1).strip() if name_match else "Unknown"

            url = ""
            for i in range(current_index + 1, len(lines)):
                if lines[i].strip() and not lines[i].startswith('#'):
                    url = lines[i].strip()
                    break

            if url:
                return Channel(
                    name=name,
                    url=url,
                    group=group,
                    tvg_id=tvg_id,
                    tvg_name=tvg_name,
                    tvg_logo=tvg_logo
                )

        except Exception as e:
            logger.warning(f"Failed to parse EXTINF: {e}")

        return None

    def _extract_attribute(self, line: str, attr: str) -> str:
        """Extract attribute from EXTINF line."""
        pattern = f'{attr}="([^"]*)"'
        match = re.search(pattern, line)
        return match.group(1) if match else ""

    def search(self, query: str) -> List[Channel]:
        """Search channels by name."""
        query = query.lower()
        return [ch for ch in self.channels if query in ch.name.lower()]

    def get_group_names(self) -> List[str]:
        """Get all group names."""
        return sorted(self.groups.keys())

    def get_channels_in_group(self, group_name: str) -> List[Channel]:
        """Get channels in specific group."""
        return self.groups.get(group_name, [])

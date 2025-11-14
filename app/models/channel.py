"""Channel data model."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class Channel:
    """IPTV Channel."""
    name: str
    url: str
    group: str = ""
    tvg_id: str = ""
    tvg_logo: str = ""
    tvg_name: str = ""

    def __hash__(self):
        return hash((self.name, self.url))

    def __eq__(self, other):
        if not isinstance(other, Channel):
            return False
        return self.name == other.name and self.url == other.url

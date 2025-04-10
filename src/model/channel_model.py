from dataclasses import dataclass, field
from typing import Any, Dict
import re
import requests
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@dataclass
class Channel:
    """
    Represents a TV channel with streaming information.

    Attributes:
        name (str): The name of the channel.
        stream_url (str): The URL from which the channel is streamed.
        tvg_id (str): The TV guide identifier for the channel.
        tvg_logo (str): The URL to the channel's logo.
    """
    name: str
    stream_url: str
    tvg_id: str = ""
    tvg_logo: str = ""
    channel_type: str = ""

    def __str__(self) -> str:
        """
        Returns a string representation of the Channel.
        """
        return f"{self.name} (ID: {self.tvg_id})"

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes the Channel instance to a dictionary.

        Returns:
            Dict[str, Any]: The serialized channel data.
        """
        return {
            "name": self.name,
            "stream_url": self.stream_url,
            "tvg_id": self.tvg_id,
            "tvg_logo": self.tvg_logo,
            "channel_type":self.channel_type

        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Channel':
        """
        Creates a Channel instance from a dictionary.

        Args:
            data (Dict[str, Any]): The data to create the Channel from.

        Returns:
            Channel: The created Channel instance.
        """
        try:
            return cls(
                name=data.get("name", ""),
                stream_url=data.get("stream_url", ""),
                tvg_id=data.get("tvg_id", ""),
                tvg_logo=data.get("tvg_logo", ""),
                channel_type=data.get("channel_type", "")
            )
        except KeyError as e:
            logger.error(f"Missing key in channel data: {e}")
            raise ValueError(f"Invalid channel data: missing {e}")

    def update(self, **kwargs) -> None:
        """
        Updates the Channel's attributes with provided keyword arguments.

        Args:
            **kwargs: Attribute names and their new values.
        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
                logger.debug(f"Updated {key} to {value} for channel {self.name}")
            else:
                logger.warning(f"Tried to update non-existent attribute '{key}' on Channel")

    def validate_stream_url(self) -> bool:
        """
        Validates the stream URL by checking if it's a properly formatted URL and reachable.

        Returns:
            bool: True if valid, False otherwise.
        """
        if not self._is_valid_url(self.stream_url):
            logger.error(f"Invalid stream URL format: {self.stream_url}")
            return False
        try:
            response = requests.head(self.stream_url, timeout=5)
            is_valid = response.status_code == 200
            if is_valid:
                logger.debug(f"Stream URL is reachable: {self.stream_url}")
            else:
                logger.error(f"Stream URL returned status code {response.status_code}: {self.stream_url}")
            return is_valid
        except requests.RequestException as e:
            logger.error(f"Error validating stream URL '{self.stream_url}': {e}")
            return False

    def validate_tvg_logo(self) -> bool:
        """
        Validates the TVG logo URL by checking if it's a properly formatted URL and the image exists.

        Returns:
            bool: True if valid, False otherwise.
        """
        if not self._is_valid_url(self.tvg_logo):
            logger.error(f"Invalid TVG logo URL format: {self.tvg_logo}")
            return False
        try:
            response = requests.head(self.tvg_logo, timeout=5)
            is_valid = response.status_code == 200 and 'image' in response.headers.get('Content-Type', '')
            if is_valid:
                logger.debug(f"TVG logo URL is valid and points to an image: {self.tvg_logo}")
            else:
                logger.error(f"TVG logo URL is invalid or does not point to an image: {self.tvg_logo}")
            return is_valid
        except requests.RequestException as e:
            logger.error(f"Error validating TVG logo URL '{self.tvg_logo}': {e}")
            return False

    def download_logo(self, save_path: str) -> bool:
        """
        Downloads the TVG logo image to the specified path.

        Args:
            save_path (str): The file path where the logo will be saved.

        Returns:
            bool: True if download is successful, False otherwise.
        """
        if not self.tvg_logo:
            logger.error("No TVG logo URL provided.")
            return False
        try:
            response = requests.get(self.tvg_logo, stream=True, timeout=10)
            if response.status_code == 200 and 'image' in response.headers.get('Content-Type', ''):
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(1024):
                        f.write(chunk)
                logger.debug(f"Downloaded TVG logo to {save_path}")
                return True
            else:
                logger.error(f"Failed to download TVG logo, status code {response.status_code}")
                return False
        except requests.RequestException as e:
            logger.error(f"Error downloading TVG logo '{self.tvg_logo}': {e}")
            return False

    @staticmethod
    def _is_valid_url(url: str) -> bool:
        """
        Validates the format of a URL using regex.

        Args:
            url (str): The URL to validate.

        Returns:
            bool: True if the URL is valid, False otherwise.
        """
        regex = re.compile(
            r'^(?:http|https)://'  # http:// or https://
            r'(?:\S+)'  # Non-whitespace characters
        )
        is_valid = re.match(regex, url) is not None
        if not is_valid:
            logger.debug(f"URL is invalid: {url}")
        return is_valid

    def __eq__(self, other: Any) -> bool:
        """
        Checks equality based on the tvg_id and stream_url.

        Args:
            other (Any): The other object to compare.

        Returns:
            bool: True if equal, False otherwise.
        """
        if not isinstance(other, Channel):
            return False
        return (self.name, self.stream_url) == (other.name, other.stream_url)

    def __hash__(self) -> int:
        """
        Returns a hash based on the tvg_id and stream_url.

        Returns:
            int: The hash value.
        """
        return hash((self.name, self.stream_url))

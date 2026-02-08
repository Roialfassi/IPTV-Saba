from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import json
import logging
import re
import requests

# Configure logging
from src.data.data_loader import DataLoader
from src.model.channel_model import Channel

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@dataclass
class Profile:
    name: str
    url: str
    favorites: List[Channel] = field(default_factory=list)
    history: List[Channel] = field(default_factory=list)
    last_loaded: Optional[int] = None
    max_history_items: int = 50

    def __init__(self, name: str, url: str, favorites: Optional[List[Channel]] = None,
                 history: Optional[List[Channel]] = None, last_loaded: Optional[int] = None):
        """
        Initializes a Profile instance.

        Args:
            name (str): The name of the profile.
            url (str): The IPTV playlist URL associated with the profile.
            favorites (Optional[List[str]]): A list of favorite channel names.
            history (Optional[List[str]]): A list of recently watched channel names.
            last_loaded (Optional[str]): ISO format timestamp of the last data loading.
        """
        self.name = name
        self.url = url
        self.favorites = favorites if favorites is not None else []
        self.history = history if history is not None else []
        self.last_loaded = last_loaded  # ISO formatted string
        self.max_history_items = 50

    def add_favorite(self, channel: Channel):
        """
        Adds a channel to the favorites list if not already present.

        Args:
            channel_name (Channel): The name of the channel to add.
        """
        if channel not in self.favorites:
            self.favorites.append(channel)

    def remove_favorite(self, channel: Channel):
        """
        Removes a channel from the favorites list if present.

        Args:
            :param channel:
        """
        if channel in self.favorites:
            self.favorites.remove(channel)

    def add_history(self, channel: Channel):
        """
        Adds a channel to the history list, ensuring a maximum of 20 entries.

        Args:
            :param channel:
        """
        if channel in self.history:
            self.history.remove(channel)
        self.history.insert(0, channel)
        if len(self.history) > self.max_history_items:
            self.history.pop()

    def update_last_loaded(self):
        """
        Updates the last_loaded timestamp to the current UTC time in ISO format.
        """
        self.last_loaded = int(round(datetime.now().timestamp()))

    def needs_refresh(self) -> bool:
        """
        Determines whether the channel data needs to be refreshed based on the last_loaded timestamp.

        Returns:
            bool: True if data needs to be refreshed (i.e., last_loaded was over 24 hours ago or never), False otherwise.
        """
        if not self.last_loaded:
            return True
        last_loaded_time = datetime.fromtimestamp(self.last_loaded)
        return (datetime.utcnow() - last_loaded_time).total_seconds() > 86400  # 24 hours

    def __str__(self) -> str:
        """
        Returns a string representation of the Profile.

        Returns:
            str: A JSON string of the profile's data.
        """
        return json.dumps(self.to_dict(), indent=4)

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes the Profile instance to a dictionary.

        Returns:
            Dict[str, Any]: The serialized profile data.
        """
        return {
            "name": self.name,
            "url": self.url,
            "favorites": [channel.to_dict() for channel in self.favorites],
            "history": [channel.to_dict() for channel in self.history],
            "last_loaded": self.last_loaded
        }

    def to_json(self) -> str:
        """
        Serializes the Profile instance to a JSON string.

        Returns:
            str: The JSON string of the profile's data.
        """
        try:
            profile_json = json.dumps(self.to_dict())
            logger.debug(f"Serialized profile '{self.name}' to JSON.")
            return profile_json
        except (TypeError, ValueError) as e:
            logger.error(f"Error serializing profile '{self.name}' to JSON: {e}")
            raise

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Profile':
        """
        Creates a Profile instance from a dictionary.

        Args:
            data (Dict[str, Any]): The data to create the Profile from.

        Returns:
            Profile: The created Profile instance.
        """
        try:
            favorites = [Channel.from_dict(ch) for ch in data.get('favorites', [])]
            history = [Channel.from_dict(ch) for ch in data.get('history', [])]
            return cls(
                name=data['name'],
                url=data['url'],
                favorites=favorites,
                history=history,
                last_loaded=data.get('last_loaded')
            )
        except KeyError as e:
            logger.error(f"Missing key in profile data: {e}")
            raise ValueError(f"Invalid profile data: missing {e}")

    @classmethod
    def from_json(cls, json_str: str) -> 'Profile':
        """
        Creates a Profile instance from a JSON string.

        Args:
            json_str (str): A JSON string containing profile data.

        Returns:
            Profile: The created Profile instance.
        """
        try:
            data = json.loads(json_str)
            logger.debug("Deserialized JSON to profile data.")
            return cls.from_dict(data)
        except json.JSONDecodeError as e:
            logger.error(f"Error decoding JSON: {e}")
            raise

    def update_profile(self, name: Optional[str] = None, url: Optional[str] = None) -> None:
        """
        Updates the profile's name and/or URL.

        Args:
            name (Optional[str]): New name for the profile.
            url (Optional[str]): New URL for the profile.
        """
        if name:
            logger.debug(f"Updating profile name from '{self.name}' to '{name}'.")
            self.name = name
        if url:
            logger.debug(f"Updating profile URL from '{self.url}' to '{url}'.")
            self.url = url

    def add_to_history(self, channel: Channel) -> None:
        """
        Adds a channel to the history. If the channel exists, moves it to the first position.
        Ensures the history list does not exceed 10 elements.

        Args:
            channel (str): The channel name to add to the history.
        """
        try:
            channel_index = self.is_in_history(channel.name)
            if channel_index > -1:
                self.remove_from_history(channel)
                logger.debug(f"Moved channel '{channel}' to the top of history.")
            else:
                logger.debug(f"Added new channel '{channel}' to history.")

            self.history.insert(0, channel)

            if len(self.history) > 10:
                removed = self.history.pop()
                logger.debug(f"Removed oldest channel '{removed}' from history to maintain size.")
        except Exception as e:
            logger.error(f"Error adding to history {e}")
            return False

    def add_to_favorites(self, channel: Channel) -> None:
        """
        Adds a channel to the favorites list if it is not already present.

        Args:
            channel (Channel): The channel name to add to favorites.
        """
        channel_index = self.is_in_favorites(channel.name)
        if channel_index == -1:
            self.favorites.append(channel)
            logger.info(f"Channel '{channel}' added to favorites.")
        else:
            logger.warning(f"Attempted to add channel '{channel}' to favorites, but it is already present.")

    def remove_from_favorites(self, channel: str) -> None:
        """
        Removes a channel from the favorites list if it exists.

        Args:
            channel (str): The channel name to remove from favorites.
        """
        channel_index = self.is_in_favorites(channel.name)
        if channel_index > -1:
            self.favorites.pop(channel_index)
            logger.info(f"Channel '{channel}' removed from favorites.")
        else:
            logger.warning(f"Attempted to remove channel '{channel}' from favorites, but it was not found.")


    def remove_from_history(self, channel: str) -> None:
        """
        Removes a channel from the history list if it exists.

        Args:
            channel (str): The channel name to remove from history.
        """
        channel_index = self.is_in_history(channel.name)
        if channel_index > -1:
            self.history.pop(channel_index)
            logger.info(f"Channel '{channel}' removed from history.")
        else:
            logger.warning(f"Attempted to remove channel '{channel}' from history, but it was not found.")


    def is_in_favorites(self, name: str) -> int:
        """
        Checks if a channel is in the favorites list and returns its index.

        Args:
            name (str): The channel name to check.

        Returns:
            int: The index of the channel in favorites if found, -1 otherwise.
        """
        for i, channel in enumerate(self.favorites):
            if channel.name.lower() == name.lower():
                return i
        return -1

    def is_in_history(self, name: str) -> int:
        """
        Checks if a channel is in the history list and returns its index.

        Args:
            name (str): The channel name to check.

        Returns:
            int: The index of the channel in history if found, -1 otherwise.
        """
        for i, channel in enumerate(self.history):
            if channel.name.lower() == name.lower():
                return i
        return -1

    def clear_history(self) -> None:
        """
        Clears the entire history list.
        """
        self.history.clear()
        logger.info(f"Cleared history for profile '{self.name}'.")

    def clear_favorites(self) -> None:
        """
        Clears the entire favorites list.
        """
        self.favorites.clear()
        logger.info(f"Cleared favorites for profile '{self.name}'.")

    def validate_url(self) -> bool:
        """
        Validates the profile's URL by checking if it's a properly formatted URL and reachable.

        Returns:
            bool: True if valid, False otherwise.
        """
        if not self._is_valid_url(self.url):
            logger.error(f"Invalid profile URL format: {self.url}")
            return False
        try:
            response = requests.head(self.url, timeout=5)
            is_valid = response.status_code == 200
            if is_valid:
                logger.debug(f"Profile URL is reachable: {self.url}")
            else:
                logger.error(f"Profile URL returned status code {response.status_code}: {self.url}")
            return is_valid
        except requests.RequestException as e:
            logger.error(f"Error validating profile URL '{self.url}': {e}")
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
            r'(?:\S+)$'  # Non-whitespace characters till end
        )
        is_valid = re.match(regex, url) is not None
        logger.debug(f"URL '{url}' validation result: {is_valid}")
        return is_valid

    def update_favorites(self, data_loader: DataLoader):
        updated_favorites = []
        for channel in self.favorites:
            updated_channel = data_loader.get_channel_by_name(channel.name)
            if updated_channel:
                updated_favorites.append(updated_channel)
                if updated_channel != channel:
                    logger.info(f"channel updated '{channel.name}' in the data.")
            else:
                logger.info(f"Couldnt find '{channel.name}' in the Favorites.")
        self.favorites = updated_favorites

    def update_history(self, data_loader: DataLoader):
        updated_history = []
        for channel in self.history:
            updated_channel = data_loader.get_channel_by_name(channel.name)
            if updated_channel:
                updated_history.append(updated_channel)
                if updated_channel != channel:
                    logger.info(f"channel updated '{channel.name}' in the history.")
            else:
                logger.info(f"Couldnt find '{channel.name}' in the data.")
        self.history = updated_history

    def list_channels_in_favorites(self) -> List[str]:
        """
        Lists all channel names within a specified group. If no group is specified,
        lists channels from the selected group.

        Args:
        Returns:
            List[str]: A list of channel names.
        """
        try:
            channel_names = [channel.name for channel in self.favorites]
            # logger.debug(f"Channels in group '{group.name}': {channel_names}")
            return channel_names
        except Exception as e:
            logger.error(e)
            return []

    def list_channels_in_history(self) -> List[str]:
        """
        Lists all channel names within a specified group. If no group is specified,
        lists channels from the selected group.

        Args:
        Returns:
            List[str]: A list of channel names.
        """
        try:
            channel_names = [channel.name for channel in self.history]
            # logger.debug(f"Channels in group '{group.name}': {channel_names}")
            return channel_names
        except Exception as e:
            logger.error(e)
            return []

    def __eq__(self, other: Any) -> bool:
        """
        Checks equality based on the profile's name and URL.

        Args:
            other (Any): The other object to compare.

        Returns:
            bool: True if equal, False otherwise.
        """
        if not isinstance(other, Profile):
            return False
        is_equal = self.name == other.name and self.url == other.url
        logger.debug(f"Comparing profiles '{self.name}' and '{other.name}': {'equal' if is_equal else 'not equal'}.")
        return is_equal

    def __hash__(self) -> int:
        """
        Returns a hash based on the profile's name and URL.

        Returns:
            int: The hash value.
        """
        return hash((self.name, self.url))

    def is_within_24_hours(self) -> bool:
        """
        Checks if the given last_loaded timestamp is within the last 24 hours.

        Args:
            last_loaded_str (str): The last_loaded timestamp in ISO format.

        Returns:
            bool: True if the timestamp is within the last 24 hours, False otherwise.
        """
        try:
            if self.last_loaded is None:
                return False
            last_loaded_dt = datetime.fromtimestamp(self.last_loaded)
            now = datetime.now()
            return now - last_loaded_dt <= timedelta(days=1)
        except ValueError:
            # Invalid ISO format
            return False


def create_mock_profile():
    # Creating channels for the mock profile
    channel1 = Channel(name="Big Buck Bunny",
                       stream_url="http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4")
    channel2 = Channel(name="Tears of Steel",
                       stream_url="http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/TearsOfSteel.mp4")
    channel3 = Channel(name="Elephants Dream",
                       stream_url="http://commondatastorage.googleapis.com/gtv-videos-bucket/sample/ElephantsDream.mp4")

    # Adding channels to favorites (as URLs)
    favorites = [
        channel1,
        channel2,
        channel3
    ]

    # Creating the mock profile
    mock_profile = Profile(name="Test Profile", url="https://iptv-org.github.io/iptv/countries/il.m3u", favorites=favorites)

    return mock_profile

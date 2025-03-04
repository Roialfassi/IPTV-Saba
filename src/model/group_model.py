from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import logging

from .channel_model import Channel

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


@dataclass
class Group:
    """
    Represents a group of TV channels that share a common characteristic.

    Attributes:
        name (str): The name of the group.
        channels (List[Channel]): A list of channels belonging to the group.
    """
    name: str
    channels: List[Channel] = field(default_factory=list)

    def __str__(self) -> str:
        """
        Returns a string representation of the Group.

        Returns:
            str: The group's name and the number of channels it contains.
        """
        return f"{self.name} ({len(self.channels)} channels)"

    def to_dict(self) -> Dict[str, Any]:
        """
        Serializes the Group instance to a dictionary.

        Returns:
            Dict[str, Any]: The serialized group data.
        """
        return {
            "name": self.name,
            "channels": [channel.to_dict() for channel in self.channels]
        }

    @classmethod
    def create_group(cls, name: str, channel_list: List[Channel]) -> 'Group':
        """
        Creates a new Group with the given name and a list of channels.

        Args:
            name (str): The name of the group.
            channel_list (List[Channel]): A list of Channel objects to be added to the group.

        Returns:
            Group: A new Group instance with the specified name and channels.
        """
        return cls(name=name, channels=channel_list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Group':
        """
        Creates a Group instance from a dictionary.

        Args:
            data (Dict[str, Any]): The data to create the Group from.

        Returns:
            Group: The created Group instance.
        """
        channels_data = data.get("channels", [])
        channels = [Channel.from_dict(channel) for channel in channels_data]
        return cls(
            name=data.get("name", ""),
            channels=channels
        )

    def add_channel(self, channel: Channel) -> None:
        """
        Adds a channel to the group if it's not already present.

        Args:
            channel (Channel): The channel to add.
        """
        if channel in self.channels:
            logger.warning(f"Channel '{channel.name}' already exists in group '{self.name}'.")
        else:
            self.channels.append(channel)
            # logger.debug(f"Added channel '{channel.name}' to group '{self.name}'.")

    def remove_channel(self, channel: Channel) -> None:
        """
        Removes a channel from the group if it exists.

        Args:
            channel (Channel): The channel to remove.

        Raises:
            ValueError: If the channel is not found in the group.
        """
        try:
            self.channels.remove(channel)
            logger.debug(f"Removed channel '{channel.name}' from group '{self.name}'.")
        except ValueError:
            logger.error(f"Channel '{channel.name}' not found in group '{self.name}'.")
            raise ValueError(f"Channel '{channel.name}' not found in group '{self.name}'.")

    def find_channel_by_name(self, name: str) -> Optional[Channel]:
        """
        Finds a channel in the group by its name.

        Args:
            name (str): The name of the channel to find.

        Returns:
            Optional[Channel]: The found channel or None if not found.
        """
        for channel in self.channels:
            if channel.name.lower() == name.lower():
                logger.debug(f"Found channel '{name}' in group '{self.name}'.")
                return channel
        logger.debug(f"Channel '{name}' not found in group '{self.name}'.")
        return None

    def find_channels_by_tvg_id(self, tvg_id: str) -> List[Channel]:
        """
        Finds all channels in the group with a specific TVG ID.

        Args:
            tvg_id (str): The TVG ID to search for.

        Returns:
            List[Channel]: A list of channels matching the TVG ID.
        """
        matched_channels = [channel for channel in self.channels if channel.tvg_id == tvg_id]
        logger.debug(f"Found {len(matched_channels)} channel(s) with TVG ID '{tvg_id}' in group '{self.name}'.")
        return matched_channels

    def update_group_name(self, new_name: str) -> None:
        """
        Updates the name of the group.

        Args:
            new_name (str): The new name for the group.
        """
        logger.debug(f"Updating group name from '{self.name}' to '{new_name}'.")
        self.name = new_name

    def update_channel(self, old_channel: Channel, new_channel: Channel) -> None:
        """
        Updates an existing channel in the group.

        Args:
            old_channel (Channel): The channel to be updated.
            new_channel (Channel): The new channel data.

        Raises:
            ValueError: If the old channel is not found in the group.
        """
        try:
            index = self.channels.index(old_channel)
            self.channels[index] = new_channel
            logger.debug(f"Updated channel '{old_channel.name}' to '{new_channel.name}' in group '{self.name}'.")
        except ValueError:
            logger.error(f"Channel '{old_channel.name}' not found in group '{self.name}'.")
            raise ValueError(f"Channel '{old_channel.name}' not found in group '{self.name}'.")

    def list_channels(self) -> List[str]:
        """
        Lists the names of all channels in the group.

        Returns:
            List[str]: A list of channel names.
        """
        channel_names = [channel.name for channel in self.channels]
        logger.debug(f"Listing channels in group '{self.name}': {channel_names}")
        return channel_names

    def clear_channels(self) -> None:
        """
        Removes all channels from the group.
        """
        self.channels.clear()
        logger.debug(f"Cleared all channels from group '{self.name}'.")

    def validate_channels(self) -> bool:
        """
        Validates all channels in the group.

        Returns:
            bool: True if all channels are valid, False otherwise.
        """
        all_valid = True
        for channel in self.channels:
            if not channel.validate_stream_url():
                logger.error(f"Invalid stream URL for channel '{channel.name}'.")
                all_valid = False
            if not channel.validate_tvg_logo():
                logger.error(f"Invalid TVG logo URL for channel '{channel.name}'.")
                all_valid = False
        return all_valid

    def __eq__(self, other: Any) -> bool:
        """
        Checks equality based on the group's name and channels.

        Args:
            other (Any): The other object to compare.

        Returns:
            bool: True if equal, False otherwise.
        """
        if not isinstance(other, Group):
            return False
        return self.name == other.name and set(self.channels) == set(other.channels)

    def __hash__(self) -> int:
        """
        Returns a hash based on the group's name.

        Returns:
            int: The hash value.
        """
        return hash(self.name)

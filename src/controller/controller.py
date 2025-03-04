import logging
from typing import List, Dict, Optional, Tuple
import os
from PyQt5.QtCore import QObject, pyqtSlot, pyqtSignal

from src.data.data_loader import DataLoader
from src.data.profile_manager import ProfileManager
from src.model.channel_model import Channel
from src.model.group_model import Group
from src.model.profile import Profile
from src.data.config_manager import ConfigManager

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Controller(QObject):
    profiles_updated = pyqtSignal()  # login
    error_occurred = pyqtSignal(str)
    profile_selected = pyqtSignal(str)  # login
    data_loaded = pyqtSignal(dict)

    def __init__(self, profiles_file: str = "profiles.json", folder_name: str = 'IPTV-Saba'):
        super().__init__()
        ## Paths
        self.config_dir = os.path.join(os.getcwd(), folder_name)
        self.config_manager = ConfigManager(self.config_dir)
        self.profile_path = os.path.join(self.config_dir, profiles_file)  # path to profile

        self.profile_manager = ProfileManager(self.config_dir, profiles_file)  # login
        self.data_loader = DataLoader()  # login
        self.active_profile: Optional[Profile] = None  # if logged in
        self.selected_group: Optional[Group] = None
        self.active_window = None
        self.last_window = None
        logger.info("Controller initialized.")

    def login_logic(self):
        try:
            should_auto_login, profile_id = self.config_manager.should_auto_login()
            if should_auto_login:
                profile = self.profile_manager.get_profile(profile_id)
                if profile:
                    self.active_profile = profile
                    return True
            else:
                return False
        except Exception as e:
            logger.error(f"Auto Login Error: {e}")
            return False

    # --------------------------- Profile Management ---------------------------

    @pyqtSlot()
    def list_profiles(self) -> List[str]:
        """
        Lists all available profile names.

        Returns:
            List[str]: A list of profile names.
        """
        profiles = self.profile_manager.list_profiles()
        logger.debug(f"Available profiles: {profiles}")
        return profiles

    @pyqtSlot(str)
    def select_profile(self, name: str) -> None:
        """
        Selects an active profile by name and emits the profile_selected signal.

        Args:
            name (str): The name of the profile to select.
        """
        profile = self.profile_manager.get_profile(name)

        if profile:
            self.active_profile = profile
            logger.info(f"Profile '{profile.name}' selected.")
            self.profile_selected.emit(name)  # Emit signal with profile name
        else:
            logger.warning(f"Profile '{name}' not found.")
            self.error_occurred.emit(f"Profile '{name}' not found.")  # Emit error signal

    @pyqtSlot(str, str, list)
    def create_profile(self, name: str, url: str) -> None:
        """
        Creates a new profile.

        Args:
            name (str): The name of the new profile.
            url (str): The URL associated with the new profile.
        """
        try:
            self.profile_manager.create_profile(name, url)
            logger.info(f"Profile '{name}' created.")
            self.profiles_updated.emit()  # Emit signal to update profile list
        except ValueError as ve:
            logger.error(f"Failed to create profile '{name}': {ve}")
            self.error_occurred.emit(str(ve))  # Emit error signal

    @pyqtSlot(str, str, list)
    def delete_profile(self, name: str, url: str) -> None:
        """
        Creates a new profile.

        Args:
            name (str): The name of the new profile.
            url (str): The URL associated with the new profile.
        """
        try:
            self.profile_manager.delete_profile(name, url)
            logger.info(f"Profile '{name}' deleted.")
            self.profiles_updated.emit()  # Emit signal to update profile list
        except ValueError as ve:
            logger.error(f"Failed to delete profile '{name}': {ve}")
            self.error_occurred.emit(str(ve))  # Emit error signal

    # --------------------------- Group Management ---------------------------

    @pyqtSlot()
    def list_groups(self) -> List[str]:
        """
        Lists all group names from the loaded IPTV data.

        Returns:
            List[str]: A list of group names.
        """
        group_names = list(self.data_loader.groups.keys())
        logger.debug(f"Available groups: {group_names}")
        return group_names

    @pyqtSlot(str)
    def select_group(self, group_name: str) -> None:
        """
        Selects a group by name.

        Args:
            group_name (str): The name of the group to select.
        """
        group = self.data_loader.get(group_name)
        if group:
            self.selected_group = group
            logger.info(f"Group '{group_name}' selected.")
            self.channels_updated.emit([channel.name for channel in group.channels])
        else:
            logger.warning(f"Group '{group_name}' not found.")
            self.error_occurred.emit(f"Group '{group_name}' not found.")

    @pyqtSlot(str)
    def list_channels_in_group(self, group_name: Optional[str] = None) -> List[str]:
        """
        Lists all channel names within a specified group. If no group is specified,
        lists channels from the selected group.

        Args:
            group_name (Optional[str]): The name of the group. Defaults to None.

        Returns:
            List[str]: A list of channel names.
        """
        if group_name:
            group = self.data_loader.groups.get(group_name)
            if not group:
                logger.warning(f"Group '{group_name}' not found.")
                self.error_occurred.emit(f"Group '{group_name}' not found.")
                return []
        else:
            group = self.selected_group
            if not group:
                logger.warning("No group selected.")
                self.error_occurred.emit("No group selected.")
                return []

        channel_names = [channel.name for channel in group.channels]
        # logger.debug(f"Channels in group '{group.name}': {channel_names}")
        return channel_names

    @pyqtSlot(str)
    def search_channels(self, query: str) -> List[Channel]:
        """
        Searches for channels across all groups that match the query in their name.

        Args:
            query (str): The search query.

        Returns:
            List[Channel]: A list of matching channels.
        """
        matched_channels = []
        for group in self.data_loader.groups.values():
            for channel in group.channels:
                if query.lower() in channel.name.lower():
                    matched_channels.append(channel)
        logger.debug(f"Found {len(matched_channels)} channel(s) matching query '{query}'.")
        return matched_channels

    def find_channel_by_name(self, channel_name: str) -> Optional[Channel]:
        """
        Finds a channel object by its name.

        Args:
            channel_name (str): The name of the channel to find.

        Returns:
            Optional[Channel]: The channel object if found, else None.
        """
        for group in self.data_loader.groups.values():
            for channel in group.channels:
                if channel.name.lower() == channel_name.lower():
                    logger.debug(f"Channel '{channel_name}' found in group '{group.name}'.")
                    return channel
        logger.debug(f"Channel '{channel_name}' not found in any group.")
        return None

    def add_to_history(self, channel: Channel) -> None:
        """
        adds channel to history
        :param channel:  channel
        :return:
        """
        channel = self.find_channel_by_name(channel.name)
        if not channel:
            logger.debug(f"Channel '{channel.name}' not found in any group.")
            return
        self.active_profile.add_to_history(channel)
        self.profile_manager.update_profile(self.active_profile)
        self.profile_manager.export_profiles(self.profile_path)

    def add_to_favorites(self, channel_name: str) -> None:
        """
        adds channel to favorites
        :param channel_name: name of channel
        :return:
        """
        channel = self.find_channel_by_name(channel_name)
        if not channel:
            logger.debug(f"Channel '{channel_name}' not found in any group.")
            return
        self.active_profile.add_to_favorites(channel)
        self.profile_manager.update_profile(self.active_profile)
        self.profile_manager.export_profiles(self.profile_path)

    def remove_from_favorites(self, channel_name: str) -> None:
        """
        adds channel to favorites
        :param channel_name: name of channel
        :return:
        """
        channel = self.find_channel_by_name(channel_name)
        if not channel:
            logger.debug(f"Channel '{channel_name}' not found in any group.")
            return
        self.active_profile.remove_from_favorites(channel)
        self.profile_manager.update_profile(self.active_profile)
        self.profile_manager.export_profiles(self.profile_path)



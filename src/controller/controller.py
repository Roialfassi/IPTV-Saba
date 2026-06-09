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

logger = logging.getLogger(__name__)


class Controller(QObject):
    profiles_updated = pyqtSignal()  # login
    error_occurred = pyqtSignal(str)
    profile_selected = pyqtSignal(str)  # login
    data_loaded = pyqtSignal(dict)
    channels_updated = pyqtSignal(list)  # emitted by select_group with channel names

    def __init__(self, profiles_file: str = "profiles.json", folder_name: str = 'IPTV-Saba'):
        super().__init__()
        ## Paths
        self.config_dir = os.path.join(os.getcwd(), folder_name)
        self.config_manager = ConfigManager(self.config_dir)
        self.profile_path = os.path.join(self.config_dir, profiles_file)  # path to profile

        self.profile_manager = ProfileManager(self.config_dir, profiles_file)  # login
        cache_dir = os.path.join(self.config_dir, 'cache')
        self.data_loader = DataLoader(cache_dir=cache_dir)  # login
        self.active_profile: Optional[Profile] = None  # if logged in
        self.selected_group: Optional[Group] = None
        self.active_window = None
        self.last_window = None
        self._channel_names_cache: Dict[str, List[str]] = {}
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

    @pyqtSlot(str, str, str)
    def edit_profile(self, old_name: str, new_name: str, new_url: str) -> None:
        """
        Edit an existing profile's name and/or URL.

        Keeps the active profile and the saved auto-login id in sync when the
        edited profile is the current/last-used one, then notifies the UI.

        Args:
            old_name (str): Current name of the profile to edit.
            new_name (str): New name for the profile.
            new_url (str): New playlist URL for the profile.
        """
        try:
            if not self.profile_manager.edit_profile(old_name, new_name, new_url):
                self.error_occurred.emit(
                    f"Could not edit profile '{old_name}'. The name may be taken or the URL invalid."
                )
                return

            # Keep references to the renamed profile consistent.
            if self.active_profile and self.active_profile.name == old_name:
                self.active_profile = self.profile_manager.get_profile(new_name)
            if self.config_manager.get_value("last_active_profile_id") == old_name:
                self.config_manager.set_value("last_active_profile_id", new_name)

            logger.info(f"Profile '{old_name}' edited (now '{new_name}').")
            self.profiles_updated.emit()
        except Exception as e:
            logger.error(f"Failed to edit profile '{old_name}': {e}")
            self.error_occurred.emit(str(e))

    @pyqtSlot(str)
    def delete_profile(self, name: str) -> None:
        """
        Deletes an existing profile.

        Args:
            name (str): The name of the profile to delete.
        """
        try:
            self.profile_manager.delete_profile(name)
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
        Special groups (All Channels, All VODs, etc.) are pinned to the top.

        Returns:
            List[str]: A list of group names.
        """
        from src.data.data_loader import DataLoader
        all_names = list(self.data_loader.groups.keys())
        special = [n for n in all_names if n in DataLoader.SPECIAL_GROUP_NAMES]
        regular = [n for n in all_names if n not in DataLoader.SPECIAL_GROUP_NAMES]
        group_names = special + regular
        logger.debug(f"Available groups: {len(group_names)} ({len(special)} special)")
        return group_names

    @pyqtSlot(str)
    def select_group(self, group_name: str) -> None:
        """
        Selects a group by name.

        Args:
            group_name (str): The name of the group to select.
        """
        group = self.data_loader.get_group(group_name)
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

        cache_key = group.name
        if cache_key not in self._channel_names_cache:
            self._channel_names_cache[cache_key] = [channel.name for channel in group.channels]
        return self._channel_names_cache[cache_key]

    @pyqtSlot(str)
    def search_channels(self, query: str) -> List[Channel]:
        """
        Searches for channels across all groups that match the query in their name.

        Args:
            query (str): The search query.

        Returns:
            List[Channel]: A list of matching channels.
        """
        query_lower = query.lower()
        matched_channels = [ch for ch in self.data_loader.channels if query_lower in ch.name.lower()]
        logger.debug(f"Found {len(matched_channels)} channel(s) matching query '{query}'.")
        return matched_channels

    def find_channel_by_name(self, channel_name: str) -> Optional[Channel]:
        """
        Finds a channel object by its name.
        Delegates to DataLoader's indexed O(1) lookup.

        Args:
            channel_name (str): The name of the channel to find.

        Returns:
            Optional[Channel]: The channel object if found, else None.
        """
        return self.data_loader.get_channel_by_name(channel_name)

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
        # update_profile() already persists profiles.json atomically.
        self.profile_manager.update_profile(self.active_profile)

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
        # update_profile() already persists profiles.json atomically.
        self.profile_manager.update_profile(self.active_profile)

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
        # update_profile() already persists profiles.json atomically.
        self.profile_manager.update_profile(self.active_profile)



"""
Android-compatible Controller wrapper for IPTV-Saba
Wraps the original Controller and makes it work with Kivy
"""

import logging
import os
from typing import List, Optional
from pathlib import Path

from kivy.event import EventDispatcher
from kivy.utils import platform

from src.data.data_loader import DataLoader
from src.data.profile_manager import ProfileManager
from src.data.config_manager import ConfigManager
from src.model.channel_model import Channel
from src.model.group_model import Group
from src.model.profile import Profile

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class AndroidController(EventDispatcher):
    """
    Android-compatible controller for IPTV-Saba app.
    Similar to the original Controller but uses Kivy events instead of PyQt signals.
    """

    def __init__(self, profiles_file: str = "profiles.json", folder_name: str = 'IPTV-Saba', **kwargs):
        super().__init__(**kwargs)

        # Register events (Kivy equivalent of PyQt signals)
        self.register_event_type('on_profiles_updated')
        self.register_event_type('on_error_occurred')
        self.register_event_type('on_profile_selected')
        self.register_event_type('on_data_loaded')

        # Determine storage path based on platform
        if platform == 'android':
            try:
                from android.storage import primary_external_storage_path
                storage_path = primary_external_storage_path()
                self.config_dir = os.path.join(storage_path, folder_name)
            except Exception as e:
                logger.error(f"Failed to get Android storage path: {e}")
                self.config_dir = os.path.join('/sdcard', folder_name)
        else:
            # Desktop testing
            self.config_dir = os.path.join(str(Path.home()), '.' + folder_name)

        # Create directory if it doesn't exist
        os.makedirs(self.config_dir, exist_ok=True)

        # Initialize managers
        self.config_manager = ConfigManager(self.config_dir)
        self.profile_path = os.path.join(self.config_dir, profiles_file)
        self.profile_manager = ProfileManager(self.config_dir, profiles_file)
        self.data_loader = DataLoader()

        # State
        self.active_profile: Optional[Profile] = None
        self.selected_group: Optional[Group] = None

        logger.info(f"AndroidController initialized. Storage: {self.config_dir}")

    # Event handlers (required for registered events)
    def on_profiles_updated(self):
        pass

    def on_error_occurred(self, error_msg):
        pass

    def on_profile_selected(self, profile_name):
        pass

    def on_data_loaded(self, data):
        pass

    def login_logic(self):
        """
        Check if auto-login should occur.
        Returns True if a profile was auto-loaded.
        """
        try:
            auto_login_enabled = self.config_manager.get('auto_login_enabled', False)
            if auto_login_enabled:
                profile_id = self.config_manager.get('last_active_profile_id')
                if profile_id:
                    profile = self.profile_manager.get_profile(profile_id)
                    if profile:
                        self.active_profile = profile
                        return True
            return False
        except Exception as e:
            logger.error(f"Auto Login Error: {e}")
            return False

    # --------------------------- Profile Management ---------------------------

    def list_profiles(self) -> List[Profile]:
        """
        Lists all available profiles.
        Returns:
            List[Profile]: A list of Profile objects.
        """
        try:
            profiles = self.profile_manager.list_profiles()
            return profiles
        except Exception as e:
            logger.error(f"Error listing profiles: {e}")
            return []

    def select_profile(self, profile_name: str) -> bool:
        """
        Select a profile by name.
        Args:
            profile_name: Name of the profile to select
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            profile = self.profile_manager.get_profile(profile_name)
            if profile:
                self.active_profile = profile
                self.dispatch('on_profile_selected', profile_name)
                logger.info(f"Profile selected: {profile_name}")
                return True
            else:
                logger.error(f"Profile not found: {profile_name}")
                return False
        except Exception as e:
            logger.error(f"Error selecting profile: {e}")
            self.dispatch('on_error_occurred', str(e))
            return False

    def create_profile(self, name: str, url: str) -> bool:
        """
        Create a new profile.
        Args:
            name: Profile name
            url: M3U playlist URL
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Check if profile already exists
            existing = self.profile_manager.get_profile(name)
            if existing:
                logger.error(f"Profile already exists: {name}")
                return False

            # Create new profile
            new_profile = Profile(name=name, url=url)
            success = self.profile_manager.add_profile(new_profile)

            if success:
                self.dispatch('on_profiles_updated')
                logger.info(f"Profile created: {name}")
                return True
            else:
                logger.error(f"Failed to create profile: {name}")
                return False

        except Exception as e:
            logger.error(f"Error creating profile: {e}")
            self.dispatch('on_error_occurred', str(e))
            return False

    def delete_profile(self, profile_name: str) -> bool:
        """
        Delete a profile.
        Args:
            profile_name: Name of the profile to delete
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            success = self.profile_manager.delete_profile(profile_name)
            if success:
                # Clear active profile if it was deleted
                if self.active_profile and self.active_profile.name == profile_name:
                    self.active_profile = None

                self.dispatch('on_profiles_updated')
                logger.info(f"Profile deleted: {profile_name}")
                return True
            else:
                logger.error(f"Failed to delete profile: {profile_name}")
                return False

        except Exception as e:
            logger.error(f"Error deleting profile: {e}")
            self.dispatch('on_error_occurred', str(e))
            return False

    def update_profile(self, profile: Profile) -> bool:
        """
        Update an existing profile.
        Args:
            profile: Profile object with updated data
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            success = self.profile_manager.update_profile(profile)
            if success:
                # Update active profile if it's the one being updated
                if self.active_profile and self.active_profile.name == profile.name:
                    self.active_profile = profile

                logger.info(f"Profile updated: {profile.name}")
                return True
            else:
                logger.error(f"Failed to update profile: {profile.name}")
                return False

        except Exception as e:
            logger.error(f"Error updating profile: {e}")
            self.dispatch('on_error_occurred', str(e))
            return False

    # --------------------------- Data Management ---------------------------

    def get_groups(self) -> List[Group]:
        """Get all channel groups from data loader"""
        return self.data_loader.get_groups()

    def get_channels(self, group_name: Optional[str] = None) -> List[Channel]:
        """
        Get channels, optionally filtered by group.
        Args:
            group_name: Optional group name to filter by
        Returns:
            List of Channel objects
        """
        groups = self.data_loader.get_groups()
        if group_name:
            for group in groups:
                if group.name == group_name:
                    return group.channels
            return []
        else:
            # Return all channels from all groups
            all_channels = []
            for group in groups:
                all_channels.extend(group.channels)
            return all_channels

    # --------------------------- Utility Methods ---------------------------

    def save_state(self):
        """Save current state (called on app pause)"""
        try:
            if self.active_profile:
                self.profile_manager.update_profile(self.active_profile)
            self.config_manager.save()
            logger.info("State saved")
        except Exception as e:
            logger.error(f"Error saving state: {e}")

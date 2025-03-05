import os
import json
import logging
from pathlib import Path


class ConfigManager:
    """
    auto-login settings, and theme preferences.
    """
    DEFAULT_CONFIG = {
        "last_active_profile_id": None,
        "auto_login_enabled": False,
        "theme": "default",
        "app_version": "1.0.0",
        "first_run": True,
        "log_level": "INFO"
    }

    def __init__(self, config_dir=None, config_filename="config.json"):
        """
        Initialize the ConfigManager.

        Args:
            config_dir (str, optional): Directory to store config file.
                                        Defaults to user's home directory.
            config_filename (str, optional): Name of config file. Defaults to "config.json".
        """
        # Set up logging
        self.logger = logging.getLogger(__name__)

        # Set config file path
        if config_dir is None:
            # Default to user's home directory
            self.config_dir = os.path.join(Path.home(), '.myapp')
        else:
            self.config_dir = config_dir

        self.config_path = os.path.join(self.config_dir, config_filename)

        # Ensure config directory exists
        os.makedirs(self.config_dir, exist_ok=True)

        # Load or create configuration
        self.config = self._load_config()

    def _load_config(self):
        """
        Load config from file or create default if file doesn't exist.

        Returns:
            dict: The configuration dictionary.
        """
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r') as f:
                    config = json.load(f)
                    # Ensure all default keys exist in case config file is old
                    for key, value in self.DEFAULT_CONFIG.items():
                        if key not in config:
                            config[key] = value
                    self.logger.info(f"Loaded configuration from {self.config_path}")
                    return config
            else:
                self.logger.info(f"Config file not found. Creating default configuration.")
                return self._create_default_config()
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            return self._create_default_config()

    def _create_default_config(self):
        """
        Create and save default configuration.

        Returns:
            dict: The default configuration dictionary.
        """
        config = self.DEFAULT_CONFIG.copy()
        self._save_config(config)
        return config

    def _save_config(self, config=None):
        """
        Save configuration to file.

        Args:
            config (dict, optional): Config to save. Defaults to current config.
        """
        if config is None:
            config = self.config

        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=4)
            self.logger.info(f"Configuration saved to {self.config_path}")
        except Exception as e:
            self.logger.error(f"Error saving config: {e}")

    def save(self):
        """
        Save current configuration to file.
        """
        self._save_config()

    # Getters and setters for specific configuration options

    @property
    def last_active_profile_id(self):
        """Get the ID of the last active profile."""
        return self.config.get("last_active_profile_id")

    @last_active_profile_id.setter
    def last_active_profile_id(self, profile_id):
        """Set the ID of the last active profile."""
        self.config["last_active_profile_id"] = profile_id
        self.save()

    @property
    def auto_login_enabled(self):
        """Check if auto-login is enabled."""
        return self.config.get("auto_login_enabled", False)

    @auto_login_enabled.setter
    def auto_login_enabled(self, enabled):
        """Enable or disable auto-login."""
        self.config["auto_login_enabled"] = bool(enabled)
        self.save()

    @property
    def theme(self):
        """Get the current theme."""
        return self.config.get("theme", "default")

    @theme.setter
    def theme(self, theme_name):
        """Set the theme."""
        self.config["theme"] = theme_name
        self.save()

    def should_auto_login(self):
        """
        Check if auto-login should be performed.

        Returns:
            tuple: (bool, str) - Whether to auto-login and profile ID to use.
        """
        if self.auto_login_enabled and self.last_active_profile_id:
            return True, self.last_active_profile_id
        return False, None

    # Additional utility methods

    def reset_to_defaults(self):
        """Reset configuration to default values."""
        self.config = self.DEFAULT_CONFIG.copy()
        self.save()

    def get_value(self, key, default=None):
        """
        Get a configuration value by key.

        Args:
            key (str): The configuration key.
            default: Default value if key not found.

        Returns:
            The configuration value or default.
        """
        return self.config.get(key, default)

    def set_value(self, key, value):
        """
        Set a configuration value.

        Args:
            key (str): The configuration key.
            value: The value to set.
        """
        self.config[key] = value
        self.save()

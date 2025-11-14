"""Application configuration and settings management."""
import json
from pathlib import Path
from typing import Any, Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class AppSettings:
    """Application settings."""
    theme: str = "dark"
    auto_login: bool = False
    last_profile: str = ""
    remember_volume: bool = True
    last_volume: int = 80
    download_directory: str = ""
    concurrent_downloads: int = 3
    auto_hide_overlay_ms: int = 3000
    window_width: int = 1280
    window_height: int = 720
    window_maximized: bool = False


class Config:
    """Global configuration manager."""

    _config_dir: Path = None
    _settings: AppSettings = None
    _profiles: Dict[str, Any] = {}

    @classmethod
    def initialize(cls, config_dir: Optional[Path] = None):
        """Initialize configuration system."""
        if config_dir is None:
            config_dir = Path.home() / ".iptv-saba"

        cls._config_dir = config_dir
        cls._config_dir.mkdir(parents=True, exist_ok=True)

        cls._load_settings()
        cls._load_profiles()

    @classmethod
    def get_config_dir(cls) -> Path:
        """Get configuration directory."""
        return cls._config_dir

    @classmethod
    def get_downloads_dir(cls) -> Path:
        """Get downloads directory."""
        if cls._settings.download_directory:
            return Path(cls._settings.download_directory)
        return cls._config_dir / "downloads"

    @classmethod
    def get_cache_dir(cls) -> Path:
        """Get cache directory."""
        cache_dir = cls._config_dir / "cache"
        cache_dir.mkdir(exist_ok=True)
        return cache_dir

    @classmethod
    def get_settings(cls) -> AppSettings:
        """Get application settings."""
        return cls._settings

    @classmethod
    def update_settings(cls, **kwargs):
        """Update settings."""
        for key, value in kwargs.items():
            if hasattr(cls._settings, key):
                setattr(cls._settings, key, value)
        cls._save_settings()

    @classmethod
    def get_profiles(cls) -> Dict[str, Any]:
        """Get all profiles."""
        return cls._profiles.copy()

    @classmethod
    def add_profile(cls, name: str, url: str, username: str = "", password: str = ""):
        """Add new profile."""
        cls._profiles[name] = {
            "url": url,
            "username": username,
            "password": password,
            "created_at": datetime.now().isoformat(),
            "last_used": None,
            "favorites": [],
            "history": []
        }
        cls._save_profiles()

    @classmethod
    def update_profile(cls, name: str, **kwargs):
        """Update profile."""
        if name in cls._profiles:
            cls._profiles[name].update(kwargs)
            cls._save_profiles()

    @classmethod
    def delete_profile(cls, name: str):
        """Delete profile."""
        if name in cls._profiles:
            del cls._profiles[name]
            cls._save_profiles()

    @classmethod
    def get_profile(cls, name: str) -> Optional[Dict]:
        """Get specific profile."""
        return cls._profiles.get(name)

    @classmethod
    def _load_settings(cls):
        """Load settings from file."""
        settings_file = cls._config_dir / "settings.json"

        if settings_file.exists():
            try:
                with open(settings_file, 'r') as f:
                    data = json.load(f)
                cls._settings = AppSettings(**data)
                return
            except Exception:
                pass

        cls._settings = AppSettings()

    @classmethod
    def _save_settings(cls):
        """Save settings to file."""
        settings_file = cls._config_dir / "settings.json"
        with open(settings_file, 'w') as f:
            json.dump(asdict(cls._settings), f, indent=2)

    @classmethod
    def _load_profiles(cls):
        """Load profiles from file."""
        profiles_file = cls._config_dir / "profiles.json"

        if profiles_file.exists():
            try:
                with open(profiles_file, 'r') as f:
                    cls._profiles = json.load(f)
                return
            except Exception:
                pass

        cls._profiles = {}

    @classmethod
    def _save_profiles(cls):
        """Save profiles to file."""
        profiles_file = cls._config_dir / "profiles.json"
        with open(profiles_file, 'w') as f:
            json.dump(cls._profiles, f, indent=2)

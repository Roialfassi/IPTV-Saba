"""
Resource path helper for PyInstaller bundled applications.

When running as a bundled EXE, PyInstaller extracts files to a temp directory.
This module provides a helper to get the correct path to bundled resources.
"""
import sys
import os


def resource_path(relative_path: str) -> str:
    """
    Get the absolute path to a resource, works for dev and PyInstaller bundle.

    Args:
        relative_path: Path relative to the src directory (e.g., "Assets/icon.ico")

    Returns:
        Absolute path to the resource
    """
    if getattr(sys, 'frozen', False):
        # Running as bundled EXE - PyInstaller stores files in _MEIPASS
        base_path = sys._MEIPASS
    else:
        # Running in development - use the src directory
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    return os.path.join(base_path, relative_path)

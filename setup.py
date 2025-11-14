"""Setup script for building executable."""
from cx_Freeze import setup, Executable
import sys

build_exe_options = {
    "packages": ["PyQt5", "vlc", "requests", "pathlib", "json", "logging", "datetime"],
    "includes": [
        "PyQt5.QtCore",
        "PyQt5.QtGui",
        "PyQt5.QtWidgets",
        "app.core",
        "app.services",
        "app.ui.views",
        "app.ui.widgets",
        "app.ui.dialogs",
        "app.models"
    ],
    "include_files": [],
    "excludes": ["tkinter", "matplotlib", "numpy", "pandas"],
    "optimize": 2,
}

base = None
if sys.platform == "win32":
    base = "Win32GUI"

executables = [
    Executable(
        "app/main.py",
        base=base,
        target_name="IPTV-Saba",
        icon="assets/icon.ico" if sys.platform == "win32" else None
    )
]

setup(
    name="IPTV-Saba",
    version="2.0.0",
    description="IPTV Player with Download Support",
    author="Roi Alfassi",
    options={"build_exe": build_exe_options},
    executables=executables
)

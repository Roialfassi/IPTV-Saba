# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for IPTV-Saba

Build command: pyinstaller iptv_saba.spec

IMPORTANT: VLC Media Player must be installed on the target system!
The application requires VLC to be installed at: C:\Program Files\VideoLAN\VLC\
"""

import sys
from pathlib import Path

block_cipher = None

# Get the project root directory
PROJECT_ROOT = Path(SPECPATH)
SRC_DIR = PROJECT_ROOT / 'src'

# Collect all source files
a = Analysis(
    [str(SRC_DIR / 'iptv_app.py')],
    pathex=[str(PROJECT_ROOT), str(SRC_DIR)],
    binaries=[],
    datas=[
        # Include Assets folder
        (str(SRC_DIR / 'Assets'), 'Assets'),
    ],
    hiddenimports=[
        # PyQt5 imports
        'PyQt5',
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'PyQt5.sip',
        # VLC
        'vlc',
        # aiohttp and dependencies
        'aiohttp',
        'aiosignal',
        'async_timeout',
        'multidict',
        'yarl',
        'frozenlist',
        # Other dependencies
        'chardet',
        'requests',
        'certifi',
        'urllib3',
        'fuzzywuzzy',
        'Levenshtein',
        'rapidfuzz',
        # App modules
        'src.controller.controller',
        'src.model.profile',
        'src.model.channel_model',
        'src.model.group_model',
        'src.data.config_manager',
        'src.data.data_loader',
        'src.data.profile_manager',
        'src.services.shared_player_manager',
        'src.services.download_record_manager',
        'src.services.schedule_manager',
        'src.services.recording_scheduler',
        'src.services.hls_parser',
        'src.services.stream_health_tracker',
        'src.view.login_view',
        'src.view.choose_channel_screen',
        'src.view.full_screen_view',
        'src.view.easy_mode_screen',
        'src.view.retry_overlay',
        'src.view.schedule_dialog',
        'src.utils.resource_path',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude unnecessary modules to reduce size
        'tkinter',
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'cv2',
        'kivy',  # Exclude kivy if not used
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='IPTV-Saba',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to True if you want to see console output for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(SRC_DIR / 'Assets' / 'iptv-logo2.ico'),
    version='version_info.txt' if (PROJECT_ROOT / 'version_info.txt').exists() else None,
)

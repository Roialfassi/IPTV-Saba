# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build specification for IPTV Saba."""

block_cipher = None

a = Analysis(
    ['app/main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'vlc',
        'requests',
        'app.core.application',
        'app.core.config',
        'app.services.vlc_service',
        'app.services.playlist_service',
        'app.services.download_service',
        'app.ui.views.login_view',
        'app.ui.views.main_view',
        'app.ui.views.player_view',
        'app.ui.widgets.player_overlay',
        'app.ui.dialogs.downloads_dialog',
        'app.models.channel',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'pandas', 'scipy', 'tkinter'],
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
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

# IPTV Saba - Export Guide for Beginners

Complete step-by-step guide to package and distribute the IPTV Saba application as a standalone executable.

---

## Prerequisites

### Required Software

1. **Python 3.8+**
   - Download: https://www.python.org/downloads/
   - During installation: ✅ Check "Add Python to PATH"

2. **Git** (optional, for cloning)
   - Download: https://git-scm.com/downloads

3. **VLC Media Player**
   - Download: https://www.videolan.org/vlc/
   - Required for video playback

4. **FFmpeg** (for downloads)
   - Windows: https://www.gyan.dev/ffmpeg/builds/
   - Extract and add to PATH

---

## Step 1: Project Setup

### Option A: Clone from Git

```bash
git clone https://github.com/yourusername/IPTV-Saba.git
cd IPTV-Saba
```

### Option B: Manual Setup

1. Create project folder: `IPTV-Saba`
2. Copy all `app/` folder contents
3. Copy `requirements.txt`
4. Copy `setup.py`

---

## Step 2: Install Dependencies

### Open Command Prompt/Terminal in project directory

```bash
# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Install PyInstaller (for building executable)
pip install pyinstaller
```

---

## Step 3: Test the Application

Before building, verify the application works:

```bash
python -m app.main
```

Expected:
- Window opens showing login screen
- No errors in console

If errors occur:
- Check all dependencies installed
- Verify VLC installed
- Check Python version (3.8+)

---

## Step 4: Build Standalone Executable

### Method 1: PyInstaller (Recommended)

Create `build.spec` file:

```python
# build.spec
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['app/main.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('assets', 'assets'),
    ],
    hiddenimports=[
        'PyQt5.QtCore',
        'PyQt5.QtGui',
        'PyQt5.QtWidgets',
        'vlc',
        'requests',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    console=False,  # No console window
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/icon.ico'  # Optional: add icon
)
```

Build command:

```bash
# Single executable (larger file, ~100MB)
pyinstaller build.spec

# Or use simple command:
pyinstaller --onefile --windowed --name "IPTV-Saba" --icon=assets/icon.ico app/main.py
```

Output location: `dist/IPTV-Saba.exe` (Windows) or `dist/IPTV-Saba` (Linux/Mac)

---

### Method 2: cx_Freeze (Alternative)

Install:
```bash
pip install cx-freeze
```

Create `setup.py`:

```python
# setup.py
from cx_Freeze import setup, Executable
import sys

build_exe_options = {
    "packages": ["PyQt5", "vlc", "requests"],
    "includes": ["PyQt5.QtCore", "PyQt5.QtGui", "PyQt5.QtWidgets"],
    "include_files": [("assets/", "assets/")],
    "excludes": ["tkinter"],
}

base = None
if sys.platform == "win32":
    base = "Win32GUI"  # No console window

setup(
    name="IPTV-Saba",
    version="2.0.0",
    description="IPTV Player with Download Support",
    options={"build_exe": build_exe_options},
    executables=[Executable("app/main.py", base=base, icon="assets/icon.ico", target_name="IPTV-Saba")],
)
```

Build:
```bash
python setup.py build
```

Output: `build/exe.win-amd64-3.x/IPTV-Saba.exe`

---

## Step 5: Create Installer (Windows)

### Using Inno Setup

1. **Download Inno Setup**: https://jrsoftware.org/isdl.php

2. **Create installer script** (`installer.iss`):

```iss
[Setup]
AppName=IPTV Saba
AppVersion=2.0.0
DefaultDirName={pf}\IPTV-Saba
DefaultGroupName=IPTV Saba
OutputDir=installer_output
OutputBaseFilename=IPTV-Saba-Setup
Compression=lzma2
SolidCompression=yes
SetupIconFile=assets\icon.ico
WizardStyle=modern

[Files]
Source: "dist\IPTV-Saba.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "assets\*"; DestDir: "{app}\assets"; Flags: ignoreversion recursesubdirs

[Icons]
Name: "{group}\IPTV Saba"; Filename: "{app}\IPTV-Saba.exe"
Name: "{commondesktop}\IPTV Saba"; Filename: "{app}\IPTV-Saba.exe"

[Run]
Filename: "{app}\IPTV-Saba.exe"; Description: "Launch IPTV Saba"; Flags: nowait postinstall skipifsilent
```

3. **Compile**:
   - Open Inno Setup
   - File → Open → Select `installer.iss`
   - Build → Compile
   - Output: `installer_output/IPTV-Saba-Setup.exe`

---

## Step 6: Package for Distribution

### Windows

Create distribution folder structure:

```
IPTV-Saba-v2.0.0-Windows/
├── IPTV-Saba.exe
├── README.txt
├── LICENSE.txt
├── assets/
│   └── icon.png
└── Requirements.txt
```

**README.txt**:
```
IPTV Saba v2.0.0

REQUIREMENTS:
1. VLC Media Player (https://www.videolan.org/vlc/)
2. FFmpeg (for downloads) - Optional

INSTALLATION:
1. Run IPTV-Saba.exe
2. Create profile with M3U playlist URL
3. Login and enjoy!

FEATURES:
- M3U/M3U8 playlist support
- Channel browsing and search
- Video playback
- Download channels
- Fullscreen mode
- Keyboard shortcuts (Space=Play/Pause, F=Fullscreen, D=Download, Esc=Exit)

SUPPORT:
GitHub: https://github.com/yourusername/IPTV-Saba
```

**Compress to ZIP**:
```bash
# Windows (PowerShell)
Compress-Archive -Path "IPTV-Saba-v2.0.0-Windows" -DestinationPath "IPTV-Saba-v2.0.0-Windows.zip"

# Linux/Mac
zip -r IPTV-Saba-v2.0.0-Windows.zip IPTV-Saba-v2.0.0-Windows/
```

---

### Linux

Create AppImage:

1. **Install appimagetool**:
```bash
wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage
chmod +x appimagetool-x86_64.AppImage
```

2. **Create AppDir structure**:
```bash
mkdir -p IPTV-Saba.AppDir/usr/bin
mkdir -p IPTV-Saba.AppDir/usr/share/applications
mkdir -p IPTV-Saba.AppDir/usr/share/icons

cp dist/IPTV-Saba IPTV-Saba.AppDir/usr/bin/
```

3. **Create .desktop file** (`IPTV-Saba.AppDir/IPTV-Saba.desktop`):
```desktop
[Desktop Entry]
Type=Application
Name=IPTV Saba
Exec=IPTV-Saba
Icon=iptv-saba
Categories=AudioVideo;Video;Player;
```

4. **Build AppImage**:
```bash
./appimagetool-x86_64.AppImage IPTV-Saba.AppDir IPTV-Saba-v2.0.0-x86_64.AppImage
```

---

### macOS

Create DMG:

1. **Build app bundle**:
```bash
pyinstaller build.spec --windowed
```

2. **Create DMG** (requires `create-dmg`):
```bash
brew install create-dmg

create-dmg \
  --volname "IPTV Saba" \
  --window-pos 200 120 \
  --window-size 800 400 \
  --icon-size 100 \
  --app-drop-link 600 185 \
  "IPTV-Saba-v2.0.0.dmg" \
  "dist/IPTV-Saba.app"
```

---

## Step 7: Testing the Build

### Before Distribution

Test on clean system (VM recommended):

1. **Create fresh Windows VM**
   - Install VLC only
   - No Python or development tools
   - Run your .exe

2. **Verify**:
   - ✅ Application starts without errors
   - ✅ Login screen appears
   - ✅ Can create profile
   - ✅ Can load playlist
   - ✅ Video plays correctly
   - ✅ Downloads work
   - ✅ No missing DLL errors

3. **Common Issues**:

| Issue | Solution |
|-------|----------|
| `VCRUNTIME140.dll missing` | Include Visual C++ Redistributable |
| `No module named 'vlc'` | Add `--hidden-import=vlc` to PyInstaller |
| `Black screen in player` | Ensure VLC installed on target system |
| `Application won't start` | Check Windows Defender/antivirus |

---

## Step 8: Code Signing (Optional)

### Windows

1. **Obtain certificate**:
   - Purchase from CA (Comodo, DigiCert, etc.)
   - Or create self-signed for testing

2. **Sign executable**:
```bash
signtool sign /f certificate.pfx /p password /t http://timestamp.digicert.com IPTV-Saba.exe
```

Benefits:
- No Windows SmartScreen warning
- Users trust signed applications
- Required for enterprise distribution

---

## Step 9: Publishing

### GitHub Releases

1. Create repository
2. Tag version: `git tag v2.0.0`
3. Push tags: `git push --tags`
4. GitHub → Releases → Create new release
5. Upload:
   - `IPTV-Saba-v2.0.0-Windows.zip`
   - `IPTV-Saba-v2.0.0-x86_64.AppImage`
   - `IPTV-Saba-v2.0.0.dmg`

### Alternative Distribution

- **Microsoft Store**: Requires developer account ($19)
- **Website**: Host on GitHub Pages or custom domain
- **Direct download**: Use Dropbox/Google Drive for large files

---

## Troubleshooting

### Build Errors

**"ModuleNotFoundError during build"**
```bash
# Add to hiddenimports in build.spec:
hiddenimports=['missing_module_name'],
```

**"ImportError: DLL load failed"**
```bash
# Include binaries:
binaries=[('path/to/dll', '.')],
```

**"Application too large (>200MB)"**
```bash
# Exclude unused packages:
excludes=['matplotlib', 'numpy', 'pandas'],
```

### Runtime Errors

**"VLC not found"**
- Ensure VLC installed on target system
- Or bundle VLC with application (increases size to ~400MB)

**"FFmpeg not found for downloads"**
- Bundle ffmpeg.exe in assets folder
- Update download service to use bundled version

---

## File Size Optimization

### Reduce Executable Size

```bash
# Use UPX compression
pip install pyinstaller[encryption]
pyinstaller --onefile --upx-dir=/path/to/upx app/main.py
```

### Split Components

Create launcher + data files:
```
IPTV-Saba/
├── IPTV-Saba.exe       # 50MB
├── data/                # 150MB (libraries)
│   └── ...
└── assets/
```

```bash
pyinstaller --onedir app/main.py
```

---

## Automatic Updates

### Integrate auto-updater

```python
# app/utils/updater.py
import requests

def check_for_updates():
    """Check GitHub releases for new version."""
    try:
        response = requests.get('https://api.github.com/repos/user/repo/releases/latest')
        latest = response.json()['tag_name']
        current = '2.0.0'

        if latest > current:
            return latest, response.json()['assets'][0]['browser_download_url']
    except:
        pass

    return None, None
```

---

## Distribution Checklist

Before releasing:

- [ ] Test on clean Windows 10/11
- [ ] Test on clean Linux (Ubuntu/Fedora)
- [ ] Test on clean macOS (if applicable)
- [ ] Verify all features work
- [ ] Check file size reasonable (<150MB)
- [ ] Include README with instructions
- [ ] Include LICENSE file
- [ ] Create release notes
- [ ] Upload to GitHub/website
- [ ] Announce release

---

## License and Legal

Include licenses for dependencies:
- PyQt5: GPL v3
- Python-VLC: LGPL
- VLC (if bundled): GPL v2

Your application must be GPL-compatible if distributing VLC.

---

## Support Resources

- **PyInstaller Documentation**: https://pyinstaller.readthedocs.io/
- **cx_Freeze Manual**: https://cx-freeze.readthedocs.io/
- **Inno Setup**: https://jrsoftware.org/isinfo.php
- **Code Signing**: https://docs.microsoft.com/en-us/windows/win32/seccrypto/signtool

---

## Quick Reference Commands

```bash
# Full build process (Windows)
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install pyinstaller
pyinstaller --onefile --windowed --icon=assets/icon.ico app/main.py
iscc installer.iss

# Test build
dist\IPTV-Saba.exe

# Package
Compress-Archive -Path dist\IPTV-Saba.exe -DestinationPath IPTV-Saba-v2.0.0.zip
```

---

**Export complete! Your application is ready for distribution.**

# IPTV-Saba Development Setup Guide

## Prerequisites

### Required Software

| Software | Version | Purpose |
|----------|---------|---------|
| Python | 3.8+ | Runtime |
| VLC Media Player | 3.0+ | Video playback |
| Git | 2.0+ | Version control |
| pip | Latest | Package management |

### Recommended Tools

| Tool | Purpose |
|------|---------|
| VS Code / PyCharm | IDE |
| Python extension | Linting, debugging |
| Qt Designer | UI prototyping |

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Roialfassi/IPTV-Saba.git
cd IPTV-Saba
```

### 2. Create Virtual Environment

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/macOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install VLC

**Windows:**
- Download from [videolan.org](https://www.videolan.org/)
- Install to default location: `C:\Program Files\VideoLAN\VLC\`

**Linux (Ubuntu/Debian):**
```bash
sudo apt install vlc libvlc-dev
```

**macOS:**
```bash
brew install vlc
```

### 5. Verify Installation

```bash
cd src
python -c "import vlc; print('VLC:', vlc.libvlc_get_version())"
python -c "from PyQt5.QtWidgets import QApplication; print('PyQt5: OK')"
```

## Project Structure

```
IPTV-Saba/
├── src/                    # Source code
│   ├── iptv_app.py        # Entry point
│   ├── controller/        # Business logic
│   ├── model/             # Data models
│   ├── view/              # PyQt5 UI
│   ├── data/              # Data layer
│   ├── services/          # Service layer
│   └── Assets/            # Resources
├── docs/                   # Documentation
├── tests/                  # Test files
├── requirements.txt        # Dependencies
└── CLAUDE.md              # AI assistant guide
```

## Running the Application

### Standard Run

```bash
cd src
python iptv_app.py
```

### Debug Mode

```bash
cd src
python -m pdb iptv_app.py
```

### With Logging

```bash
cd src
python iptv_app.py 2>&1 | tee app.log
```

## Development Workflow

### 1. Create Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

- Follow coding conventions in CLAUDE.md
- Add type hints
- Write docstrings
- Log important operations

### 3. Test Changes

```bash
# Manual testing
python iptv_app.py

# Run existing tests
python ../test_simple.py
python ../test_optimized_loader.py
```

### 4. Commit Changes

```bash
git add -p  # Stage selectively
git commit -m "feat: your feature description"
```

### 5. Push and Create PR

```bash
git push -u origin feature/your-feature-name
```

## Coding Standards

### Python Style

- Follow PEP 8
- Use 4 spaces for indentation
- Max line length: 100 characters
- Use type hints for function signatures

### Imports

```python
# Standard library
import os
import logging

# Third-party
from PyQt5.QtCore import QObject, pyqtSignal

# Local
from src.model.channel_model import Channel
```

### Docstrings

```python
def function_name(param: str) -> bool:
    """
    Brief description of function.

    Args:
        param: Description of parameter

    Returns:
        Description of return value

    Raises:
        ValueError: When param is invalid
    """
```

### Logging

```python
import logging
logger = logging.getLogger(__name__)

logger.debug("Detailed debugging info")
logger.info("General information")
logger.warning("Warning message")
logger.error("Error message")
```

## Debugging

### PyQt5 Debugging

```python
# Enable Qt debug output
import os
os.environ['QT_DEBUG_PLUGINS'] = '1'
```

### VLC Debugging

```python
# Enable VLC verbose mode
vlc_instance = vlc.Instance('--verbose=2')
```

### Common Issues

#### "No module named 'src'"

Run from correct directory:
```bash
cd IPTV-Saba/src
python iptv_app.py
```

Or add to path:
```python
import sys
sys.path.insert(0, '/path/to/IPTV-Saba')
```

#### "VLC not found"

Check VLC installation:
```python
import vlc
print(vlc.libvlc_get_version())
```

#### Black Screen

Check window ID attachment timing:
```python
# Must attach AFTER window is shown
def showEvent(self, event):
    super().showEvent(event)
    QTimer.singleShot(100, self.attach_player)
```

## Testing

### Manual Testing Checklist

- [ ] Profile create/delete
- [ ] M3U loading (small and large)
- [ ] Channel playback
- [ ] Fullscreen transition
- [ ] Favorites management
- [ ] Easy Mode
- [ ] Download/Record

### Test Files

```bash
# Basic functionality
python test_simple.py

# Performance benchmark
python test_optimized_loader.py
```

## IDE Setup

### VS Code

**settings.json:**
```json
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true
}
```

**Recommended Extensions:**
- Python (Microsoft)
- Pylance
- Python Docstring Generator

### PyCharm

1. Open project folder
2. Configure Python interpreter to use venv
3. Enable PEP 8 checks
4. Set up run configuration for `src/iptv_app.py`

## Building Distribution

### PyInstaller (Windows)

```bash
pip install pyinstaller
cd src
pyinstaller --onefile --windowed --icon=Assets/iptv-logo2.ico iptv_app.py
```

### Spec File

See `src/iptv_saba.spec` for build configuration.

## Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `QT_DEBUG_PLUGINS` | Qt debug output | Unset |
| `VLC_VERBOSE` | VLC verbosity | 0 |
| `IPTV_LOG_LEVEL` | App log level | INFO |

## Resources

- [PyQt5 Documentation](https://www.riverbankcomputing.com/static/Docs/PyQt5/)
- [python-vlc Documentation](https://www.olivieraubert.net/vlc/python-ctypes/doc/)
- [VLC Command Line](https://wiki.videolan.org/VLC_command-line_help/)
- [M3U Format](https://en.wikipedia.org/wiki/M3U)

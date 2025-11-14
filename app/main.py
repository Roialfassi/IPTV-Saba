#!/usr/bin/env python3
"""
IPTV Saba - Main Application Entry Point
Production-ready IPTV player with download support
"""
import sys
import logging
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

from app.core.application import IPTVApplication
from app.core.config import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('iptv_saba.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


def setup_application() -> QApplication:
    """Initialize Qt application with settings."""
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    app.setApplicationName("IPTV Saba")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("IPTV")
    app.setOrganizationDomain("iptv-saba.local")

    icon_path = Path(__file__).parent.parent / "assets" / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    return app


def main():
    """Application entry point."""
    try:
        app = setup_application()

        Config.initialize()

        window = IPTVApplication()
        window.show()

        logger.info("Application started successfully")
        sys.exit(app.exec_())

    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

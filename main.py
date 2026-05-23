import sys
import os
import logging
from logging.handlers import RotatingFileHandler

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(ROOT_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(),
        RotatingFileHandler(
            os.path.join(LOG_DIR, "aura.log"),
            maxBytes=2 * 1024 * 1024,  # 2MB
            backupCount=3,
            encoding="utf-8",
        ),
    ],
)

if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import core.config  # noqa: F401  — env vars must be set before funasr import

from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow
from server.ws_server import ws_manager


def main():
    ws_manager.start()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()

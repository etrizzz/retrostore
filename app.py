from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from retrohub.config import AppConfig
from retrohub.logging_utils import configure_logging
from retrohub.services.downloader import DownloadService
from retrohub.services.library import LibraryRepository
from retrohub.services.search_service import SearchService
from retrohub.ui.main_window import MainWindow, apply_app_palette


def main() -> int:
    config = AppConfig()
    config.paths.ensure()
    configure_logging(config.paths.logs)
    app = QApplication(sys.argv)
    apply_app_palette(app)
    window = MainWindow(
        search_service=SearchService(config),
        download_service=DownloadService(config),
        library_repo=LibraryRepository(config.paths.root),
    )
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())

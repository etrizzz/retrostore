from __future__ import annotations

import logging
import traceback
from typing import Callable

from PySide6.QtCore import QObject, QRunnable, QThreadPool, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from retrohub.models import GameRecord
from retrohub.services.downloader import DownloadService
from retrohub.services.library import LibraryRepository
from retrohub.services.search_service import SearchService

logger = logging.getLogger(__name__)


class WorkerSignals(QObject):
    success = Signal(object)
    error = Signal(str)


class Worker(QRunnable):
    def __init__(self, fn: Callable, *args, **kwargs) -> None:
        super().__init__()
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self) -> None:
        try:
            result = self.fn(*self.args, **self.kwargs)
            self.signals.success.emit(result)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Worker failure")
            self.signals.error.emit(f"{exc}\n\n{traceback.format_exc(limit=4)}")


class MainWindow(QMainWindow):
    def __init__(self, search_service: SearchService, download_service: DownloadService, library_repo: LibraryRepository) -> None:
        super().__init__()
        self.search_service = search_service
        self.download_service = download_service
        self.library_repo = library_repo
        self.thread_pool = QThreadPool.globalInstance()
        self.current_results: list[GameRecord] = []
        self.setWindowTitle("RetroHub Cinema")
        self.resize(1440, 900)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(22, 22, 22, 22)
        outer.setSpacing(16)

        hero = QFrame()
        hero.setObjectName("hero")
        hero_layout = QVBoxLayout(hero)
        title = QLabel("RETROHUB CINEMA")
        title.setFont(QFont("Arial", 26, QFont.Weight.Bold))
        subtitle = QLabel("Recherche multi-sources, téléchargement robuste et lancement one-click pour DOS/ScummVM.")
        subtitle.setWordWrap(True)
        hero_layout.addWidget(title)
        hero_layout.addWidget(subtitle)
        outer.addWidget(hero)

        search_row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Ex: Monkey Island, Doom, Prince of Persia...")
        self.search_button = QPushButton("Rechercher")
        self.search_button.clicked.connect(self.start_search)
        search_row.addWidget(self.search_input, 1)
        search_row.addWidget(self.search_button)
        outer.addLayout(search_row)

        content = QGridLayout()
        content.setColumnStretch(0, 2)
        content.setColumnStretch(1, 3)
        outer.addLayout(content, 1)

        self.results_list = QListWidget()
        self.results_list.currentRowChanged.connect(self._show_details)
        content.addWidget(self.results_list, 0, 0)

        right = QVBoxLayout()
        content.addLayout(right, 0, 1)

        self.details = QTextEdit()
        self.details.setReadOnly(True)
        right.addWidget(self.details, 1)

        action_row = QHBoxLayout()
        self.download_button = QPushButton("Télécharger / Lancer")
        self.download_button.clicked.connect(self.start_download)
        self.library_button = QPushButton("Voir la bibliothèque")
        self.library_button.clicked.connect(self.show_library)
        action_row.addWidget(self.download_button)
        action_row.addWidget(self.library_button)
        right.addLayout(action_row)

        self.status_label = QLabel("Prêt.")
        outer.addWidget(self.status_label)

        self._apply_theme()

    def _apply_theme(self) -> None:
        self.setStyleSheet(
            """
            QWidget { background-color: #0b0b0d; color: #f4f1ea; }
            QFrame#hero { background-color: #13131a; border: 1px solid #39291a; border-radius: 18px; padding: 18px; }
            QLineEdit, QListWidget, QTextEdit { background-color: #121217; border: 1px solid #2c2c35; border-radius: 12px; padding: 12px; }
            QPushButton { background-color: #7a4b12; border: none; border-radius: 12px; padding: 12px 16px; font-weight: 700; }
            QPushButton:hover { background-color: #a16015; }
            QPushButton:disabled { background-color: #444; color: #999; }
            QListWidget::item:selected { background-color: #2f261d; border-radius: 8px; }
            """
        )

    def start_search(self) -> None:
        query = self.search_input.text().strip()
        if not query:
            self._warn("Saisis un titre de jeu avant de lancer la recherche.")
            return
        self._set_busy(True, f"Recherche en cours pour '{query}'...")
        worker = Worker(self.search_service.search, query)
        worker.signals.success.connect(self._populate_results)
        worker.signals.error.connect(self._handle_error)
        self.thread_pool.start(worker)

    def _populate_results(self, result) -> None:
        self.results_list.clear()
        self.current_results = result.results
        for record in result.results:
            badge = f"[{record.provider}] [{record.game_type.value}]"
            QListWidgetItem(f"{badge} {record.title}", self.results_list)
        warnings = "\n".join(result.warnings)
        self.status_label.setText(f"{len(result.results)} résultat(s). {warnings}".strip())
        self._set_busy(False)
        if result.results:
            self.results_list.setCurrentRow(0)
        else:
            self.details.setText("Aucun résultat exploitable.")

    def _show_details(self, row: int) -> None:
        if row < 0 or row >= len(self.current_results):
            self.details.clear()
            return
        record = self.current_results[row]
        self.details.setText(
            f"Titre: {record.title}\n"
            f"Source: {record.provider}\n"
            f"Type: {record.game_type.value}\n"
            f"Année: {record.year or 'n/a'}\n"
            f"Genre/Plateforme: {record.genre or 'n/a'}\n"
            f"URL: {record.source_url}\n"
            f"Assets détectés: {len(record.assets)}\n\n"
            f"Résumé:\n{record.summary}"
        )

    def start_download(self) -> None:
        row = self.results_list.currentRow()
        if row < 0:
            self._warn("Sélectionne un jeu avant de télécharger.")
            return
        record = self.current_results[row]
        self._set_busy(True, f"Téléchargement de {record.title}...")
        worker = Worker(self.download_service.process_game, record)
        worker.signals.success.connect(self._download_complete)
        worker.signals.error.connect(self._handle_error)
        self.thread_pool.start(worker)

    def _download_complete(self, result) -> None:
        self.library_repo.add(result)
        self._set_busy(False, f"Terminé : {result.message}")
        QMessageBox.information(
            self,
            "Traitement terminé",
            f"Jeu: {result.record.title}\nDestination: {result.final_path}\n\n{result.message}",
        )

    def show_library(self) -> None:
        rows = self.library_repo.list_all(raw=True)
        if not rows:
            self._warn("La bibliothèque est vide pour l'instant.")
            return
        text = "\n\n".join(f"{item['title']}\n{item['path']}\n{item['message']}" for item in rows)
        QMessageBox.information(self, "Bibliothèque locale", text)

    def _handle_error(self, error_text: str) -> None:
        self._set_busy(False, "Une erreur a été capturée sans fermer l'application.")
        QMessageBox.critical(self, "Erreur gérée", error_text)

    def _warn(self, message: str) -> None:
        QMessageBox.warning(self, "RetroHub Cinema", message)

    def _set_busy(self, busy: bool, message: str | None = None) -> None:
        self.search_button.setDisabled(busy)
        self.download_button.setDisabled(busy)
        if message:
            self.status_label.setText(message)


def apply_app_palette(app: QApplication) -> None:
    palette = app.palette()
    palette.setColor(palette.Window, QColor("#0b0b0d"))
    palette.setColor(palette.WindowText, QColor("#f4f1ea"))
    app.setPalette(palette)

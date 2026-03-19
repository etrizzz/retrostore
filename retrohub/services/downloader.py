from __future__ import annotations

import logging
import shutil
import time
import zipfile
from pathlib import Path, PurePosixPath
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

try:
    import requests
except ModuleNotFoundError:  # pragma: no cover - optional in test environment
    requests = None

from retrohub.config import AppConfig
from retrohub.models import DownloadAsset, DownloadResult, GameRecord, GameType
from retrohub.services.launcher import LauncherService

logger = logging.getLogger(__name__)

try:
    import py7zr
except ModuleNotFoundError:  # pragma: no cover - optional dependency at runtime
    py7zr = None


class DownloadError(Exception):
    pass


class DownloadService:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.launcher = LauncherService(config)
        self.session = requests.Session() if requests is not None else None
        if self.session is not None:
            self.session.headers.update({"User-Agent": "RetroHubCinema/1.0 (+desktop downloader)"})

    def process_game(self, record: GameRecord) -> DownloadResult:
        if not record.assets:
            raise DownloadError("Aucun asset téléchargeable détecté pour ce jeu.")
        asset = self._pick_asset(record.assets)
        self.config.paths.ensure()
        target = self.config.paths.downloads / asset.filename
        self._download(asset, target)
        if record.game_type in {GameType.DOS, GameType.SCUMMVM} and target.suffix.lower() in {".zip", ".7z"}:
            final_dir = self.config.paths.library / self._safe_name(record.title)
            if final_dir.exists():
                shutil.rmtree(final_dir)
            final_dir.mkdir(parents=True, exist_ok=True)
            self._extract(target, final_dir)
            launched, message = self.launcher.launch(record, final_dir)
            return DownloadResult(record=record, download_path=target, final_path=final_dir, launched=launched, message=message)
        final_path = self.config.paths.installers / asset.filename
        shutil.copy2(target, final_path)
        return DownloadResult(
            record=record,
            download_path=target,
            final_path=final_path,
            launched=False,
            message="Package complexe détecté : copie vers A_Installer_Manuellement effectuée. Double-clique ensuite sur l'installateur ou monte l'ISO.",
        )

    def _download(self, asset: DownloadAsset, target: Path) -> None:
        errors: list[str] = []
        tmp = target.with_suffix(target.suffix + ".part")
        for attempt in range(1, self.config.network.max_retries + 1):
            try:
                if self.session is not None:
                    self._download_with_requests(asset, tmp)
                else:
                    self._download_with_urllib(asset, tmp)
                if tmp.stat().st_size == 0:
                    raise DownloadError(f"Téléchargement vide pour {asset.url}")
                tmp.replace(target)
                return
            except Exception as exc:  # noqa: BLE001
                retryable = self._is_retryable_exception(exc)
                errors.append(f"tentative {attempt}: {exc}")
                if tmp.exists():
                    tmp.unlink(missing_ok=True)
                if not retryable or attempt >= self.config.network.max_retries:
                    break
                time.sleep(min(2 ** (attempt - 1), 8))
        raise DownloadError("; ".join(errors))

    def _download_with_requests(self, asset: DownloadAsset, tmp: Path) -> None:
        assert self.session is not None
        logger.info("Downloading %s", asset.url)
        with self.session.get(asset.url, timeout=self.config.network.timeout_seconds, stream=True) as response:
            response.raise_for_status()
            with tmp.open("wb") as handle:
                for chunk in response.iter_content(chunk_size=self.config.network.chunk_size):
                    if chunk:
                        handle.write(chunk)

    def _download_with_urllib(self, asset: DownloadAsset, tmp: Path) -> None:
        logger.info("Downloading %s", asset.url)
        request = Request(asset.url, headers={"User-Agent": "RetroHubCinema/1.0 (+desktop downloader)"})
        with urlopen(request, timeout=self.config.network.timeout_seconds) as response:
            with tmp.open("wb") as handle:
                while True:
                    chunk = response.read(self.config.network.chunk_size)
                    if not chunk:
                        break
                    handle.write(chunk)

    @staticmethod
    def _is_retryable_exception(exc: Exception) -> bool:
        if isinstance(exc, (DownloadError, OSError, URLError, HTTPError)):
            return True
        if requests is not None and isinstance(exc, requests.RequestException):
            return True
        return False

    def _extract(self, archive_path: Path, destination: Path) -> None:
        try:
            if archive_path.suffix.lower() == ".zip":
                with zipfile.ZipFile(archive_path) as zf:
                    bad = zf.testzip()
                    if bad:
                        raise DownloadError(f"Archive ZIP corrompue: {bad}")
                    for member in zf.infolist():
                        self._validate_member_path(member.filename)
                    zf.extractall(destination)
            elif archive_path.suffix.lower() == ".7z":
                if py7zr is None:
                    raise DownloadError("py7zr non installé : extraction .7z indisponible.")
                with py7zr.SevenZipFile(archive_path, mode="r") as archive:
                    for name in archive.getnames():
                        self._validate_member_path(name)
                with py7zr.SevenZipFile(archive_path, mode="r") as archive:
                    archive.extractall(destination)
            else:
                raise DownloadError(f"Format d'extraction non supporté: {archive_path.suffix}")
        except zipfile.BadZipFile as exc:
            raise DownloadError(f"Archive corrompue: {exc}") from exc
        except Exception as exc:
            if py7zr is not None and isinstance(exc, py7zr.exceptions.Bad7zFile):
                raise DownloadError(f"Archive corrompue: {exc}") from exc
            if isinstance(exc, DownloadError):
                raise
            raise DownloadError(f"Extraction impossible: {exc}") from exc

    @staticmethod
    def _validate_member_path(member_name: str) -> None:
        path = PurePosixPath(member_name)
        if path.is_absolute() or ".." in path.parts:
            raise DownloadError(f"Entrée d'archive dangereuse détectée: {member_name}")

    @staticmethod
    def _pick_asset(assets: list[DownloadAsset]) -> DownloadAsset:
        preferred = sorted(
            assets,
            key=lambda item: {"zip": 0, "7z": 1, "iso": 2, "cue": 3, "exe": 4}.get(item.format_hint or "", 9),
        )
        return preferred[0]

    @staticmethod
    def _safe_name(name: str) -> str:
        return "".join(char if char.isalnum() or char in "-_ " else "_" for char in name).strip() or "game"

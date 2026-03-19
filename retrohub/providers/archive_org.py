from __future__ import annotations

import logging
from typing import Any

import requests

from retrohub.config import AppConfig
from retrohub.models import DownloadAsset, GameRecord, GameType, SearchResult
from retrohub.providers.base import SearchProvider

logger = logging.getLogger(__name__)


class ArchiveOrgProvider(SearchProvider):
    name = "Archive.org"
    API_URL = "https://archive.org/advancedsearch.php"

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "RetroHubCinema/1.0 (+desktop research client)"})

    def search(self, query: str, limit: int = 8) -> SearchResult:
        params = {
            "q": f'title:("{query}") AND mediatype:(software)',
            "fl[]": ["identifier", "title", "description", "subject", "year", "downloads"],
            "rows": limit,
            "page": 1,
            "output": "json",
        }
        response = self.session.get(
            self.API_URL,
            params=params,
            timeout=self.config.network.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        results: list[GameRecord] = []
        for doc in data.get("response", {}).get("docs", []):
            identifier = doc.get("identifier")
            if not identifier:
                continue
            title = doc.get("title") or identifier
            description = doc.get("description")
            if isinstance(description, list):
                description = " ".join(description)
            subject = doc.get("subject")
            genre = ", ".join(subject) if isinstance(subject, list) else subject
            results.append(
                GameRecord(
                    title=title,
                    provider=self.name,
                    summary=(description or "Collection logicielle issue d'Archive.org.")[:500],
                    source_url=f"https://archive.org/details/{identifier}",
                    year=str(doc.get("year")) if doc.get("year") else None,
                    genre=genre,
                    game_type=self._infer_type(title, description or "", genre or ""),
                    assets=self._build_assets(identifier),
                    raw=doc,
                )
            )
        return SearchResult(query=query, results=results)

    def _build_assets(self, identifier: str) -> list[DownloadAsset]:
        metadata_url = f"https://archive.org/metadata/{identifier}"
        try:
            response = self.session.get(metadata_url, timeout=self.config.network.timeout_seconds)
            response.raise_for_status()
            payload: dict[str, Any] = response.json()
        except Exception as exc:  # noqa: BLE001
            logger.warning("Archive metadata unavailable for %s: %s", identifier, exc)
            return []

        files = payload.get("files", []) or []
        assets: list[DownloadAsset] = []
        for item in files:
            name = item.get("name", "")
            if name.endswith((".zip", ".7z", ".iso", ".cue", ".exe")):
                assets.append(
                    DownloadAsset(
                        url=f"https://archive.org/download/{identifier}/{name}",
                        filename=name,
                        size_label=item.get("size"),
                        format_hint=name.rsplit(".", 1)[-1].lower(),
                    )
                )
        return assets

    @staticmethod
    def _infer_type(title: str, description: str, genre: str) -> GameType:
        blob = f"{title} {description} {genre}".lower()
        if any(token in blob for token in ["scummvm", "adventure", "lucasarts"]):
            return GameType.SCUMMVM
        if any(token in blob for token in ["windows 95", "windows 98", ".iso", "cd-rom"]):
            return GameType.WINDOWS
        if any(token in blob for token in ["dos", "ms-dos", "dosbox"]):
            return GameType.DOS
        return GameType.UNKNOWN

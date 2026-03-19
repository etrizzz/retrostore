from __future__ import annotations

import logging
from urllib.parse import quote_plus, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from retrohub.config import AppConfig
from retrohub.models import DownloadAsset, GameRecord, GameType, SearchResult
from retrohub.providers.base import SearchProvider

logger = logging.getLogger(__name__)


class MyAbandonwareProvider(SearchProvider):
    name = "MyAbandonware"
    BASE_URL = "https://www.myabandonware.com"

    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "RetroHubCinema/1.0 (+desktop research client)"})

    def search(self, query: str, limit: int = 8) -> SearchResult:
        search_url = f"{self.BASE_URL}/search/q/{quote_plus(query)}"
        response = self.session.get(search_url, timeout=self.config.network.timeout_seconds)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "lxml")
        cards = soup.select("a.gameLink, a.item")[:limit]
        results: list[GameRecord] = []
        for card in cards:
            href = card.get("href")
            if not href:
                continue
            title = card.select_one(".gameTitle, .item-title")
            meta = card.select_one(".gameYear, .item-year")
            platform = card.select_one(".gamePlatform, .item-platform")
            record = GameRecord(
                title=title.get_text(strip=True) if title else href.rsplit("/", 1)[-1],
                provider=self.name,
                summary="Fiche indexée depuis MyAbandonware.",
                source_url=urljoin(self.BASE_URL, href),
                year=meta.get_text(strip=True) if meta else None,
                genre=platform.get_text(strip=True) if platform else None,
                game_type=self._infer_type(platform.get_text(" ", strip=True) if platform else ""),
            )
            self._hydrate_detail(record)
            results.append(record)
        return SearchResult(query=query, results=results)

    def _hydrate_detail(self, record: GameRecord) -> None:
        try:
            response = self.session.get(record.source_url, timeout=self.config.network.timeout_seconds)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "lxml")
            desc = soup.select_one(".text-break, .gamePageText, .overview")
            if desc:
                record.summary = desc.get_text(" ", strip=True)[:600]
            cover = soup.select_one(".gameCover img, .cover img")
            if cover and cover.get("src"):
                record.cover_url = urljoin(self.BASE_URL, cover["src"])
            downloads = []
            for link in soup.select("a[href*='/download/'], a[href*='download_game'], a.button-download"):
                href = link.get("href")
                if not href:
                    continue
                filename = self._guess_filename(href)
                downloads.append(
                    DownloadAsset(
                        url=urljoin(self.BASE_URL, href),
                        filename=filename,
                        format_hint=filename.rsplit(".", 1)[-1].lower() if "." in filename else None,
                    )
                )
            record.assets = downloads
        except Exception as exc:  # noqa: BLE001
            logger.warning("Unable to hydrate MyAbandonware detail for %s: %s", record.title, exc)

    @staticmethod
    def _guess_filename(url: str) -> str:
        path = urlparse(url).path
        name = path.rsplit("/", 1)[-1] or "download.bin"
        return name

    @staticmethod
    def _infer_type(platform: str) -> GameType:
        lowered = platform.lower()
        if "dos" in lowered:
            return GameType.DOS
        if "windows" in lowered:
            return GameType.WINDOWS
        return GameType.UNKNOWN

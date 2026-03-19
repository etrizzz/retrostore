from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from retrohub.models import GameRecord, GameType, SearchResult
from retrohub.providers.base import SearchProvider


class ExoDOSManifestProvider(SearchProvider):
    name = "eXoDOS Manifest"

    def __init__(self, manifest_path: Path) -> None:
        self.manifest_path = manifest_path

    def search(self, query: str, limit: int = 10) -> SearchResult:
        if not self.manifest_path.exists():
            return SearchResult(query=query, results=[], warnings=[f"Manifeste eXoDOS introuvable: {self.manifest_path}"])
        root = ET.parse(self.manifest_path).getroot()
        results: list[GameRecord] = []
        lowered = query.lower()
        for game in root.findall(".//Game"):
            title = (game.findtext("Title") or "").strip()
            if lowered not in title.lower():
                continue
            results.append(
                GameRecord(
                    title=title,
                    provider=self.name,
                    summary=(game.findtext("Notes") or "Métadonnées importées d'un export LaunchBox/eXoDOS.")[:500],
                    source_url="local://exodos-manifest",
                    year=game.findtext("ReleaseDate"),
                    genre=game.findtext("Genre"),
                    game_type=GameType.DOS,
                    raw={"application_path": game.findtext("ApplicationPath")},
                )
            )
            if len(results) >= limit:
                break
        return SearchResult(query=query, results=results)

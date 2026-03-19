from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path


class GameType(str, Enum):
    DOS = "dos"
    SCUMMVM = "scummvm"
    WINDOWS = "windows"
    UNKNOWN = "unknown"


@dataclass(slots=True)
class DownloadAsset:
    url: str
    filename: str
    size_label: str | None = None
    format_hint: str | None = None
    provider_asset_id: str | None = None


@dataclass(slots=True)
class GameRecord:
    title: str
    provider: str
    summary: str
    source_url: str
    genre: str | None = None
    year: str | None = None
    game_type: GameType = GameType.UNKNOWN
    assets: list[DownloadAsset] = field(default_factory=list)
    cover_url: str | None = None
    raw: dict = field(default_factory=dict)


@dataclass(slots=True)
class DownloadResult:
    record: GameRecord
    download_path: Path
    final_path: Path
    launched: bool = False
    message: str = ""


@dataclass(slots=True)
class SearchResult:
    query: str
    results: list[GameRecord]
    warnings: list[str] = field(default_factory=list)

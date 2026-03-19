from __future__ import annotations

import json
from pathlib import Path

from retrohub.models import DownloadResult, GameRecord


class LibraryRepository:
    def __init__(self, root: Path) -> None:
        self.path = root / "library_index.json"
        if not self.path.exists():
            self.path.write_text("[]", encoding="utf-8")

    def add(self, result: DownloadResult) -> None:
        items = self.list_all(raw=True)
        items.append(
            {
                "title": result.record.title,
                "provider": result.record.provider,
                "source_url": result.record.source_url,
                "game_type": result.record.game_type.value,
                "path": str(result.final_path),
                "launched": result.launched,
                "message": result.message,
            }
        )
        self.path.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")

    def list_all(self, raw: bool = False) -> list[dict] | list[GameRecord]:
        items = json.loads(self.path.read_text(encoding="utf-8"))
        if raw:
            return items
        return [
            GameRecord(
                title=item["title"],
                provider=item["provider"],
                summary=item.get("message", ""),
                source_url=item["source_url"],
            )
            for item in items
        ]

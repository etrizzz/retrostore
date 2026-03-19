from __future__ import annotations

import logging
from pathlib import Path

from retrohub.config import AppConfig
from retrohub.models import GameRecord, SearchResult
from retrohub.providers.archive_org import ArchiveOrgProvider
from retrohub.providers.exodos_manifest import ExoDOSManifestProvider
from retrohub.providers.mobygames import MobyGamesProvider
from retrohub.providers.myabandonware import MyAbandonwareProvider
from retrohub.providers.base import SearchProvider

logger = logging.getLogger(__name__)


class SearchService:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        manifest = config.paths.manifests / "exodos.xml"
        self.providers: list[SearchProvider] = [
            ArchiveOrgProvider(config),
            MyAbandonwareProvider(config),
            MobyGamesProvider(config),
            ExoDOSManifestProvider(manifest),
        ]

    def search(self, query: str, per_provider: int = 5) -> SearchResult:
        aggregate: list[GameRecord] = []
        warnings: list[str] = []
        for provider in self.providers:
            try:
                result = provider.search(query, limit=per_provider)
                aggregate.extend(result.results)
                warnings.extend(result.warnings)
            except Exception as exc:  # noqa: BLE001
                logger.exception("Search provider failed: %s", provider.name)
                warnings.append(f"{provider.name}: {exc}")
        aggregate.sort(key=lambda item: (item.game_type.value, item.title.lower()))
        return SearchResult(query=query, results=aggregate, warnings=warnings)

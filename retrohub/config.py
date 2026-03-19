from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

APP_NAME = "RetroHub Cinema"


def _default_root() -> Path:
    env_root = os.getenv("RETROHUB_HOME")
    if env_root:
        return Path(env_root).expanduser().resolve()
    return (Path.home() / "RetroHubCinema").resolve()


@dataclass(slots=True)
class AppPaths:
    root: Path = field(default_factory=_default_root)

    @property
    def downloads(self) -> Path:
        return self.root / "downloads"

    @property
    def library(self) -> Path:
        return self.root / "library"

    @property
    def installers(self) -> Path:
        return self.root / "A_Installer_Manuellement"

    @property
    def cache(self) -> Path:
        return self.root / "cache"

    @property
    def manifests(self) -> Path:
        return self.root / "manifests"

    @property
    def logs(self) -> Path:
        return self.root / "logs"

    def ensure(self) -> None:
        for path in [
            self.root,
            self.downloads,
            self.library,
            self.installers,
            self.cache,
            self.manifests,
            self.logs,
        ]:
            path.mkdir(parents=True, exist_ok=True)


@dataclass(slots=True)
class LauncherSettings:
    dosbox_path: str | None = os.getenv("DOSBOX_PATH")
    scummvm_path: str | None = os.getenv("SCUMMVM_PATH")


@dataclass(slots=True)
class NetworkSettings:
    timeout_seconds: int = int(os.getenv("RETROHUB_TIMEOUT", "25"))
    max_retries: int = int(os.getenv("RETROHUB_MAX_RETRIES", "3"))
    chunk_size: int = int(os.getenv("RETROHUB_CHUNK_SIZE", str(1024 * 256)))


@dataclass(slots=True)
class AppConfig:
    paths: AppPaths = field(default_factory=AppPaths)
    launchers: LauncherSettings = field(default_factory=LauncherSettings)
    network: NetworkSettings = field(default_factory=NetworkSettings)
    mobygames_api_key: str | None = os.getenv("MOBYGAMES_API_KEY")

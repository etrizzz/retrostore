from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path

from retrohub.config import AppConfig
from retrohub.models import GameRecord, GameType


class LauncherService:
    def __init__(self, config: AppConfig) -> None:
        self.config = config

    def launch(self, record: GameRecord, folder: Path) -> tuple[bool, str]:
        if record.game_type == GameType.SCUMMVM:
            return self._launch_scummvm(folder)
        if record.game_type == GameType.DOS:
            return self._launch_dosbox(folder)
        return False, "Jeu copié dans A_Installer_Manuellement : installation manuelle requise."

    def _launch_dosbox(self, folder: Path) -> tuple[bool, str]:
        dosbox = self._resolve_launcher("dosbox", self.config.launchers.dosbox_path)
        if not dosbox:
            return False, "DOSBox introuvable. Définis DOSBOX_PATH ou installe DOSBox dans Program Files."
        conf = folder / "retrohub_dosbox.conf"
        autoexec = self._find_executable(folder)
        conf.write_text(
            "[autoexec]\n"
            f"mount c \"{folder}\"\n"
            "c:\n"
            f"{autoexec}\n"
            "exit\n",
            encoding="utf-8",
        )
        subprocess.Popen([dosbox, "-conf", str(conf)], cwd=folder)
        return True, f"DOSBox lancé avec {autoexec}."

    def _launch_scummvm(self, folder: Path) -> tuple[bool, str]:
        scummvm = self._resolve_launcher("scummvm", self.config.launchers.scummvm_path)
        if not scummvm:
            return False, "ScummVM introuvable. Définis SCUMMVM_PATH ou installe ScummVM dans Program Files."
        subprocess.Popen([scummvm, "--path", str(folder)], cwd=folder)
        return True, "ScummVM lancé automatiquement (dossier préchargé)."

    def _resolve_launcher(self, executable_name: str, configured_path: str | None) -> str | None:
        candidates: list[str] = []
        if configured_path:
            candidates.append(configured_path)
        which = shutil.which(executable_name)
        if which:
            candidates.append(which)
        if os.name == "nt":
            for base in filter(None, [os.getenv("ProgramFiles"), os.getenv("ProgramFiles(x86)")]):
                if executable_name == "dosbox":
                    candidates.extend(
                        [
                            str(Path(base) / "DOSBox-0.74-3" / "DOSBox.exe"),
                            str(Path(base) / "DOSBox Staging" / "dosbox.exe"),
                        ]
                    )
                if executable_name == "scummvm":
                    candidates.append(str(Path(base) / "ScummVM" / "scummvm.exe"))
        for candidate in candidates:
            if candidate and Path(candidate).exists():
                return str(Path(candidate))
        return None

    @staticmethod
    def _find_executable(folder: Path) -> str:
        for pattern in ("*.bat", "*.exe", "*.com"):
            matches = sorted(folder.rglob(pattern))
            if matches:
                return os.path.relpath(matches[0], folder).replace("/", "\\")
        return "DIR"

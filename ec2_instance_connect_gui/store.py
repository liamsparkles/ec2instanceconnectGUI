"""Persist server entries as a JSON text file."""

from __future__ import annotations

import json
import os
import shutil
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class ServerEntry:
    label: str
    username: str
    instance_id: str

    def validate(self) -> None:
        if not self.label.strip():
            raise ValueError("Label is required.")
        if not self.username.strip():
            raise ValueError("Username is required.")
        if not self.instance_id.strip():
            raise ValueError("Instance ID is required.")
        iid = self.instance_id.strip()
        if not iid.startswith("i-") or len(iid) < 4:
            raise ValueError(
                "Instance ID should look like an EC2 id, e.g. i-0123456789abcdef0."
            )


def legacy_data_paths() -> List[Path]:
    """Previous default locations (project data/ or next to the built exe)."""
    paths: List[Path] = []
    package_root = Path(__file__).resolve().parent.parent
    paths.append(package_root / "data" / "servers.json")
    if getattr(sys, "frozen", False):
        paths.append(Path(sys.executable).resolve().parent / "data" / "servers.json")
    return paths


def migrate_legacy_data(target: Path) -> None:
    """Copy servers from a legacy path when the new location has no file yet."""
    if target.is_file():
        return
    for legacy in legacy_data_paths():
        if legacy == target or not legacy.is_file():
            continue
        if not legacy.read_text(encoding="utf-8").strip():
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(legacy, target)
        return


def default_data_path() -> Path:
    configured = load_data_directory()
    data_dir = configured if configured is not None else default_storage_dir()
    data_dir.mkdir(parents=True, exist_ok=True)
    path = data_dir / "servers.json"
    migrate_legacy_data(path)
    return path


def default_config_dir() -> Path:
    appdata = os.environ.get("APPDATA")
    if appdata:
        return Path(appdata) / "EC2InstanceConnectGUI"
    return Path.home() / ".ec2instanceconnectgui"


def settings_path() -> Path:
    return default_config_dir() / "settings.json"


def default_storage_dir() -> Path:
    return default_config_dir() / "data"


def load_data_directory() -> Optional[Path]:
    path = settings_path()
    if not path.is_file():
        return None
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return None
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        return None
    value = payload.get("data_directory")
    if not isinstance(value, str) or not value.strip():
        return None
    return Path(value).expanduser()


def save_data_directory(directory: Path) -> None:
    directory = directory.expanduser().resolve()
    settings = settings_path()
    settings.parent.mkdir(parents=True, exist_ok=True)
    payload = {"data_directory": str(directory)}
    settings.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


def load_servers(path: Path) -> List[ServerEntry]:
    if not path.is_file():
        return []
    raw = path.read_text(encoding="utf-8").strip()
    if not raw:
        return []
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("Invalid servers file: expected a JSON array.")
    out: List[ServerEntry] = []
    for item in data:
        if not isinstance(item, dict):
            continue
        out.append(
            ServerEntry(
                label=str(item.get("label", "")),
                username=str(item.get("username", "")),
                instance_id=str(item.get("instance_id", "")),
            )
        )
    return out


def save_servers(path: Path, servers: List[ServerEntry]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = [asdict(s) for s in servers]
    path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )

"""Persist server entries as a JSON text file."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List


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


def default_data_path() -> Path:
    root = Path(__file__).resolve().parent.parent
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "servers.json"


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

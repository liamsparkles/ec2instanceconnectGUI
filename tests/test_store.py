"""Tests for JSON persistence."""

from __future__ import annotations

from pathlib import Path

import ec2_instance_connect_gui.store as store_module
from ec2_instance_connect_gui.store import (
    ServerEntry,
    default_data_path,
    load_data_directory,
    load_servers,
    migrate_legacy_data,
    save_data_directory,
    save_servers,
)


def test_save_and_load_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "servers.json"
    entries = [
        ServerEntry("A", "ec2-user", "i-0aaaaaaaaaaaaaaaaa"),
        ServerEntry("B", "ubuntu", "i-0bbbbbbbbbbbbbbbbb"),
    ]
    save_servers(path, entries)
    loaded = load_servers(path)
    assert loaded == entries


def test_load_missing_file_returns_empty(tmp_path: Path) -> None:
    path = tmp_path / "missing.json"
    assert load_servers(path) == []


def test_save_and_load_data_directory(
    tmp_path: Path,
    monkeypatch,
) -> None:
    settings = tmp_path / "settings.json"
    monkeypatch.setattr(store_module, "settings_path", lambda: settings)
    target = tmp_path / "chosen"

    save_data_directory(target)
    loaded = load_data_directory()

    assert loaded == target.resolve()


def test_default_data_path_uses_config_dir(
    tmp_path: Path,
    monkeypatch,
) -> None:
    config_dir = tmp_path / "config"
    monkeypatch.setenv("APPDATA", str(config_dir))
    monkeypatch.setattr(store_module, "load_data_directory", lambda: None)

    path = default_data_path()

    assert path == config_dir / "EC2InstanceConnectGUI" / "data" / "servers.json"
    assert path.parent.is_dir()


def test_migrate_legacy_data_copies_existing_file(
    tmp_path: Path,
    monkeypatch,
) -> None:
    legacy = tmp_path / "old" / "servers.json"
    target = tmp_path / "new" / "servers.json"
    entries = [ServerEntry("A", "ec2-user", "i-0aaaaaaaaaaaaaaaaa")]
    save_servers(legacy, entries)
    monkeypatch.setattr(store_module, "legacy_data_paths", lambda: [legacy])

    migrate_legacy_data(target)

    assert load_servers(target) == entries
    assert legacy.is_file()

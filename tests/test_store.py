"""Tests for JSON persistence."""

from __future__ import annotations

from pathlib import Path

from ec2_instance_connect_gui.store import ServerEntry, load_servers, save_servers


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

"""Shared fixtures for GUI tests."""

from __future__ import annotations

import pytest
from pathlib import Path

from ec2_instance_connect_gui.main_window import MainWindow
from ec2_instance_connect_gui.store import ServerEntry, save_servers


@pytest.fixture
def servers_json_path(tmp_path: Path) -> Path:
    return tmp_path / "servers.json"


@pytest.fixture
def main_window(qtbot, servers_json_path: Path) -> MainWindow:
    w = MainWindow(servers_json_path)
    qtbot.addWidget(w)
    return w


@pytest.fixture
def main_window_with_server(qtbot, servers_json_path: Path) -> MainWindow:
    save_servers(
        servers_json_path,
        [ServerEntry("Test host", "ubuntu", "i-0123456789abcdef0")],
    )
    w = MainWindow(servers_json_path)
    qtbot.addWidget(w)
    return w

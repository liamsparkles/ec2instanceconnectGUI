"""Tests for MainWindow: add, edit, delete, connect."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox

import ec2_instance_connect_gui.main_window as main_window_module
from ec2_instance_connect_gui.main_window import MainWindow
from ec2_instance_connect_gui.store import ServerEntry, load_servers


def test_create_new_server_entry(qtbot, main_window: MainWindow, servers_json_path: Path) -> None:
    qtbot.mouseClick(main_window._btn_add, Qt.MouseButton.LeftButton)
    assert main_window._creating_new is True
    assert main_window._btn_add.isEnabled() is False

    main_window._label_edit.setText("My server")
    main_window._user_edit.setText("ec2-user")
    main_window._instance_edit.setText("i-0abc123456789abcd")
    qtbot.mouseClick(main_window._btn_save, Qt.MouseButton.LeftButton)

    assert main_window._list.count() == 1
    assert main_window._list.item(0).text() == "My server"
    assert main_window._label_edit.isEnabled() is False
    assert main_window._creating_new is False

    raw = json.loads(servers_json_path.read_text(encoding="utf-8"))
    assert raw == [
        {
            "label": "My server",
            "username": "ec2-user",
            "instance_id": "i-0abc123456789abcd",
        }
    ]
    assert load_servers(servers_json_path) == [
        ServerEntry("My server", "ec2-user", "i-0abc123456789abcd")
    ]


def test_edit_server(
    qtbot,
    main_window_with_server: MainWindow,
    servers_json_path: Path,
) -> None:
    assert main_window_with_server._list.currentRow() == 0
    assert main_window_with_server._label_edit.text() == "Test host"

    qtbot.mouseClick(main_window_with_server._btn_edit, Qt.MouseButton.LeftButton)
    assert main_window_with_server._editing is True
    main_window_with_server._label_edit.setText("Renamed host")
    main_window_with_server._user_edit.setText("ec2-user")
    qtbot.mouseClick(main_window_with_server._btn_save, Qt.MouseButton.LeftButton)

    assert main_window_with_server._list.item(0).text() == "Renamed host"
    assert main_window_with_server._editing is False
    assert main_window_with_server._label_edit.isEnabled() is False

    loaded = load_servers(servers_json_path)
    assert len(loaded) == 1
    assert loaded[0].label == "Renamed host"
    assert loaded[0].username == "ec2-user"
    assert loaded[0].instance_id == "i-0123456789abcdef0"


def test_delete_server(
    monkeypatch: pytest.MonkeyPatch,
    qtbot,
    main_window_with_server: MainWindow,
    servers_json_path: Path,
) -> None:
    monkeypatch.setattr(
        QMessageBox,
        "question",
        lambda *a, **k: QMessageBox.StandardButton.Yes,
    )

    qtbot.mouseClick(main_window_with_server._btn_delete, Qt.MouseButton.LeftButton)

    assert main_window_with_server._list.count() == 0
    assert servers_json_path.read_text(encoding="utf-8").strip() == "[]"


def test_connect_invokes_mssh(
    monkeypatch: pytest.MonkeyPatch,
    qtbot,
    main_window_with_server: MainWindow,
) -> None:
    calls: list[tuple[str, str]] = []

    def fake_open(instance_id: str, os_user: str) -> None:
        calls.append((instance_id, os_user))

    monkeypatch.setattr(main_window_module, "_open_ssh_session", fake_open)

    qtbot.mouseClick(main_window_with_server._btn_connect, Qt.MouseButton.LeftButton)

    assert calls == [("i-0123456789abcdef0", "ubuntu")]

"""Main application window."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path
from typing import List, Optional

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QIcon
from PyQt6.QtWidgets import (
    QApplication,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ec2_instance_connect_gui.store import (
    ServerEntry,
    default_data_path,
    load_servers,
    save_servers,
)


def _find_mssh() -> Optional[str]:
    """Resolve the mssh executable from PATH or next to the running interpreter."""
    found = shutil.which("mssh")
    if found:
        return found
    bin_dir = Path(sys.executable).resolve().parent
    for name in ("mssh.cmd", "mssh.exe", "mssh"):
        candidate = bin_dir / name
        if candidate.is_file():
            return str(candidate)
    return None


def _open_ssh_session(instance_id: str, os_user: str) -> None:
    """Start an interactive session via mssh (ec2instanceconnectcli) in a new terminal on Windows."""
    mssh = _find_mssh()
    if not mssh:
        raise FileNotFoundError(
            "mssh not found. Install the ec2instanceconnectcli package "
            "(pip install ec2instanceconnectcli) and run this app with the same Python environment."
        )
    user = os_user.strip()
    iid = instance_id.strip()
    target = f"{user}@{iid}"
    args = [mssh, target]
    if sys.platform == "win32":
        cmd = " ".join(_quote_win(a) for a in args)
        subprocess.Popen(
            ["cmd", "/c", "start", "cmd", "/k", cmd],
            cwd=str(Path.home()),
            shell=False,
        )
    else:
        subprocess.Popen(args, cwd=str(Path.home()))


def _quote_win(s: str) -> str:
    if any(c in s for c in ' \t"&|<>^'):
        return '"' + s.replace('"', '\\"') + '"'
    return s


def _project_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _assets_dir() -> Path:
    """Dev: project assets/. Frozen (PyInstaller): sys._MEIPASS/assets (bundle with --add-data)."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "assets"
    return _project_root() / "assets"


def _window_icon() -> QIcon:
    """Taskbar / window icon: prefer assets/logo.ico when present (bundled or dev)."""
    ico = _assets_dir() / "logo.ico"
    if ico.is_file():
        return QIcon(str(ico))
    if getattr(sys, "frozen", False) or hasattr(sys, "_MEIPASS"):
        return QIcon(sys.executable)
    return QIcon()


class MainWindow(QMainWindow):
    def __init__(self, data_path: Path) -> None:
        super().__init__()
        self._data_path = data_path
        self._servers: List[ServerEntry] = []
        self._current_index: Optional[int] = None
        self._creating_new: bool = False
        self._editing: bool = False

        self.setWindowTitle("EC2 Instance Connect")
        self.setMinimumSize(640, 420)
        self._build_ui()
        self._reload_list()

    def _build_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        splitter = QSplitter(Qt.Orientation.Horizontal)

        self._list = QListWidget()
        self._list.currentRowChanged.connect(self._on_row_changed)
        splitter.addWidget(self._list)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)

        form_group = QGroupBox("Server")
        form = QFormLayout(form_group)
        self._label_edit = QLineEdit()
        self._label_edit.setPlaceholderText("Display name")
        self._user_edit = QLineEdit()
        self._user_edit.setPlaceholderText("e.g. ec2-user, ubuntu, admin")
        self._instance_edit = QLineEdit()
        self._instance_edit.setPlaceholderText("e.g. i-0123456789abcdef0")
        form.addRow("Label:", self._label_edit)
        form.addRow("Username:", self._user_edit)
        form.addRow("Instance ID:", self._instance_edit)
        right_layout.addWidget(form_group)

        btn_row = QHBoxLayout()
        self._btn_add = QPushButton("Add new")
        self._btn_edit = QPushButton("Edit")
        self._btn_save = QPushButton("Save")
        self._btn_delete = QPushButton("Delete")
        self._btn_connect = QPushButton("Connect (SSH)")
        self._btn_add.clicked.connect(self._add_new)
        self._btn_edit.clicked.connect(self._edit_current)
        self._btn_save.clicked.connect(self._save_current)
        self._btn_delete.clicked.connect(self._delete_current)
        self._btn_connect.clicked.connect(self._connect_current)
        btn_row.addWidget(self._btn_add)
        btn_row.addWidget(self._btn_edit)
        btn_row.addWidget(self._btn_save)
        btn_row.addWidget(self._btn_delete)
        btn_row.addStretch()
        btn_row.addWidget(self._btn_connect)
        right_layout.addLayout(btn_row)

        hint = QLabel(
            "Connect runs mssh (from ec2instanceconnectcli), e.g. user@instance-id.\n"
            "Configure AWS credentials and region (e.g. AWS_REGION) as usual."
        )
        hint.setWordWrap(True)
        right_layout.addWidget(hint)

        right_layout.addStretch()
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        layout.addWidget(splitter)

        quit_action = QAction(self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        self.addAction(quit_action)

    def _set_fields_enabled(self, enabled: bool) -> None:
        self._label_edit.setEnabled(enabled)
        self._user_edit.setEnabled(enabled)
        self._instance_edit.setEnabled(enabled)

    def _sync_buttons(self) -> None:
        has_selection = self._current_index is not None
        self._btn_add.setEnabled(not self._creating_new)
        self._btn_edit.setEnabled(
            has_selection and not self._creating_new and not self._editing
        )
        self._btn_save.setEnabled(self._creating_new or self._editing)
        self._btn_delete.setEnabled(has_selection and not self._creating_new)
        self._btn_connect.setEnabled(
            has_selection and not self._creating_new and not self._editing
        )

    def _reload_list(self) -> None:
        try:
            self._servers = load_servers(self._data_path)
        except (OSError, ValueError) as e:
            QMessageBox.warning(self, "Load failed", str(e))
            self._servers = []
        self._list.clear()
        for s in self._servers:
            QListWidgetItem(s.label or "(no label)", self._list)
        self._creating_new = False
        self._editing = False
        if self._servers:
            self._list.setCurrentRow(0)
        else:
            self._clear_form()
            self._current_index = None
            self._set_fields_enabled(False)
            self._sync_buttons()

    def _on_row_changed(self, row: int) -> None:
        if row < 0:
            self._current_index = None
            if not self._creating_new:
                self._clear_form()
                self._set_fields_enabled(False)
                self._editing = False
            self._sync_buttons()
            return
        if row >= len(self._servers):
            self._current_index = None
            self._creating_new = False
            self._editing = False
            self._clear_form()
            self._set_fields_enabled(False)
            self._sync_buttons()
            return
        self._creating_new = False
        self._editing = False
        self._current_index = row
        s = self._servers[row]
        self._label_edit.setText(s.label)
        self._user_edit.setText(s.username)
        self._instance_edit.setText(s.instance_id)
        self._set_fields_enabled(False)
        self._sync_buttons()

    def _clear_form(self) -> None:
        self._label_edit.clear()
        self._user_edit.clear()
        self._instance_edit.clear()

    def _add_new(self) -> None:
        self._creating_new = True
        self._editing = False
        self._list.blockSignals(True)
        self._list.clearSelection()
        self._list.blockSignals(False)
        self._current_index = None
        self._clear_form()
        self._set_fields_enabled(True)
        self._label_edit.setFocus()
        self._sync_buttons()

    def _edit_current(self) -> None:
        if self._current_index is None:
            return
        self._editing = True
        self._set_fields_enabled(True)
        self._label_edit.setFocus()
        self._sync_buttons()

    def _save_current(self) -> None:
        entry = ServerEntry(
            label=self._label_edit.text(),
            username=self._user_edit.text(),
            instance_id=self._instance_edit.text(),
        )
        try:
            entry.validate()
        except ValueError as e:
            QMessageBox.warning(self, "Invalid entry", str(e))
            return
        if self._current_index is None:
            self._servers.append(entry)
            self._list.addItem(QListWidgetItem(entry.label))
            self._creating_new = False
            self._editing = False
            self._list.setCurrentRow(len(self._servers) - 1)
        else:
            self._servers[self._current_index] = entry
            item = self._list.item(self._current_index)
            if item:
                item.setText(entry.label)
            self._editing = False
            self._set_fields_enabled(False)
        self._persist()
        self._sync_buttons()

    def _delete_current(self) -> None:
        if self._current_index is None:
            QMessageBox.information(self, "Delete", "Select a server to delete.")
            return
        row = self._current_index
        reply = QMessageBox.question(
            self,
            "Delete server",
            "Remove this server from the saved list?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        del self._servers[row]
        self._list.takeItem(row)
        self._persist()
        self._editing = False
        if self._servers:
            new_row = min(row, len(self._servers) - 1)
            self._list.setCurrentRow(new_row)
        else:
            self._clear_form()
            self._current_index = None
            self._set_fields_enabled(False)
            self._sync_buttons()

    def _connect_current(self) -> None:
        if self._current_index is None:
            QMessageBox.information(
                self, "Connect", "Select a saved server or fill the form and save first."
            )
            return
        s = self._servers[self._current_index]
        try:
            s.validate()
        except ValueError as e:
            QMessageBox.warning(self, "Invalid entry", str(e))
            return
        try:
            _open_ssh_session(s.instance_id, s.username)
        except FileNotFoundError as e:
            QMessageBox.warning(self, "Connect", str(e))
        except OSError as e:
            QMessageBox.critical(self, "Connect failed", str(e))

    def _persist(self) -> None:
        try:
            save_servers(self._data_path, self._servers)
        except OSError as e:
            QMessageBox.critical(self, "Save failed", str(e))


def run_app(data_path: Optional[Path] = None) -> int:
    app = QApplication(sys.argv)
    icon = _window_icon()
    if not icon.isNull():
        app.setWindowIcon(icon)
    path = data_path or default_data_path()
    w = MainWindow(path)
    if not icon.isNull():
        w.setWindowIcon(icon)
    w.show()
    return app.exec()

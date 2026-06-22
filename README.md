# EC2 Instance Connect GUI

A small desktop app (PyQt6) to save EC2 Instance Connect targets (label, username, instance ID) and open a session with `**mssh**` from [ec2instanceconnectcli](https://pypi.org/project/ec2instanceconnectcli/).

This application is almost fully vibe coded, it is a simple program that I just needed to accomplish a task and I didn't want to waste much time on it.

## Prerequisites

- **Python** 3.10 or newer (64-bit recommended on Windows)
- **Git** (optional), to clone the repository

## Setup

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate
pip install -r requirements.txt
```

On macOS/Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

With the virtual environment activated:

```powershell
python main.py
```

Alternatively:

```powershell
python -m ec2_instance_connect_gui
```

Saved servers are stored in a writable user location by default:

- Windows: `%APPDATA%\EC2InstanceConnectGUI\data\servers.json`
- Other OSes: `~/.ec2instanceconnectgui/data/servers.json`

### Change where data is saved

Use `File -> Change data directory...` in the app and pick a folder.

- The app stores all server entries in `<chosen folder>/servers.json`.
- The chosen directory path is persisted in:
  - Windows: `%APPDATA%\EC2InstanceConnectGUI\settings.json`
  - Other OSes: `~/.ec2instanceconnectgui/settings.json`
- On startup, the app reads that setting and keeps using the same folder until you change it again.
- The current data file path is shown in the status bar at the bottom of the window.
- If you previously used the old default (`data/servers.json` in the project or next to the executable), the app copies that file into the new location on first run.

### Connect (SSH)

The **Connect** action runs `**mssh`** (installed with `ec2instanceconnectcli`). Configure AWS credentials and region as you normally would (for example `**AWS_REGION**` or your default profile) so Instance Connect can reach the instance.

## Tests (optional)

Install dev dependencies and run **pytest**:

```powershell
pip install -r requirements-dev.txt
pytest
```

## Build a Windows executable (PyInstaller)

Install PyInstaller in the same environment you use to run the app:

```powershell
pip install pyinstaller
```

The repo includes `**main.spec**`, which bundles the `**assets**` folder (icons) and builds a single windowed executable.

```powershell
pyinstaller --clean --noconfirm main.spec
```

The output is `**dist\EC2InstanceConnect.exe**`.

### Command-line equivalent (no spec file)

If you prefer not to use the spec file:

```powershell
pyinstaller --onefile --windowed --name EC2InstanceConnect --icon=assets\logo.ico --add-data "assets;assets" main.py
```

On Windows, `**--add-data**` uses the form `**source;destination_inside_the_bundle**`. The app loads resources from `**sys._MEIPASS\assets**` at runtime; omitting `**--add-data**` will break icons bundled under `**assets/**`.
Rebuild after changing dependencies or `**main.spec**` with `**--clean**` if you see stale behavior.
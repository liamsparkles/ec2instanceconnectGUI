"""Entry point for the EC2 Instance Connect GUI."""

from __future__ import annotations

import sys

from ec2_instance_connect_gui.main_window import run_app


if __name__ == "__main__":
    sys.exit(run_app())

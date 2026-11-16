#!/usr/bin/env python3
"""
PlasmaTahoe-Engine: Plasma 6 Layout Script Orchestrator
Executes the JavaScript panel & dock configuration through the PlasmaShell D-Bus interface.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, Optional

from core.config import EngineConfig


class PlasmaLayoutManager:
    """Applies macOS Tahoe top panel and floating dock layouts via QDBus."""

    def __init__(self, config: EngineConfig) -> None:
        self.config = config
        self.template_path = Path(__file__).parent / "plasma_layout.js"

    def generate_script(self) -> str:
        """Read template and interpolate geometry settings."""
        if not self.template_path.exists():
            raise FileNotFoundError(f"Missing layout template: {self.template_path}")

        with open(self.template_path, "r", encoding="utf-8") as f:
            content = f.read()

        content = content.replace("__TOP_PANEL_HEIGHT__", str(self.config.components.top_panel_height))
        content = content.replace("__DOCK_HEIGHT__", str(self.config.components.dock_height))
        return content

    def apply_layout(self, log_cb: Optional[Callable[[str, str], None]] = None) -> bool:
        """
        Send generated JavaScript to PlasmaShell evaluateScript D-Bus method.
        """
        if log_cb:
            log_cb("Deploying macOS Tahoe Top Panel and Floating Dock layout...", "INFO")

        script_code = self.generate_script()

        if self.config.dry_run:
            if log_cb:
                log_cb("[DRY-RUN] Script generation verified. Skipping live PlasmaShell D-Bus invocation.", "INFO")
            return True

        # Find D-Bus executable (strictly qdbus6 for Plasma 6)
        qdbus_bin = shutil.which("qdbus6")
        if not qdbus_bin:
            if log_cb:
                log_cb("qdbus6 not found on system. Writing layout script to cache for manual execution.", "WARN")
            dest = self.config.cache_dir / "generated_layout.js"
            try:
                dest.parent.mkdir(parents=True, exist_ok=True)
                with open(dest, "w", encoding="utf-8") as f:
                    f.write(script_code)
            except Exception:
                pass
            return True

        # Execute script via DBus
        cmd = [
            qdbus_bin,
            "org.kde.plasmashell",
            "/PlasmaShell",
            "org.kde.PlasmaShell.evaluateScript",
            script_code,
        ]

        try:
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            if res.returncode == 0:
                if log_cb:
                    log_cb("Plasma 6 layout applied successfully via D-Bus.", "SUCCESS")
                return True
            else:
                if log_cb:
                    log_cb(f"PlasmaShell evaluateScript returned: {res.stderr.strip() or res.stdout.strip()}", "WARN")
                return False
        except Exception as e:
            if log_cb:
                log_cb(f"Error evaluating layout script: {e}", "ERROR")
            return False

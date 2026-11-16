#!/usr/bin/env python3
"""
PlasmaTahoe-Engine: Atomic Snapshot Backup & Rollback Manager
Creates pre-flight backups of KDE Plasma configurations and provides 1-click restore.
Archives files into ~/.local/share/plasmatahoe/backups/ with a full manifest.
"""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import tarfile
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, List, Optional


@dataclass
class BackupInfo:
    """Metadata describing a saved configuration snapshot."""
    archive_path: Path
    timestamp: str
    formatted_date: str
    size_bytes: int
    files_count: int
    manifest_data: Dict[str, any]

    @property
    def size_human(self) -> str:
        kb = self.size_bytes / 1024
        if kb < 1024:
            return f"{kb:.1f} KB"
        return f"{kb / 1024:.2f} MB"


class BackupManager:
    """Manages atomic backups and rollbacks of KDE configurations."""

    # Target configuration files and directories relative to ~/.config
    CONFIG_TARGETS = [
        "kdeglobals",
        "kwinrc",
        "plasmarc",
        "dolphinrc",
        "krunnerrc",
        "kglobalshortcutsrc",
        "plasma-org.kde.plasma.desktop-appletsrc",
        "Kvantum",
    ]

    def __init__(self, backup_dir: Optional[Path] = None, home_dir: Optional[Path] = None) -> None:
        self.home_dir = home_dir or Path.home()
        xdg_config = os.environ.get("XDG_CONFIG_HOME")
        self.config_dir = Path(xdg_config).resolve() if xdg_config else (self.home_dir / ".config")
        xdg_data = os.environ.get("XDG_DATA_HOME")
        default_backup_dir = (
            Path(xdg_data).resolve() if xdg_data else (self.home_dir / ".local" / "share")
        ) / "plasmatahoe" / "backups"
        self.backup_dir = backup_dir or default_backup_dir
        self.backup_dir.mkdir(parents=True, exist_ok=True)

    def _calculate_sha256(self, file_path: Path) -> str:
        """Compute SHA256 checksum of a file."""
        sha = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                sha.update(chunk)
        return sha.hexdigest()

    def _get_installed_plasmoids(self) -> List[str]:
        """List currently installed user plasmoids."""
        plasmoids_dir = self.home_dir / ".local" / "share" / "plasma" / "plasmoids"
        if not plasmoids_dir.exists():
            return []
        return [d.name for d in plasmoids_dir.iterdir() if d.is_dir()]

    def create_backup(self, log_cb: Optional[Callable[[str, str], None]] = None) -> Optional[Path]:
        """
        Create a timestamped compressed tarball of existing KDE configs.
        Returns the path to the created archive or None if failed.
        """
        now = datetime.now()
        timestamp_str = now.strftime("%Y%m%d_%H%M%S")
        archive_name = f"backup_{timestamp_str}.tar.gz"
        archive_path = self.backup_dir / archive_name

        if log_cb:
            log_cb(f"Initiating pre-flight atomic backup: {archive_name}", "INFO")

        existing_backups = list(self.backup_dir.glob("backup_*.tar.gz"))
        is_baseline = len(existing_backups) == 0

        manifest: Dict[str, any] = {
            "timestamp": now.isoformat(),
            "formatted_date": now.strftime("%b %d, %Y %I:%M:%S %p"),
            "is_baseline": is_baseline,
            "files": {},
            "installed_plasmoids": self._get_installed_plasmoids(),
            "os_release": {},
        }

        # Record os-release if available
        os_release = Path("/etc/os-release")
        if os_release.exists():
            try:
                with open(os_release, "r", encoding="utf-8") as f:
                    manifest["os_release"] = dict(line.strip().split("=", 1) for line in f if "=" in line)
            except Exception:
                pass

        try:
            # Temporary staging directory for manifest and files
            with tarfile.open(archive_path, "w:gz") as tar:
                backed_up_count = 0

                for target_rel in self.CONFIG_TARGETS:
                    target_path = self.config_dir / target_rel
                    if target_path.exists():
                        if target_path.is_file():
                            tar.add(target_path, arcname=f"config/{target_rel}")
                            manifest["files"][target_rel] = {
                                "type": "file",
                                "sha256": self._calculate_sha256(target_path),
                                "size": target_path.stat().st_size,
                            }
                            backed_up_count += 1
                        elif target_path.is_dir():
                            tar.add(target_path, arcname=f"config/{target_rel}")
                            manifest["files"][target_rel] = {
                                "type": "dir",
                                "item_count": len(list(target_path.rglob("*"))),
                            }
                            backed_up_count += 1

                # Write manifest JSON into tar archive
                manifest_json = json.dumps(manifest, indent=2).encode("utf-8")
                tarinfo = tarfile.TarInfo(name="manifest.json")
                tarinfo.size = len(manifest_json)
                tarinfo.mtime = int(time.time())
                from io import BytesIO
                tar.addfile(tarinfo, BytesIO(manifest_json))

            # Also save manifest.json alongside the archive for quick indexing
            sidecar_manifest = archive_path.with_suffix(".json")
            with open(sidecar_manifest, "w", encoding="utf-8") as f:
                json.dump(manifest, f, indent=2)

            if log_cb:
                log_cb(
                    f"Backup completed ({backed_up_count} configuration items archived: {archive_path.name})",
                    "SUCCESS",
                )
            return archive_path

        except Exception as e:
            if log_cb:
                log_cb(f"Failed to create backup: {str(e)}", "ERROR")
            if archive_path.exists():
                archive_path.unlink()
            return None

    def list_backups(self) -> List[BackupInfo]:
        """List all available backups ordered by date (newest first)."""
        backups: List[BackupInfo] = []
        for arc in sorted(self.backup_dir.glob("backup_*.tar.gz"), reverse=True):
            try:
                manifest_data: Dict[str, any] = {}
                sidecar = arc.with_suffix(".json")

                if sidecar.exists():
                    try:
                        with open(sidecar, "r", encoding="utf-8") as f:
                            manifest_data = json.load(f)
                    except Exception:
                        pass

                if not manifest_data and tarfile.is_tarfile(arc):
                    with tarfile.open(arc, "r:gz") as tar:
                        try:
                            f = tar.extractfile("manifest.json")
                            if f:
                                manifest_data = json.load(f)
                        except Exception:
                            pass

                ts = arc.stem.replace("backup_", "").replace(".tar", "")
                dt_str = manifest_data.get("formatted_date", ts)
                files_count = len(manifest_data.get("files", {}))

                backups.append(
                    BackupInfo(
                        archive_path=arc,
                        timestamp=ts,
                        formatted_date=dt_str,
                        size_bytes=arc.stat().st_size,
                        files_count=files_count,
                        manifest_data=manifest_data,
                    )
                )
            except Exception:
                continue

        return backups

    def restore_backup(
        self,
        archive_path: Path,
        log_cb: Optional[Callable[[str, str], None]] = None,
        dry_run: bool = False,
    ) -> bool:
        """
        Restore configuration files from archive and restart Plasma shell & KWin.
        """
        if not archive_path.exists() or not tarfile.is_tarfile(archive_path):
            if log_cb:
                log_cb(f"Invalid or missing backup archive: {archive_path}", "ERROR")
            return False

        if log_cb:
            log_cb(f"Restoring configuration from snapshot: {archive_path.name}", "INFO")

        if dry_run:
            if log_cb:
                log_cb(f"[DRY-RUN] Would extract {archive_path} to {self.config_dir}", "INFO")
                log_cb("[DRY-RUN] Would reload KWin and restart plasmashell via qdbus6", "INFO")
            return True

        try:
            with tarfile.open(archive_path, "r:gz") as tar:
                resolved_config = self.config_dir.resolve()
                for member in tar.getmembers():
                    if member.name.startswith("config/"):
                        rel_path = member.name[len("config/") :].strip("/")
                        if not rel_path:
                            continue

                        dest = (self.config_dir / rel_path).resolve()
                        # Path traversal protection
                        try:
                            dest.relative_to(resolved_config)
                        except ValueError:
                            if log_cb:
                                log_cb(f"Security: skipped archive entry outside config dir: {member.name}", "WARN")
                            continue

                        if member.isdir():
                            dest.mkdir(parents=True, exist_ok=True)
                            os.chmod(dest, member.mode)
                        elif member.issym():
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            if dest.is_symlink() or dest.exists():
                                dest.unlink()
                            os.symlink(member.linkname, dest)
                        else:
                            dest.parent.mkdir(parents=True, exist_ok=True)
                            source = tar.extractfile(member)
                            if source:
                                with open(dest, "wb") as f:
                                    f.write(source.read())
                                os.chmod(dest, member.mode)

            if log_cb:
                log_cb("Configuration files restored. Reloading KDE Plasma...", "INFO")

            self.restart_kde_services(log_cb)

            if log_cb:
                log_cb("Snapshot restored successfully!", "SUCCESS")
            return True

        except Exception as e:
            if log_cb:
                log_cb(f"Error during rollback: {str(e)}", "ERROR")
            return False

    def restart_kde_services(self, log_cb: Optional[Callable[[str, str], None]] = None) -> None:
        """Gracefully reload PlasmaShell and reconfigure KWin."""
        # 1. Reconfigure KWin (strictly Plasma 6 qdbus6)
        if shutil.which("qdbus6"):
            try:
                subprocess.run(
                    ["qdbus6", "org.kde.KWin", "/KWin", "reconfigure"],
                    capture_output=True,
                    timeout=5,
                )
            except Exception:
                pass

        # 2. Restart Plasmashell gracefully
        reloaded = False
        if shutil.which("kquitapp6"):
            try:
                subprocess.run(["kquitapp6", "plasmashell"], capture_output=True, timeout=5)
                time.sleep(1)
            except Exception:
                pass
        else:
            try:
                subprocess.run(["killall", "-15", "plasmashell"], capture_output=True, timeout=3)
                time.sleep(1)
            except Exception:
                pass

        # Relaunch plasmashell in background
        try:
            if shutil.which("kstart6"):
                subprocess.Popen(["kstart6", "plasmashell"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                reloaded = True
            elif shutil.which("plasmashell"):
                subprocess.Popen(
                    ["plasmashell"],
                    start_new_session=True,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
                reloaded = True
        except Exception as e:
            if log_cb:
                log_cb(f"Notice: Could not auto-launch plasmashell ({e}). You may need to restart the session.", "WARN")

        if reloaded and log_cb:
            log_cb("KDE Plasma shell restarted.", "INFO")

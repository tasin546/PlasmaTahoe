#!/usr/bin/env python3
"""
PlasmaTahoe-Engine: Upstream Git Repository Orchestrator
Fetches, updates, builds, and installs upstream open-source KDE/GTK components.
Maintains licenses, handles fallbacks, and executes builds in worker threads.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional

from core.config import EngineConfig, PerformanceProfile, ThemeMode


@dataclass
class RepoDefinition:
    """Definition of an upstream repository with primary and fallback sources."""
    name: str
    primary_url: str
    primary_branch: str
    fallback_url: Optional[str] = None
    fallback_branch: Optional[str] = None
    description: str = ""


class GitRepoManager:
    """Manages cloning, updating, and building open-source repositories."""

    REPOS: Dict[str, RepoDefinition] = {
        "mactahoe_kde": RepoDefinition(
            name="mactahoe_kde",
            primary_url="https://github.com/vinceliuice/MacTahoe-kde.git",
            primary_branch="main",
            fallback_url="https://github.com/vinceliuice/WhiteSur-kde.git",
            fallback_branch="master",
            description="KDE Plasma theme, Kvantum style, and Aurorae window decorations",
        ),
        "mactahoe_gtk": RepoDefinition(
            name="mactahoe_gtk",
            primary_url="https://github.com/vinceliuice/MacTahoe-gtk-theme.git",
            primary_branch="main",
            fallback_url="https://github.com/vinceliuice/WhiteSur-gtk-theme.git",
            fallback_branch="master",
            description="GTK3/4 and Libadwaita application theme consistency",
        ),
        "mactahoe_icons": RepoDefinition(
            name="mactahoe_icons",
            primary_url="https://github.com/vinceliuice/MacTahoe-icon-theme.git",
            primary_branch="main",
            fallback_url="https://github.com/vinceliuice/WhiteSur-icon-theme.git",
            fallback_branch="master",
            description="macOS Tahoe squircle icons and cursor themes",
        ),
        "whitesur_cursors": RepoDefinition(
            name="whitesur_cursors",
            primary_url="https://github.com/vinceliuice/WhiteSur-cursors.git",
            primary_branch="master",
            description="High-DPI macOS cursor theme",
        ),
        "liquidglass_widgets": RepoDefinition(
            name="liquidglass_widgets",
            primary_url="https://github.com/jaxparrow07/liquidglass-kde-widgets.git",
            primary_branch="master",
            description="Frosted liquid glass QML plasmoids (Calendar, Clock, Music, Weather)",
        ),
        "kpple_menu": RepoDefinition(
            name="kpple_menu",
            primary_url="https://github.com/ChrTall/kppleMenu.git",
            primary_branch="main",
            fallback_url="https://github.com/kppleos/org.kpple.kppleMenu.git",
            fallback_branch="main",
            description="macOS-styled application launcher menu for Plasma 6",
        ),
        "panel_colorizer": RepoDefinition(
            name="panel_colorizer",
            primary_url="https://github.com/luisbocanegra/plasma-panel-colorizer.git",
            primary_branch="main",
            description="Dynamic widget island margins and panel background styling",
        ),
        "better_blur": RepoDefinition(
            name="better_blur",
            primary_url="https://github.com/xarblu/kwin-effects-better-blur-dx.git",
            primary_branch="main",
            fallback_url="https://github.com/slynobody/kwin-effects-better-blur-dx-plus.git",
            fallback_branch="master",
            description="KWin C++ Better Blur DX shader effect with glass refraction",
        ),
        "rounded_corners": RepoDefinition(
            name="rounded_corners",
            primary_url="https://github.com/matinlotfali/KDE-Rounded-Corners.git",
            primary_branch="master",
            description="KWin C++ Rounded Corners effect with anti-aliasing",
        ),
    }

    def __init__(self, config: EngineConfig) -> None:
        self.config = config
        self.repos_dir = config.cache_dir / "repos"
        self.repos_dir.mkdir(parents=True, exist_ok=True)

    def _run_cmd(
        self,
        cmd: List[str],
        cwd: Optional[Path] = None,
        log_cb: Optional[Callable[[str, str], None]] = None,
    ) -> bool:
        """Run a command with live streaming output to log_cb."""
        cmd_str = " ".join(cmd)
        if log_cb:
            log_cb(f"$ {cmd_str}", "DEBUG")

        try:
            proc = subprocess.Popen(
                cmd,
                cwd=str(cwd) if cwd else None,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            if proc.stdout:
                for line in iter(proc.stdout.readline, ""):
                    clean = line.strip()
                    if clean and log_cb:
                        log_cb(clean, "INFO")

            proc.wait()
            return proc.returncode == 0
        except Exception as e:
            if log_cb:
                log_cb(f"Command execution failed: {e}", "ERROR")
            return False

    def clone_or_update(
        self,
        repo_key: str,
        log_cb: Optional[Callable[[str, str], None]] = None,
    ) -> Optional[Path]:
        """Clone or pull an upstream repository, trying primary then fallback."""
        if repo_key not in self.REPOS:
            if log_cb:
                log_cb(f"Unknown repository key: {repo_key}", "ERROR")
            return None

        defn = self.REPOS[repo_key]
        target_path = self.repos_dir / defn.name

        if self.config.dry_run:
            if log_cb:
                log_cb(f"[DRY-RUN] Would fetch {defn.name} ({defn.primary_url}) to {target_path}", "INFO")
            return target_path

        if log_cb:
            log_cb(f"Preparing upstream repository: {defn.name} ({defn.description})", "INFO")

        # If repo exists, attempt to pull updates
        if target_path.exists() and (target_path / ".git").exists():
            if log_cb:
                log_cb(f"Updating existing repository at {target_path.name}...", "INFO")
            if self._run_cmd(["git", "pull", "--ff-only"], cwd=target_path, log_cb=log_cb):
                return target_path
            else:
                if log_cb:
                    log_cb("git pull failed, cleaning directory for fresh clone...", "WARN")
                shutil.rmtree(target_path, ignore_errors=True)

        # Clone primary URL
        if log_cb:
            log_cb(f"Cloning from primary: {defn.primary_url} (branch: {defn.primary_branch})...", "INFO")
        clone_cmd = [
            "git", "clone", "--depth", "1",
            "--branch", defn.primary_branch,
            defn.primary_url, str(target_path)
        ]
        if self._run_cmd(clone_cmd, log_cb=log_cb):
            return target_path

        # If primary failed and fallback exists, try fallback
        if defn.fallback_url:
            if log_cb:
                log_cb(f"Primary clone failed. Trying fallback: {defn.fallback_url}...", "WARN")
            shutil.rmtree(target_path, ignore_errors=True)
            fb_branch = defn.fallback_branch or "master"
            fb_cmd = [
                "git", "clone", "--depth", "1",
                "--branch", fb_branch,
                defn.fallback_url, str(target_path)
            ]
            if self._run_cmd(fb_cmd, log_cb=log_cb):
                return target_path

        if target_path.exists():
            shutil.rmtree(target_path, ignore_errors=True)
        if log_cb:
            log_cb(f"Failed to clone repository: {defn.name}", "ERROR")
        return None

    def install_kde_theme(
        self,
        repo_path: Path,
        mode: ThemeMode,
        profile: PerformanceProfile,
        log_cb: Optional[Callable[[str, str], None]] = None,
    ) -> bool:
        """Run MacTahoe-kde install.sh."""
        if self.config.dry_run:
            if log_cb:
                log_cb(f"[DRY-RUN] Would execute MacTahoe-kde install.sh with mode={mode.value}", "INFO")
            return True

        install_script = repo_path / "install.sh"
        if not install_script.exists():
            if log_cb:
                log_cb("install.sh not found in MacTahoe-kde repo", "ERROR")
            return False

        # Make executable
        install_script.chmod(0o755)

        cmd = [str(install_script), "-d", str(self.config.home_dir)]
        if mode == ThemeMode.DARK:
            cmd.extend(["-c", "dark"])
        elif mode == ThemeMode.LIGHT:
            cmd.extend(["-c", "light"])
        # Else both installed

        if log_cb:
            log_cb(f"Installing KDE Plasma & Kvantum themes: {' '.join(cmd)}", "INFO")
        return self._run_cmd(cmd, cwd=repo_path, log_cb=log_cb)

    def install_gtk_theme(
        self,
        repo_path: Path,
        mode: ThemeMode,
        profile: PerformanceProfile,
        log_cb: Optional[Callable[[str, str], None]] = None,
    ) -> bool:
        """Run MacTahoe-gtk-theme install.sh."""
        if self.config.dry_run:
            if log_cb:
                log_cb(f"[DRY-RUN] Would execute MacTahoe-gtk-theme install.sh with profile={profile.value}", "INFO")
            return True

        install_script = repo_path / "install.sh"
        if not install_script.exists():
            if log_cb:
                log_cb("install.sh not found in MacTahoe-gtk-theme repo", "ERROR")
            return False

        install_script.chmod(0o755)

        dest_dir = self.config.themes_dir
        dest_dir.mkdir(parents=True, exist_ok=True)

        cmd = [str(install_script), "-d", str(dest_dir), "-l"]

        if mode == ThemeMode.DARK:
            cmd.extend(["-c", "dark"])
        elif mode == ThemeMode.LIGHT:
            cmd.extend(["-c", "light"])

        # Opacity and blur settings based on GPU mode
        if profile == PerformanceProfile.FULL_LIQUID_GLASS:
            cmd.extend(["-o", "normal", "-b"])
        else:
            cmd.extend(["-o", "solid"])

        if log_cb:
            log_cb(f"Installing GTK / Libadwaita theme: {' '.join(cmd)}", "INFO")
        return self._run_cmd(cmd, cwd=repo_path, log_cb=log_cb)

    def install_icons_and_cursors(
        self,
        icons_repo: Path,
        cursors_repo: Optional[Path] = None,
        log_cb: Optional[Callable[[str, str], None]] = None,
    ) -> bool:
        """Install MacTahoe icons and cursors."""
        if self.config.dry_run:
            if log_cb:
                log_cb("[DRY-RUN] Would install MacTahoe icons and cursors", "INFO")
            return True

        dest_icons = self.config.icons_dir
        dest_icons.mkdir(parents=True, exist_ok=True)

        # 1. Icons
        icon_script = icons_repo / "install.sh"
        if icon_script.exists():
            icon_script.chmod(0o755)
            cmd = [str(icon_script), "-d", str(dest_icons)]
            if log_cb:
                log_cb("Installing MacTahoe icons...", "INFO")
            self._run_cmd(cmd, cwd=icons_repo, log_cb=log_cb)

        # 2. Cursors: first inspect if included in icons_repo/cursors
        cursor_script = icons_repo / "cursors" / "install.sh"
        if cursor_script.exists():
            cursor_script.chmod(0o755)
            if log_cb:
                log_cb("Installing MacTahoe cursors from icon package...", "INFO")
            self._run_cmd([str(cursor_script)], cwd=icons_repo / "cursors", log_cb=log_cb)
        elif cursors_repo:
            ws_cursor_script = cursors_repo / "install.sh"
            if ws_cursor_script.exists():
                ws_cursor_script.chmod(0o755)
                if log_cb:
                    log_cb("Installing WhiteSur cursors...", "INFO")
                self._run_cmd([str(ws_cursor_script)], cwd=cursors_repo, log_cb=log_cb)

        return True

    def install_liquidglass_widgets(
        self,
        widgets_repo: Path,
        log_cb: Optional[Callable[[str, str], None]] = None,
    ) -> bool:
        """
        Install Liquid Glass QML plasmoid widgets.
        Copies packages to ~/.local/share/plasma/plasmoids/ and registers them.
        """
        if self.config.dry_run:
            if log_cb:
                log_cb("[DRY-RUN] Would install Liquid Glass QML plasmoids into ~/.local/share/plasma/plasmoids", "INFO")
            return True

        packages_dir = widgets_repo / "packages"
        if not packages_dir.exists():
            if log_cb:
                log_cb("No packages directory in liquidglass repo", "ERROR")
            return False

        plasmoids_dir = self.config.plasmoids_dir
        plasmoids_dir.mkdir(parents=True, exist_ok=True)

        installed_count = 0
        for pkg in packages_dir.iterdir():
            if not pkg.is_dir() or pkg.name.startswith("test-"):
                continue

            metadata_file = pkg / "metadata.json"
            if not metadata_file.exists():
                continue

            try:
                with open(metadata_file, "r", encoding="utf-8") as f:
                    meta = json.load(f)
                plugin_id = meta.get("KPlugin", {}).get("Id")
                if not plugin_id:
                    continue

                dest_applet = plasmoids_dir / plugin_id
                shutil.rmtree(dest_applet, ignore_errors=True)
                shutil.copytree(pkg, dest_applet)

                # Try registering with kpackagetool6 if available
                if shutil.which("kpackagetool6"):
                    subprocess.run(
                        ["kpackagetool6", "--type=Plasma/Applet", "-u", str(dest_applet)],
                        capture_output=True,
                    )

                if log_cb:
                    log_cb(f"Installed widget: {meta.get('KPlugin', {}).get('Name', pkg.name)} ({plugin_id})", "INFO")
                installed_count += 1
            except Exception as e:
                if log_cb:
                    log_cb(f"Warning: Failed to copy widget {pkg.name}: {e}", "WARN")

        if log_cb:
            log_cb(f"Liquid Glass widgets deployed: {installed_count} applets active.", "SUCCESS")
        return installed_count > 0

    def install_extra_widget(
        self,
        repo_path: Path,
        widget_id: str,
        log_cb: Optional[Callable[[str, str], None]] = None,
    ) -> bool:
        """Install a standalone widget repo (e.g. kppleMenu or panel-colorizer)."""
        if self.config.dry_run:
            if log_cb:
                log_cb(f"[DRY-RUN] Would deploy standalone widget: {widget_id}", "INFO")
            return True

        plasmoids_dir = self.config.plasmoids_dir
        plasmoids_dir.mkdir(parents=True, exist_ok=True)
        dest = plasmoids_dir / widget_id

        # Check if the repo has a 'package' subfolder or root is the package
        source_dir = repo_path
        if (repo_path / "package" / "metadata.json").exists():
            source_dir = repo_path / "package"

        try:
            shutil.rmtree(dest, ignore_errors=True)
            shutil.copytree(source_dir, dest)

            if shutil.which("kpackagetool6"):
                subprocess.run(
                    ["kpackagetool6", "--type=Plasma/Applet", "-i", str(dest)],
                    capture_output=True,
                )

            if log_cb:
                log_cb(f"Installed additional widget: {widget_id}", "INFO")
            return True
        except Exception as e:
            if log_cb:
                log_cb(f"Failed to install widget {widget_id}: {e}", "WARN")
            return False

    def build_and_install_kwin_effect(
        self,
        repo_path: Path,
        effect_name: str,
        log_cb: Optional[Callable[[str, str], None]] = None,
    ) -> bool:
        """
        Compile and install a C++ KWin shader effect using CMake.
        Falls back gracefully if dev packages are missing.
        """
        if self.config.dry_run:
            if log_cb:
                log_cb(f"[DRY-RUN] Would compile and install KWin shader effect: {effect_name}", "INFO")
            return True

        if not shutil.which("cmake"):
            if log_cb:
                log_cb(f"CMake not found, skipping C++ compilation for {effect_name}", "WARN")
            return False

        build_dir = repo_path / "build"
        shutil.rmtree(build_dir, ignore_errors=True)
        build_dir.mkdir(parents=True, exist_ok=True)

        if log_cb:
            log_cb(f"Configuring CMake for {effect_name}...", "INFO")

        # Configure
        cmake_cfg = [
            "cmake",
            "-B", "build",
            "-S", ".",
            "-DCMAKE_BUILD_TYPE=Release",
            "-DCMAKE_INSTALL_PREFIX=/usr"
        ]
        if not self._run_cmd(cmake_cfg, cwd=repo_path, log_cb=log_cb):
            if log_cb:
                log_cb(f"CMake configuration failed for {effect_name}. Host may lack KWin development headers.", "WARN")
            return False

        # Build
        nproc = str(os.cpu_count() or 2)
        if log_cb:
            log_cb(f"Compiling {effect_name} with {nproc} threads...", "INFO")
        build_cmd = ["cmake", "--build", "build", f"-j{nproc}"]
        if not self._run_cmd(build_cmd, cwd=repo_path, log_cb=log_cb):
            if log_cb:
                log_cb(f"Build failed for {effect_name}", "WARN")
            return False

        # Install using pkexec or sudo
        auth = "pkexec" if shutil.which("pkexec") else "sudo"
        install_cmd = [auth, "cmake", "--install", "build"]
        if log_cb:
            log_cb(f"Installing {effect_name} to system plugins directory...", "INFO")
        success = self._run_cmd(install_cmd, cwd=repo_path, log_cb=log_cb)
        if success and log_cb:
            log_cb(f"Successfully compiled and installed {effect_name}!", "SUCCESS")
        return success

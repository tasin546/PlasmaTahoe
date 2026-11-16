#!/usr/bin/env python3
"""
PlasmaTahoe-Engine: Central Execution Pipeline Orchestrator
Coordinates pre-flight checks, atomic backups, git cloning, package installation,
shader compilation, KDE Plasma configuration, and service restarts with real-time callbacks.
"""

from __future__ import annotations

import time
from typing import Callable, Optional

from core.backup import BackupManager
from core.config import EngineConfig, PerformanceProfile
from core.distro import DistroResolver
from core.git_repos import GitRepoManager
from core.hardware import HardwareDetector
from core.plasma_config import PlasmaConfigurator
from core.plasma_layout import PlasmaLayoutManager


class PipelineRunner:
    """Orchestrates the desktop transformation pipeline."""

    def __init__(self, config: EngineConfig) -> None:
        self.config = config
        self.cancelled = False
        self.config.ensure_directories()

        self.distro_resolver = DistroResolver()
        self.backup_manager = BackupManager(backup_dir=config.backup_dir, home_dir=config.home_dir)
        self.repo_manager = GitRepoManager(config=config)
        self.plasma_config = PlasmaConfigurator(config=config)
        self.layout_manager = PlasmaLayoutManager(config=config)

    def cancel(self) -> None:
        """Flag the pipeline to stop execution at the next checkpoint."""
        self.cancelled = True

    def run(
        self,
        progress_cb: Optional[Callable[[int, str], None]] = None,
        log_cb: Optional[Callable[[str, str], None]] = None,
    ) -> bool:
        """
        Execute the full transformation pipeline.
        Progress is reported from 0 to 100%.
        """
        def update(pct: int, msg: str, level: str = "INFO"):
            if log_cb:
                log_cb(f"[{pct}%] {msg}", level)
            if progress_cb:
                progress_cb(pct, msg)

        try:
            update(2, "Phase 1: Running hardware and system environment pre-flight checks...")
            hw = HardwareDetector.get_hardware_profile()
            update(5, f"Detected: {hw.summary()}", "INFO")

            if self.cancelled:
                update(0, "Installation cancelled by user.", "WARN")
                return False

            # Phase 2: Atomic Pre-Flight Snapshot Backup
            update(10, "Phase 2: Creating atomic snapshot backup of existing configurations...")
            backup_path = self.backup_manager.create_backup(log_cb=log_cb)
            if not backup_path:
                update(12, "Pre-flight backup failed! Halting to protect user data.", "ERROR")
                return False
            update(15, f"Snapshot successfully created: {backup_path.name}", "SUCCESS")

            if self.cancelled:
                return False

            # Phase 3: Check / Resolve System Dependencies
            update(20, "Phase 3: Verifying system build and runtime dependencies...")
            missing_cmds = self.distro_resolver.check_missing_commands()
            if missing_cmds:
                update(22, f"Missing build tools: {', '.join(missing_cmds)}. Attempting installation...", "WARN")
                # Attempt installation if pkexec/sudo available
                self.distro_resolver.install_dependencies(
                    profile=self.config.profile,
                    use_pkexec=True,
                    log_cb=log_cb,
                )

            if self.cancelled:
                return False

            # Phase 4: Fetch Upstream Open-Source Repositories
            update(28, "Phase 4: Fetching upstream open-source repositories from GitHub...")
            kde_repo = self.repo_manager.clone_or_update("mactahoe_kde", log_cb=log_cb)
            gtk_repo = self.repo_manager.clone_or_update("mactahoe_gtk", log_cb=log_cb)
            icon_repo = self.repo_manager.clone_or_update("mactahoe_icons", log_cb=log_cb)
            cursor_repo = self.repo_manager.clone_or_update("whitesur_cursors", log_cb=log_cb)

            if self.cancelled:
                return False

            # Phase 5: Install Themes, Icons, and Cursors
            update(45, "Phase 5: Installing KDE Plasma themes, Kvantum styles, and Aurorae decorations...")
            if self.config.components.install_plasma_theme and kde_repo:
                self.repo_manager.install_kde_theme(
                    kde_repo,
                    mode=self.config.mode,
                    profile=self.config.profile,
                    log_cb=log_cb,
                )

            if self.config.components.install_gtk_theme and gtk_repo:
                update(52, "Installing GTK3/GTK4 and Libadwaita themes...")
                self.repo_manager.install_gtk_theme(
                    gtk_repo,
                    mode=self.config.mode,
                    profile=self.config.profile,
                    log_cb=log_cb,
                )

            if (self.config.components.install_icons or self.config.components.install_cursors) and icon_repo:
                update(58, "Installing macOS squircle icons and High-DPI cursors...")
                self.repo_manager.install_icons_and_cursors(
                    icons_repo=icon_repo,
                    cursors_repo=cursor_repo,
                    log_cb=log_cb,
                )

            if self.cancelled:
                return False

            # Phase 6: KWin C++ Liquid Glass Shaders (Mode A)
            if self.config.profile == PerformanceProfile.FULL_LIQUID_GLASS and self.config.components.install_kwin_shaders:
                update(65, "Phase 6: Compiling and installing KWin Liquid Glass shader effects...")
                blur_repo = self.repo_manager.clone_or_update("better_blur", log_cb=log_cb)
                if blur_repo:
                    self.repo_manager.build_and_install_kwin_effect(blur_repo, "Better Blur DX", log_cb=log_cb)

                corners_repo = self.repo_manager.clone_or_update("rounded_corners", log_cb=log_cb)
                if corners_repo:
                    self.repo_manager.build_and_install_kwin_effect(corners_repo, "Rounded Corners", log_cb=log_cb)
            else:
                update(65, "Phase 6: Lite Performance Mode selected — skipping heavy C++ shader compilation.", "INFO")

            if self.cancelled:
                return False

            # Phase 7: Liquid Glass Plasmoids & Widgets
            if self.config.components.install_plasmoids:
                update(72, "Phase 7: Deploying Liquid Glass QML plasmoids and applets...")
                widgets_repo = self.repo_manager.clone_or_update("liquidglass_widgets", log_cb=log_cb)
                if widgets_repo:
                    self.repo_manager.install_liquidglass_widgets(widgets_repo, log_cb=log_cb)

                kpple_repo = self.repo_manager.clone_or_update("kpple_menu", log_cb=log_cb)
                if kpple_repo:
                    self.repo_manager.install_extra_widget(kpple_repo, "org.kpple.kppleMenu", log_cb=log_cb)

                colorizer_repo = self.repo_manager.clone_or_update("panel_colorizer", log_cb=log_cb)
                if colorizer_repo:
                    self.repo_manager.install_extra_widget(colorizer_repo, "luisbocanegra.panelcolorizer", log_cb=log_cb)

            if self.cancelled:
                return False

            # Phase 8: KDE Plasma 6 Configuration
            update(80, "Phase 8: Applying KDE Plasma 6 settings (traffic lights, Kvantum, Dolphin, KRunner)...")
            self.plasma_config.apply_window_decorations(mode=self.config.mode, log_cb=log_cb)
            self.plasma_config.configure_kvantum(mode=self.config.mode, profile=self.config.profile, log_cb=log_cb)
            self.plasma_config.apply_colors_and_icons(mode=self.config.mode, log_cb=log_cb)
            self.plasma_config.configure_kwin_effects(profile=self.config.profile, log_cb=log_cb)

            if self.config.components.apply_dolphin_styling:
                self.plasma_config.configure_dolphin(log_cb=log_cb)

            if self.config.components.apply_krunner_spotlight:
                self.plasma_config.configure_krunner_spotlight(log_cb=log_cb)

            if self.config.components.apply_flatpak_overrides:
                self.plasma_config.apply_flatpak_overrides(log_cb=log_cb)

            if self.cancelled:
                return False

            # Phase 9: Plasma 6 Layout & Floating Dock
            if self.config.components.apply_plasma_layout:
                update(90, "Phase 9: Generating and applying Top Global Menu Bar and Floating Dock layout...")
                self.layout_manager.apply_layout(log_cb=log_cb)

            # Phase 10: Reloading desktop services
            update(95, "Phase 10: Refreshing KWin compositor and PlasmaShell...")
            self.backup_manager.restart_kde_services(log_cb=log_cb)

            update(100, "macOS Tahoe 'Liquid Glass' transformation completed successfully!", "SUCCESS")
            return True

        except Exception as e:
            update(0, f"Transformation pipeline encountered an unhandled exception: {e}", "ERROR")
            return False

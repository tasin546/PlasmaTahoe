#!/usr/bin/env python3
"""
PlasmaTahoe-Engine: PyQt6 Real-Time GUI Wizard
Sleek macOS Tahoe-inspired wizard interface featuring system diagnostics,
performance profile configuration, live streaming installation console,
and one-click snapshot rollback manager.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

try:
    from PyQt6.QtCore import QSize, Qt, QThread, pyqtSignal
    from PyQt6.QtGui import QColor, QFont, QIcon, QTextCursor
    from PyQt6.QtWidgets import (
        QApplication,
        QCheckBox,
        QFrame,
        QGridLayout,
        QHBoxLayout,
        QLabel,
        QListWidget,
        QListWidgetItem,
        QMainWindow,
        QMessageBox,
        QPlainTextEdit,
        QProgressBar,
        QPushButton,
        QRadioButton,
        QSlider,
        QStackedWidget,
        QVBoxLayout,
        QWidget,
    )
    PYQT6_AVAILABLE = True
except ImportError:
    PYQT6_AVAILABLE = False

from core.backup import BackupInfo, BackupManager
from core.config import ComponentOptions, EngineConfig, PerformanceProfile, ThemeMode
from core.distro import DistroResolver
from core.hardware import HardwareDetector, HardwareProfile
from core.runner import PipelineRunner
from ui.styles import get_liquid_glass_stylesheet


if PYQT6_AVAILABLE:

    class WorkerThread(QThread):
        """Worker thread running the transformation pipeline without freezing UI."""
        progress_signal = pyqtSignal(int, str)
        log_signal = pyqtSignal(str, str)
        finished_signal = pyqtSignal(bool)

        def __init__(self, config: EngineConfig) -> None:
            super().__init__()
            self.config = config
            self.runner = PipelineRunner(config)

        def run(self) -> None:
            success = self.runner.run(
                progress_cb=self._on_progress,
                log_cb=self._on_log,
            )
            self.finished_signal.emit(success)

        def cancel(self) -> None:
            self.runner.cancel()

        def _on_progress(self, pct: int, msg: str) -> None:
            self.progress_signal.emit(pct, msg)

        def _on_log(self, text: str, level: str) -> None:
            self.log_signal.emit(text, level)


    class RestoreThread(QThread):
        """Worker thread executing snapshot rollback."""
        log_signal = pyqtSignal(str, str)
        finished_signal = pyqtSignal(bool)

        def __init__(self, backup_manager: BackupManager, archive_path: Path) -> None:
            super().__init__()
            self.backup_manager = backup_manager
            self.archive_path = archive_path

        def run(self) -> None:
            success = self.backup_manager.restore_backup(
                archive_path=self.archive_path,
                log_cb=self._on_log,
            )
            self.finished_signal.emit(success)

        def _on_log(self, text: str, level: str) -> None:
            self.log_signal.emit(text, level)


    class TahoeWizardWindow(QMainWindow):
        """Main Application Window for PlasmaTahoe Desktop Customizer."""

        def __init__(self, config: Optional[EngineConfig] = None) -> None:
            super().__init__()
            self.config = config or EngineConfig()
            self.distro_resolver = DistroResolver()
            self.hardware_profile = HardwareDetector.get_hardware_profile()
            self.backup_manager = BackupManager(backup_dir=self.config.backup_dir)

            self.worker_thread: Optional[WorkerThread] = None
            self.restore_thread: Optional[RestoreThread] = None

            self.setWindowTitle("PlasmaTahoe Engine — macOS Tahoe for KDE Plasma 6")
            self.setMinimumSize(960, 640)
            self.resize(1020, 680)

            self.init_ui()
            self.apply_theme()

        def apply_theme(self) -> None:
            dark_mode = (self.config.mode != ThemeMode.LIGHT)
            self.setStyleSheet(get_liquid_glass_stylesheet(dark_mode=dark_mode))

        def init_ui(self) -> None:
            central = QWidget()
            central.setObjectName("CentralWidget")
            self.setCentralWidget(central)

            main_layout = QHBoxLayout(central)
            main_layout.setContentsMargins(0, 0, 0, 0)
            main_layout.setSpacing(0)

            # --- Sidebar ---
            sidebar = QWidget()
            sidebar.setFixedWidth(230)
            sidebar_layout = QVBoxLayout(sidebar)
            sidebar_layout.setContentsMargins(14, 16, 14, 16)
            sidebar_layout.setSpacing(12)

            # Decorative macOS traffic light dots
            traffic_lights = QHBoxLayout()
            traffic_lights.setSpacing(8)
            for color in ["#FF5F56", "#FFBD2E", "#27C93F"]:
                dot = QLabel()
                dot.setFixedSize(12, 12)
                dot.setStyleSheet(f"background-color: {color}; border-radius: 6px;")
                traffic_lights.addWidget(dot)
            traffic_lights.addStretch()
            sidebar_layout.addLayout(traffic_lights)

            # App Title & Subtitle in Sidebar
            app_title = QLabel("PlasmaTahoe")
            app_title.setStyleSheet("font-size: 16px; font-weight: 700; margin-top: 6px;")
            app_sub = QLabel("macOS Liquid Glass Engine")
            app_sub.setStyleSheet("font-size: 11px; color: #8E8E93; margin-bottom: 8px;")
            sidebar_layout.addWidget(app_title)
            sidebar_layout.addWidget(app_sub)

            # Sidebar Navigation List
            self.nav_list = QListWidget()
            self.nav_list.setObjectName("NavigationList")
            nav_items = [
                ("System Check", "🖥️"),
                ("Customization", "🎨"),
                ("Live Console", "⚡"),
                ("Backups & Restore", "🔄"),
                ("About & Credits", "ℹ️"),
            ]
            for title, icon in nav_items:
                item = QListWidgetItem(f"{icon}  {title}")
                self.nav_list.addItem(item)
            self.nav_list.setCurrentRow(0)
            self.nav_list.currentRowChanged.connect(self._on_tab_changed)
            sidebar_layout.addWidget(self.nav_list)

            # Version Label
            ver_label = QLabel("v1.0.0-liquidglass")
            ver_label.setStyleSheet("font-size: 10px; color: #666; padding-left: 6px;")
            sidebar_layout.addWidget(ver_label)

            main_layout.addWidget(sidebar)

            # --- Main Content Stacked Widget ---
            self.content_stack = QStackedWidget()
            self.content_stack.addWidget(self._create_welcome_page())
            self.content_stack.addWidget(self._create_options_page())
            self.content_stack.addWidget(self._create_console_page())
            self.content_stack.addWidget(self._create_restore_page())
            self.content_stack.addWidget(self._create_about_page())
            main_layout.addWidget(self.content_stack)

        # ---------------- Page 1: Welcome & System Diagnostics ----------------
        def _create_welcome_page(self) -> QWidget:
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setContentsMargins(32, 28, 32, 28)
            layout.setSpacing(18)

            title = QLabel("Welcome to PlasmaTahoe Engine")
            title.setProperty("class", "title")
            subtitle = QLabel(
                "Transform KDE Plasma 6 into a fluid, near 1:1 macOS Tahoe 'Liquid Glass' desktop "
                "orchestrating real, actively maintained open-source components."
            )
            subtitle.setProperty("class", "subtitle")
            subtitle.setWordWrap(True)
            layout.addWidget(title)
            layout.addWidget(subtitle)

            grid = QGridLayout()
            grid.setSpacing(14)

            # Distro Card
            distro_card = QFrame()
            distro_card.setProperty("class", "glass-card")
            d_layout = QVBoxLayout(distro_card)
            d_title = QLabel("Linux Distribution")
            d_title.setStyleSheet("font-weight: 600; font-size: 12px; color: #8E8E93;")
            d_val = QLabel(self.distro_resolver.distro.name)
            d_val.setStyleSheet("font-size: 15px; font-weight: 600;")
            d_badge = QLabel(f"Package Manager: {self.distro_resolver.distro.package_manager.upper()}")
            d_badge.setProperty("class", "badge")
            d_badge.setFixedWidth(180)
            d_layout.addWidget(d_title)
            d_layout.addWidget(d_val)
            d_layout.addWidget(d_badge)
            grid.addWidget(distro_card, 0, 0)

            # Plasma Version Card
            plasma_card = QFrame()
            plasma_card.setProperty("class", "glass-card")
            p_layout = QVBoxLayout(plasma_card)
            p_title = QLabel("Desktop Environment")
            p_title.setStyleSheet("font-weight: 600; font-size: 12px; color: #8E8E93;")
            p_val = QLabel(f"KDE Plasma {self.hardware_profile.plasma_version}")
            p_val.setStyleSheet("font-size: 15px; font-weight: 600;")
            srv = self.hardware_profile.display_server.upper()
            p_badge = QLabel(f"Display Server: {srv}")
            p_badge.setProperty("class", "badge-success" if srv == "WAYLAND" else "badge")
            p_badge.setFixedWidth(180)
            p_layout.addWidget(p_title)
            p_layout.addWidget(p_val)
            p_layout.addWidget(p_badge)
            grid.addWidget(plasma_card, 0, 1)

            # GPU Diagnostics Card
            gpu_card = QFrame()
            gpu_card.setProperty("class", "glass-card")
            g_layout = QVBoxLayout(gpu_card)
            g_title = QLabel("Graphics Hardware")
            g_title.setStyleSheet("font-weight: 600; font-size: 12px; color: #8E8E93;")
            g_val = QLabel(f"{self.hardware_profile.gpu_vendor} {self.hardware_profile.gpu_model}")
            g_val.setStyleSheet("font-size: 14px; font-weight: 600;")
            g_val.setWordWrap(True)
            gpu_status = "Dedicated GPU" if self.hardware_profile.is_dedicated_gpu else (
                "Virtual Adapter" if self.hardware_profile.is_vm_or_software_renderer else "Integrated GPU"
            )
            g_badge = QLabel(gpu_status)
            g_badge.setProperty("class", "badge")
            g_badge.setFixedWidth(140)
            g_layout.addWidget(g_title)
            g_layout.addWidget(g_val)
            g_layout.addWidget(g_badge)
            grid.addWidget(gpu_card, 1, 0, 1, 2)

            layout.addLayout(grid)

            # Hardware Profile Recommendation Banner
            rec_banner = QFrame()
            rec_banner.setProperty("class", "glass-card")
            b_layout = QVBoxLayout(rec_banner)
            b_head = QLabel(f"Recommended Profile: {self.hardware_profile.recommended_profile.value.upper()}")
            b_head.setStyleSheet("font-size: 14px; font-weight: 700; color: #0A84FF;")
            b_desc = QLabel(self.hardware_profile.recommendation_reason)
            b_desc.setStyleSheet("font-size: 12px; color: #A0A6B8;")
            b_desc.setWordWrap(True)
            b_layout.addWidget(b_head)
            b_layout.addWidget(b_desc)
            layout.addWidget(rec_banner)

            layout.addStretch()

            # Action buttons
            btn_box = QHBoxLayout()
            btn_box.addStretch()
            next_btn = QPushButton("Continue to Options →")
            next_btn.setProperty("class", "primary")
            next_btn.setMinimumHeight(38)
            next_btn.clicked.connect(lambda: self.nav_list.setCurrentRow(1))
            btn_box.addWidget(next_btn)
            layout.addLayout(btn_box)

            return page

        # ---------------- Page 2: Customization Options ----------------
        def _create_options_page(self) -> QWidget:
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setContentsMargins(32, 24, 32, 24)
            layout.setSpacing(16)

            title = QLabel("Customization Options")
            title.setProperty("class", "title")
            layout.addWidget(title)

            # 1. Performance Profile Selector
            prof_card = QFrame()
            prof_card.setProperty("class", "glass-card")
            prof_layout = QVBoxLayout(prof_card)
            prof_lbl = QLabel("Hardware Performance Mode")
            prof_lbl.setProperty("class", "section-header")
            prof_layout.addWidget(prof_lbl)

            h_prof = QHBoxLayout()
            self.rad_full = QRadioButton("Mode A — Full Liquid Glass (Modern GPU: Refraction Shaders, Rounded Corners)")
            self.rad_lite = QRadioButton("Mode B — Lite Performance (Older iGPUs / VMs: Snappy 60 FPS, Low Power)")
            if self.hardware_profile.recommended_profile == PerformanceProfile.FULL_LIQUID_GLASS:
                self.rad_full.setChecked(True)
            else:
                self.rad_lite.setChecked(True)
            h_prof.addWidget(self.rad_full)
            h_prof.addWidget(self.rad_lite)
            prof_layout.addLayout(h_prof)
            layout.addWidget(prof_card)

            # 2. Theme Variant Selector
            theme_card = QFrame()
            theme_card.setProperty("class", "glass-card")
            t_layout = QVBoxLayout(theme_card)
            t_lbl = QLabel("Color Appearance")
            t_lbl.setProperty("class", "section-header")
            t_layout.addWidget(t_lbl)

            h_theme = QHBoxLayout()
            self.rad_dark = QRadioButton("Dark Mode (Recommended)")
            self.rad_light = QRadioButton("Light Mode")
            self.rad_dark.setChecked(True)
            h_theme.addWidget(self.rad_dark)
            h_theme.addWidget(self.rad_light)
            h_theme.addStretch()
            t_layout.addLayout(h_theme)
            layout.addWidget(theme_card)

            # 3. Floating Dock Size Slider
            dock_card = QFrame()
            dock_card.setProperty("class", "glass-card")
            d_layout = QVBoxLayout(dock_card)
            self.lbl_dock_size = QLabel(f"Floating Dock Height: {self.config.components.dock_height} px")
            self.lbl_dock_size.setProperty("class", "section-header")
            d_layout.addWidget(self.lbl_dock_size)

            self.slider_dock = QSlider(Qt.Orientation.Horizontal)
            self.slider_dock.setRange(40, 72)
            self.slider_dock.setValue(self.config.components.dock_height)
            self.slider_dock.valueChanged.connect(
                lambda val: self.lbl_dock_size.setText(f"Floating Dock Height: {val} px")
            )
            d_layout.addWidget(self.slider_dock)
            layout.addWidget(dock_card)

            # 4. Component Checkboxes
            comp_card = QFrame()
            comp_card.setProperty("class", "glass-card")
            c_layout = QVBoxLayout(comp_card)
            c_lbl = QLabel("Components to Install & Configure")
            c_lbl.setProperty("class", "section-header")
            c_layout.addWidget(c_lbl)

            grid_c = QGridLayout()
            self.cb_plasma = QCheckBox("KDE Plasma & Kvantum Themes")
            self.cb_plasma.setChecked(True)
            self.cb_gtk = QCheckBox("GTK3/4 & Libadwaita Consistency")
            self.cb_gtk.setChecked(True)
            self.cb_icons = QCheckBox("macOS Tahoe Squircle Icons & Cursors")
            self.cb_icons.setChecked(True)
            self.cb_plasmoids = QCheckBox("Liquid Glass QML Plasmoids & Widgets")
            self.cb_plasmoids.setChecked(True)
            self.cb_shaders = QCheckBox("Compile KWin GLSL Refraction Shaders")
            self.cb_shaders.setChecked(True)
            self.cb_layout = QCheckBox("Deploy Top Global Menu Bar & Floating Dock")
            self.cb_layout.setChecked(True)
            self.cb_dolphin = QCheckBox("Dolphin File Manager macOS Styling")
            self.cb_dolphin.setChecked(True)
            self.cb_krunner = QCheckBox("KRunner Centered Spotlight (Meta+Space)")
            self.cb_krunner.setChecked(True)
            self.cb_flatpak = QCheckBox("Flatpak Theme & Kvantum Overrides")
            self.cb_flatpak.setChecked(True)

            grid_c.addWidget(self.cb_plasma, 0, 0)
            grid_c.addWidget(self.cb_gtk, 0, 1)
            grid_c.addWidget(self.cb_icons, 1, 0)
            grid_c.addWidget(self.cb_plasmoids, 1, 1)
            grid_c.addWidget(self.cb_shaders, 2, 0)
            grid_c.addWidget(self.cb_layout, 2, 1)
            grid_c.addWidget(self.cb_dolphin, 3, 0)
            grid_c.addWidget(self.cb_krunner, 3, 1)
            grid_c.addWidget(self.cb_flatpak, 4, 0)
            c_layout.addLayout(grid_c)
            layout.addWidget(comp_card)

            layout.addStretch()

            # Bottom buttons
            btn_box = QHBoxLayout()
            back_btn = QPushButton("← Back")
            back_btn.clicked.connect(lambda: self.nav_list.setCurrentRow(0))
            btn_box.addWidget(back_btn)
            btn_box.addStretch()

            apply_btn = QPushButton("Apply Transformation 🚀")
            apply_btn.setProperty("class", "primary")
            apply_btn.setMinimumHeight(40)
            apply_btn.clicked.connect(self._start_installation)
            btn_box.addWidget(apply_btn)
            layout.addLayout(btn_box)

            return page

        # ---------------- Page 3: Live Execution Console ----------------
        def _create_console_page(self) -> QWidget:
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setContentsMargins(32, 24, 32, 24)
            layout.setSpacing(14)

            self.console_title = QLabel("Execution Console")
            self.console_title.setProperty("class", "title")
            layout.addWidget(self.console_title)

            self.status_lbl = QLabel("Ready to begin transformation.")
            self.status_lbl.setStyleSheet("font-size: 13px; color: #8E8E93;")
            layout.addWidget(self.status_lbl)

            self.progress_bar = QProgressBar()
            self.progress_bar.setRange(0, 100)
            self.progress_bar.setValue(0)
            layout.addWidget(self.progress_bar)

            self.console_output = QPlainTextEdit()
            self.console_output.setProperty("class", "console")
            self.console_output.setReadOnly(True)
            layout.addWidget(self.console_output)

            # Action bar
            bar = QHBoxLayout()
            self.btn_cancel = QPushButton("Cancel")
            self.btn_cancel.setProperty("class", "danger")
            self.btn_cancel.clicked.connect(self._cancel_installation)
            bar.addWidget(self.btn_cancel)

            bar.addStretch()

            self.btn_finish = QPushButton("Restart Plasma Shell & Finish")
            self.btn_finish.setProperty("class", "primary")
            self.btn_finish.setEnabled(False)
            self.btn_finish.clicked.connect(self._finish_and_restart)
            bar.addWidget(self.btn_finish)

            layout.addLayout(bar)
            return page

        # ---------------- Page 4: Snapshots & Rollback ----------------
        def _create_restore_page(self) -> QWidget:
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setContentsMargins(32, 24, 32, 24)
            layout.setSpacing(16)

            title = QLabel("Snapshot Backup & Rollback")
            title.setProperty("class", "title")
            sub = QLabel(
                "Every modification creates an atomic snapshot of your KDE settings. "
                "You can inspect saved snapshots and restore your desktop with 1-click."
            )
            sub.setProperty("class", "subtitle")
            sub.setWordWrap(True)
            layout.addWidget(title)
            layout.addWidget(sub)

            # Snapshots List
            self.backup_list = QListWidget()
            self.backup_list.setProperty("class", "backup-list")
            self.backup_list.currentRowChanged.connect(self._on_backup_selected)
            layout.addWidget(self.backup_list)

            # Manifest Info Card
            self.manifest_card = QFrame()
            self.manifest_card.setProperty("class", "glass-card")
            m_layout = QVBoxLayout(self.manifest_card)
            self.manifest_lbl = QLabel("Select a snapshot above to view details.")
            self.manifest_lbl.setStyleSheet("font-size: 12px; color: #A0A6B8;")
            self.manifest_lbl.setWordWrap(True)
            m_layout.addWidget(self.manifest_lbl)
            layout.addWidget(self.manifest_card)

            # Buttons
            bar = QHBoxLayout()
            refresh_btn = QPushButton("Refresh List")
            refresh_btn.clicked.connect(self._refresh_backups)
            bar.addWidget(refresh_btn)

            create_snap_btn = QPushButton("Create Snapshot Now")
            create_snap_btn.clicked.connect(self._create_manual_snapshot)
            bar.addWidget(create_snap_btn)

            bar.addStretch()

            self.btn_rollback = QPushButton("Rollback to Selected Snapshot ⏪")
            self.btn_rollback.setProperty("class", "danger")
            self.btn_rollback.setEnabled(False)
            self.btn_rollback.clicked.connect(self._perform_rollback)
            bar.addWidget(self.btn_rollback)

            layout.addLayout(bar)
            self._refresh_backups()
            return page

        # ---------------- Page 5: About & Credits ----------------
        def _create_about_page(self) -> QWidget:
            page = QWidget()
            layout = QVBoxLayout(page)
            layout.setContentsMargins(32, 28, 32, 28)
            layout.setSpacing(16)

            title = QLabel("About PlasmaTahoe Engine")
            title.setProperty("class", "title")
            sub = QLabel(
                "PlasmaTahoe Engine is a free and open-source desktop transformer designed for KDE Plasma 6.2+.\n"
                "Released under the GNU General Public License v3.0 (GPL-3.0)."
            )
            sub.setProperty("class", "subtitle")
            layout.addWidget(title)
            layout.addWidget(sub)

            card = QFrame()
            card.setProperty("class", "glass-card")
            c_layout = QVBoxLayout(card)
            c_title = QLabel("Upstream Open-Source Projects & Author Attributions")
            c_title.setProperty("class", "section-header")
            c_layout.addWidget(c_title)

            credits_text = (
                "• <b>MacTahoe-kde & WhiteSur Themes</b> — by <b>Vince Liuice</b> (GPL-3.0)<br>"
                "&nbsp;&nbsp;&nbsp;https://github.com/vinceliuice/MacTahoe-kde<br><br>"
                "• <b>Liquid Glass KDE Widgets</b> — by <b>Jax Faith (jaxparrow07)</b> (GPL-3.0)<br>"
                "&nbsp;&nbsp;&nbsp;https://github.com/jaxparrow07/liquidglass-kde-widgets<br><br>"
                "• <b>KWin Better Blur DX</b> — by <b>xarblu / taj-ny</b> (GPL-3.0)<br>"
                "&nbsp;&nbsp;&nbsp;https://github.com/xarblu/kwin-effects-better-blur-dx<br><br>"
                "• <b>KDE Rounded Corners</b> — by <b>Matin Lotfali</b> (GPL-3.0)<br>"
                "&nbsp;&nbsp;&nbsp;https://github.com/matinlotfali/KDE-Rounded-Corners<br><br>"
                "• <b>KppleMenu Plasma 6</b> — by <b>ChrTall</b> (GPL-3.0)<br>"
                "&nbsp;&nbsp;&nbsp;https://github.com/ChrTall/kppleMenu<br><br>"
                "• <b>Plasma Panel Colorizer</b> — by <b>Luis Bocanegra</b> (GPL-3.0)<br>"
                "&nbsp;&nbsp;&nbsp;https://github.com/luisbocanegra/plasma-panel-colorizer"
            )
            lbl = QLabel(credits_text)
            lbl.setTextFormat(Qt.TextFormat.RichText)
            lbl.setStyleSheet("font-size: 13px; line-height: 1.6; color: #C0C6D8;")
            c_layout.addWidget(lbl)
            layout.addWidget(card)

            layout.addStretch()
            return page

        # ---------------- Controller Logic ----------------
        def _on_tab_changed(self, index: int) -> None:
            self.content_stack.setCurrentIndex(index)
            if index == 3:
                self._refresh_backups()

        def _gather_options(self) -> None:
            """Collect user selections from UI into EngineConfig."""
            self.config.mode = ThemeMode.DARK if self.rad_dark.isChecked() else ThemeMode.LIGHT
            self.config.profile = (
                PerformanceProfile.FULL_LIQUID_GLASS
                if self.rad_full.isChecked()
                else PerformanceProfile.LITE_PERFORMANCE
            )
            self.config.components = ComponentOptions(
                install_plasma_theme=self.cb_plasma.isChecked(),
                install_kvantum_theme=self.cb_plasma.isChecked(),
                install_gtk_theme=self.cb_gtk.isChecked(),
                install_icons=self.cb_icons.isChecked(),
                install_cursors=self.cb_icons.isChecked(),
                install_plasmoids=self.cb_plasmoids.isChecked(),
                install_kwin_shaders=self.cb_shaders.isChecked(),
                apply_plasma_layout=self.cb_layout.isChecked(),
                apply_dolphin_styling=self.cb_dolphin.isChecked(),
                apply_krunner_spotlight=self.cb_krunner.isChecked(),
                apply_flatpak_overrides=self.cb_flatpak.isChecked(),
                top_panel_height=28,
                dock_height=self.slider_dock.value(),
                dock_icon_size=48,
            )

        def _start_installation(self) -> None:
            self._gather_options()
            self.nav_list.setCurrentRow(2)  # Switch to Console
            self.console_output.clear()
            self.progress_bar.setValue(0)
            self.btn_cancel.setEnabled(True)
            self.btn_finish.setEnabled(False)

            self.worker_thread = WorkerThread(self.config)
            self.worker_thread.progress_signal.connect(self._on_install_progress)
            self.worker_thread.log_signal.connect(self._append_console_log)
            self.worker_thread.finished_signal.connect(self._on_install_finished)
            self.worker_thread.start()

        def _cancel_installation(self) -> None:
            if self.worker_thread and self.worker_thread.isRunning():
                self.worker_thread.cancel()
                self._append_console_log("Cancelling operation...", "WARN")
                self.btn_cancel.setEnabled(False)

        def _on_install_progress(self, pct: int, msg: str) -> None:
            self.progress_bar.setValue(pct)
            self.status_lbl.setText(msg)

        def _append_console_log(self, text: str, level: str) -> None:
            color = "#A0A6B8"
            if level == "SUCCESS":
                color = "#34C759"
            elif level == "WARN":
                color = "#FF9F0A"
            elif level == "ERROR":
                color = "#FF453A"
            elif level == "DEBUG":
                color = "#5AC8FA"

            html = f'<span style="color: {color};">[{level}] {text}</span>'
            self.console_output.appendHtml(html)
            self.console_output.moveCursor(QTextCursor.MoveOperation.End)

        def _on_install_finished(self, success: bool) -> None:
            self.btn_cancel.setEnabled(False)
            self.btn_finish.setEnabled(True)
            if success:
                self.status_lbl.setText("Transformation complete! Restart services to finalize.")
                QMessageBox.information(
                    self,
                    "Transformation Complete",
                    "macOS Tahoe environment successfully configured!\n"
                    "Click 'Restart Plasma Shell & Finish' to apply changes immediately.",
                )
            else:
                self.status_lbl.setText("Installation finished with errors. Inspect log above.")

        def _finish_and_restart(self) -> None:
            self.backup_manager.restart_kde_services(log_cb=self._append_console_log)
            QMessageBox.information(
                self,
                "Ready",
                "Desktop services reloaded. Enjoy macOS Tahoe on KDE Plasma 6!",
            )

        # ---------------- Backups Controller ----------------
        def _refresh_backups(self) -> None:
            self.backup_list.clear()
            backups = self.backup_manager.list_backups()
            for b in backups:
                item = QListWidgetItem(f"📦 {b.archive_path.name}  —  {b.formatted_date}  ({b.size_human})")
                item.setData(Qt.ItemDataRole.UserRole, str(b.archive_path))
                self.backup_list.addItem(item)
            self.btn_rollback.setEnabled(False)
            self.manifest_lbl.setText(f"Found {len(backups)} snapshot(s). Select one to view contents or rollback.")

        def _on_backup_selected(self, row: int) -> None:
            if row < 0:
                self.btn_rollback.setEnabled(False)
                return
            item = self.backup_list.item(row)
            if not item:
                return
            arc_path = Path(item.data(Qt.ItemDataRole.UserRole))
            self.btn_rollback.setEnabled(True)

            sidecar = arc_path.with_suffix(".json")
            if sidecar.exists():
                try:
                    import json
                    with open(sidecar, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                    files = meta.get("files", {})
                    plasmoids = meta.get("installed_plasmoids", [])
                    info_text = (
                        f"<b>Snapshot File:</b> {arc_path.name}<br>"
                        f"<b>Date:</b> {meta.get('formatted_date', 'N/A')}<br>"
                        f"<b>Archived Config Files ({len(files)}):</b> {', '.join(files.keys())}<br>"
                        f"<b>Recorded Plasmoids:</b> {', '.join(plasmoids) if plasmoids else 'None'}"
                    )
                    self.manifest_lbl.setText(info_text)
                    return
                except Exception:
                    pass
            self.manifest_lbl.setText(f"Snapshot: {arc_path.name}")

        def _create_manual_snapshot(self) -> None:
            arc = self.backup_manager.create_backup()
            if arc:
                QMessageBox.information(self, "Backup Created", f"New snapshot saved:\n{arc.name}")
                self._refresh_backups()
            else:
                QMessageBox.warning(self, "Backup Error", "Failed to create snapshot.")

        def _perform_rollback(self) -> None:
            row = self.backup_list.currentRow()
            if row < 0:
                return
            item = self.backup_list.item(row)
            arc_path = Path(item.data(Qt.ItemDataRole.UserRole))

            reply = QMessageBox.question(
                self,
                "Confirm Rollback",
                f"Are you sure you want to rollback your desktop configuration to:\n{arc_path.name}?\n\n"
                "This will replace your current KDE configurations and reload Plasma.",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            )
            if reply == QMessageBox.StandardButton.Yes:
                ok = self.backup_manager.restore_backup(arc_path)
                if ok:
                    QMessageBox.information(self, "Rollback Complete", "Configuration restored successfully.")
                else:
                    QMessageBox.critical(self, "Rollback Failed", "Could not restore configuration snapshot.")


    def launch_gui(config: Optional[EngineConfig] = None) -> int:
        """Launch the PyQt6 wizard application."""
        app = QApplication(sys.argv)
        app.setApplicationName("PlasmaTahoe-Engine")
        window = TahoeWizardWindow(config=config)
        window.show()
        return app.exec()
else:
    class TahoeWizardWindow:  # type: ignore
        """Fallback placeholder when PyQt6 is not installed."""
        def __init__(self, *args, **kwargs) -> None:
            raise RuntimeError("PyQt6 is required for TahoeWizardWindow GUI.")

    def launch_gui(config: Optional[EngineConfig] = None) -> int:
        print("Error: PyQt6 is not installed on this system.")
        print("Please install python-pyqt6 via your package manager or run in headless mode (--headless).")
        return 1

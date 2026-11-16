#!/usr/bin/env python3
"""
PlasmaTahoe-Engine: KDE Plasma 6 Configuration Manager
Applies window decorations, Kvantum styles, global themes, Dolphin preferences,
and KRunner Spotlight shortcuts using official KDE Plasma 6 CLI tools (kwriteconfig6,
lookandfeeltool, plasma-apply-colorscheme, plasma-apply-cursortheme, qdbus6).
"""

from __future__ import annotations

import configparser
import os
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Optional

from core.config import EngineConfig, PerformanceProfile, ThemeMode


class PlasmaConfigurator:
    """Configures KDE Plasma 6 desktop settings via official CLI tooling."""

    def __init__(self, config: EngineConfig) -> None:
        self.config = config
        self.home_dir = config.home_dir
        self.config_dir = config.config_dir
        self.has_kwriteconfig = bool(shutil.which("kwriteconfig6") or shutil.which("kwriteconfig5"))
        self.kwriteconfig_bin = "kwriteconfig6" if shutil.which("kwriteconfig6") else "kwriteconfig5"

    def write_config(
        self,
        filename: str,
        group: str,
        key: str,
        value: str,
        log_cb: Optional[Callable[[str, str], None]] = None,
    ) -> bool:
        """
        Write a key/value pair into a KDE configuration file using kwriteconfig6
        or standard fallback INI parser.
        """
        if self.has_kwriteconfig:
            cmd = [self.kwriteconfig_bin, "--file", filename, "--group", group, "--key", key, str(value)]
            try:
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                return res.returncode == 0
            except Exception as e:
                if log_cb:
                    log_cb(f"kwriteconfig call failed ({e}), falling back to direct write", "WARN")

        # Direct file fallback
        target_path = self.config_dir / filename
        target_path.parent.mkdir(parents=True, exist_ok=True)

        parser = configparser.ConfigParser(interpolation=None)
        # Preserve case sensitivity
        parser.optionxform = str

        if target_path.exists():
            try:
                parser.read(target_path, encoding="utf-8")
            except Exception:
                pass

        if not parser.has_section(group):
            parser.add_section(group)
        parser.set(group, key, str(value))

        try:
            with open(target_path, "w", encoding="utf-8") as f:
                parser.write(f, space_around_delimiters=False)
            return True
        except Exception as e:
            if log_cb:
                log_cb(f"Failed to write config {filename}: {e}", "ERROR")
            return False

    def apply_window_decorations(
        self,
        mode: ThemeMode,
        log_cb: Optional[Callable[[str, str], None]] = None,
    ) -> bool:
        """Configure macOS-style traffic lights on the left and Aurorae theme."""
        if log_cb:
            log_cb("Configuring macOS window traffic lights and Aurorae decorations...", "INFO")

        # Set titlebar buttons: Close (X), Minimize (I), Maximize (A) on left
        self.write_config("kwinrc", "org.kde.kdecoration2", "ButtonsOnLeft", "XIA", log_cb)
        self.write_config("kwinrc", "org.kde.kdecoration2", "ButtonsOnRight", "", log_cb)
        self.write_config("kwinrc", "org.kde.kdecoration2", "BorderSize", "Normal", log_cb)
        self.write_config("kwinrc", "org.kde.kdecoration2", "library", "org.kde.kwin.aurorae", log_cb)

        # Aurorae decoration theme name
        theme_variant = "MacTahoe-dark" if mode == ThemeMode.DARK else "MacTahoe-light"
        self.write_config(
            "kwinrc",
            "org.kde.kdecoration2",
            "theme",
            f"__aurorae__svg__{theme_variant}",
            log_cb,
        )

        return True

    def configure_kvantum(
        self,
        mode: ThemeMode,
        profile: PerformanceProfile,
        log_cb: Optional[Callable[[str, str], None]] = None,
    ) -> bool:
        """Activate Kvantum theme in kdeglobals and kvantum.kvconfig."""
        if log_cb:
            log_cb("Activating Kvantum widget style and theme...", "INFO")

        # Set widgetStyle in kdeglobals
        self.write_config("kdeglobals", "KDE", "widgetStyle", "kvantum", log_cb)

        # Write ~/.config/Kvantum/kvantum.kvconfig
        kvantum_dir = self.config_dir / "Kvantum"
        kvantum_dir.mkdir(parents=True, exist_ok=True)
        kvconfig_path = kvantum_dir / "kvantum.kvconfig"

        theme_name = "MacTahoe" if profile == PerformanceProfile.FULL_LIQUID_GLASS else "MacTahoe"

        kvconfig_content = (
            f"[General]\n"
            f"theme={theme_name}\n"
        )
        try:
            with open(kvconfig_path, "w", encoding="utf-8") as f:
                f.write(kvconfig_content)
            if log_cb:
                log_cb(f"Kvantum active theme set to '{theme_name}'", "SUCCESS")
            return True
        except Exception as e:
            if log_cb:
                log_cb(f"Failed to write kvantum.kvconfig: {e}", "ERROR")
            return False

    def apply_colors_and_icons(
        self,
        mode: ThemeMode,
        log_cb: Optional[Callable[[str, str], None]] = None,
    ) -> bool:
        """Apply colorscheme, cursor theme, and icon theme."""
        color_scheme = "MacTahoeDark" if mode == ThemeMode.DARK else "MacTahoeLight"
        cursor_theme = "MacTahoe-cursors"
        icon_theme = "MacTahoe"

        if log_cb:
            log_cb(f"Applying color scheme: {color_scheme} and icon theme: {icon_theme}...", "INFO")

        # 1. Colorscheme
        if shutil.which("plasma-apply-colorscheme"):
            subprocess.run(["plasma-apply-colorscheme", color_scheme], capture_output=True)
        self.write_config("kdeglobals", "General", "ColorScheme", color_scheme, log_cb)

        # 2. Cursors
        if shutil.which("plasma-apply-cursortheme"):
            subprocess.run(["plasma-apply-cursortheme", cursor_theme], capture_output=True)
        self.write_config("kcminputrc", "Mouse", "cursorTheme", cursor_theme, log_cb)

        # 3. Icons
        self.write_config("kdeglobals", "Icons", "Theme", icon_theme, log_cb)

        # 4. Try lookandfeeltool if packaged
        look_name = f"com.github.vinceliuice.{color_scheme}"
        if shutil.which("lookandfeeltool"):
            try:
                subprocess.run(["lookandfeeltool", "-a", look_name], capture_output=True, timeout=5)
            except Exception:
                pass

        return True

    def configure_kwin_effects(
        self,
        profile: PerformanceProfile,
        log_cb: Optional[Callable[[str, str], None]] = None,
    ) -> bool:
        """Configure KWin blur strength, noise, and rounded corner parameters."""
        if log_cb:
            log_cb(f"Tuning KWin compositor effects for profile: {profile.value}...", "INFO")

        if profile == PerformanceProfile.FULL_LIQUID_GLASS:
            # Enable blur effect
            self.write_config("kwinrc", "Plugins", "blurEnabled", "true", log_cb)
            self.write_config("kwinrc", "Effect-blur", "BlurStrength", "12", log_cb)
            self.write_config("kwinrc", "Effect-blur", "NoiseStrength", "4", log_cb)
            # Enable BetterBlurDX & RoundedCorners plugins if compiled
            self.write_config("kwinrc", "Plugins", "kwin4_effect_shapecornersEnabled", "true", log_cb)
            self.write_config("kwinrc", "Plugins", "kwin_better_blur_dxEnabled", "true", log_cb)
            self.write_config("kwinrc", "Effect-shapecorners", "RoundRadius", "12", log_cb)
        else:
            # Lite / Performance mode
            self.write_config("kwinrc", "Plugins", "blurEnabled", "false", log_cb)
            self.write_config("kwinrc", "Effect-blur", "BlurStrength", "2", log_cb)
            self.write_config("kwinrc", "Plugins", "kwin4_effect_shapecornersEnabled", "false", log_cb)
            self.write_config("kwinrc", "Plugins", "kwin_better_blur_dxEnabled", "false", log_cb)

        return True

    def configure_dolphin(self, log_cb: Optional[Callable[[str, str], None]] = None) -> bool:
        """Configure Dolphin file manager for a clean, macOS-styled layout."""
        if log_cb:
            log_cb("Configuring Dolphin file manager (clean toolbar, hidden menubar, icons view)...", "INFO")

        # Icons view default (Mode 1), hide select circles
        self.write_config("dolphinrc", "General", "ViewMode", "1", log_cb)
        self.write_config("dolphinrc", "General", "ShowSelectionToggle", "false", log_cb)
        self.write_config("dolphinrc", "General", "ShowToolTips", "true", log_cb)
        self.write_config("dolphinrc", "General", "BrowseThroughArchives", "true", log_cb)

        # Disable standard menubar in favor of hamburger button
        self.write_config("dolphinrc", "MenuBar", "MenuBar", "Disabled", log_cb)

        # Sidebar translucent styling
        self.write_config("dolphinrc", "PlacesPanel", "IconSize", "22", log_cb)

        return True

    def configure_krunner_spotlight(self, log_cb: Optional[Callable[[str, str], None]] = None) -> bool:
        """Map Meta+Space to KRunner and position it in the center of the screen."""
        if log_cb:
            log_cb("Configuring KRunner Spotlight search (FreeFloating center, shortcut Meta+Space)...", "INFO")

        # Centered free-floating mode
        self.write_config("krunnerrc", "General", "FreeFloating", "true", log_cb)
        self.write_config("krunnerrc", "General", "historyBehavior", "Disabled", log_cb)

        # Global shortcut mapping
        self.write_config(
            "kglobalshortcutsrc",
            "krunner.desktop",
            "_launch",
            "Meta+Space,none,Spotlight Search",
            log_cb,
        )

        return True

    def apply_flatpak_overrides(self, log_cb: Optional[Callable[[str, str], None]] = None) -> bool:
        """Grant Flatpak applications read access to user themes and Kvantum."""
        if not shutil.which("flatpak"):
            if log_cb:
                log_cb("Flatpak is not installed on this system. Skipping overrides.", "INFO")
            return True

        if log_cb:
            log_cb("Applying Flatpak theme overrides for sandboxed application consistency...", "INFO")

        overrides = [
            ["flatpak", "override", "--user", "--filesystem=xdg-config/Kvantum:ro"],
            ["flatpak", "override", "--user", "--filesystem=~/.themes:ro"],
            ["flatpak", "override", "--user", "--filesystem=~/.local/share/icons:ro"],
        ]

        for cmd in overrides:
            try:
                subprocess.run(cmd, capture_output=True, timeout=5)
            except Exception as e:
                if log_cb:
                    log_cb(f"Warning: Flatpak override failed: {e}", "WARN")

        return True

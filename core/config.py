#!/usr/bin/env python3
"""
PlasmaTahoe-Engine: Core Configuration Module
Defines configuration schemas, hardware profiles, theme modes, and path settings.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict


def _get_xdg_config_home() -> Path:
    env = os.environ.get("XDG_CONFIG_HOME")
    return Path(env).resolve() if env else Path.home() / ".config"


def _get_xdg_data_home() -> Path:
    env = os.environ.get("XDG_DATA_HOME")
    return Path(env).resolve() if env else Path.home() / ".local" / "share"


def _get_xdg_cache_home() -> Path:
    env = os.environ.get("XDG_CACHE_HOME")
    return Path(env).resolve() if env else Path.home() / ".cache"


class ThemeMode(str, Enum):
    """macOS Tahoe Theme Color Variants."""
    DARK = "dark"
    LIGHT = "light"
    AUTO = "auto"


class PerformanceProfile(str, Enum):
    """
    Hardware Performance Profile:
    - FULL_LIQUID_GLASS: Compiles C++ KWin shaders (better-blur-dx, rounded-corners),
      activates refractive glass blur, specular edge highlight, translucent Kvantum.
    - LITE_PERFORMANCE: Skips C++ shader compilation, uses solid/opaque Kvantum theme,
      disables expensive multi-pass blur for older iGPUs/VMs/battery saving.
    """
    FULL_LIQUID_GLASS = "full_liquid_glass"
    LITE_PERFORMANCE = "lite_performance"


@dataclass
class ComponentOptions:
    """Toggles for individual desktop transformation components."""
    install_plasma_theme: bool = True
    install_kvantum_theme: bool = True
    install_gtk_theme: bool = True
    install_icons: bool = True
    install_cursors: bool = True
    install_plasmoids: bool = True
    install_kwin_shaders: bool = True
    apply_plasma_layout: bool = True
    apply_dolphin_styling: bool = True
    apply_krunner_spotlight: bool = True
    apply_flatpak_overrides: bool = True
    top_panel_height: int = 28
    dock_height: int = 56
    dock_icon_size: int = 48

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ComponentOptions:
        valid_keys = {f.name for f in cls.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in valid_keys}
        return cls(**filtered)


@dataclass
class EngineConfig:
    """Master engine configuration."""
    mode: ThemeMode = ThemeMode.DARK
    profile: PerformanceProfile = PerformanceProfile.FULL_LIQUID_GLASS
    components: ComponentOptions = field(default_factory=ComponentOptions)

    # Standard XDG paths
    home_dir: Path = field(default_factory=Path.home)
    config_dir: Path = field(default_factory=_get_xdg_config_home)
    local_share_dir: Path = field(default_factory=_get_xdg_data_home)
    cache_dir: Path = field(default_factory=lambda: _get_xdg_cache_home() / "plasmatahoe")
    backup_dir: Path = field(default_factory=lambda: _get_xdg_data_home() / "plasmatahoe" / "backups")
    icons_dir: Path = field(default_factory=lambda: _get_xdg_data_home() / "icons")
    themes_dir: Path = field(default_factory=lambda: Path.home() / ".themes")
    aurorae_dir: Path = field(default_factory=lambda: _get_xdg_data_home() / "aurorae" / "themes")
    plasma_themes_dir: Path = field(default_factory=lambda: _get_xdg_data_home() / "plasma" / "desktoptheme")
    plasmoids_dir: Path = field(default_factory=lambda: _get_xdg_data_home() / "plasma" / "plasmoids")
    wallpapers_dir: Path = field(default_factory=lambda: _get_xdg_data_home() / "wallpapers")
    color_schemes_dir: Path = field(default_factory=lambda: _get_xdg_data_home() / "color-schemes")
    kvantum_config_dir: Path = field(default_factory=lambda: _get_xdg_config_home() / "Kvantum")

    # Execution flags
    dry_run: bool = False
    headless: bool = False
    verbose: bool = False

    def ensure_directories(self) -> None:
        """Create required engine and configuration directories."""
        dirs = [
            self.cache_dir,
            self.cache_dir / "repos",
            self.backup_dir,
            self.icons_dir,
            self.themes_dir,
            self.aurorae_dir,
            self.plasma_themes_dir,
            self.plasmoids_dir,
            self.wallpapers_dir,
            self.color_schemes_dir,
            self.kvantum_config_dir,
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode.value,
            "profile": self.profile.value,
            "components": self.components.to_dict(),
            "dry_run": self.dry_run,
            "headless": self.headless,
            "verbose": self.verbose,
        }

    def save_to_file(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2)

    @classmethod
    def load_from_file(cls, path: Path) -> EngineConfig:
        if not path.exists():
            return cls()
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        mode = ThemeMode(data.get("mode", ThemeMode.DARK.value))
        profile = PerformanceProfile(data.get("profile", PerformanceProfile.FULL_LIQUID_GLASS.value))
        components = ComponentOptions.from_dict(data.get("components", {}))
        return cls(
            mode=mode,
            profile=profile,
            components=components,
            dry_run=data.get("dry_run", False),
            headless=data.get("headless", False),
            verbose=data.get("verbose", False),
        )

#!/usr/bin/env python3
"""Tests for core.plasma_config and core.plasma_layout."""

import tempfile
import unittest
from pathlib import Path

from core.config import EngineConfig, PerformanceProfile, ThemeMode
from core.plasma_config import PlasmaConfigurator
from core.plasma_layout import PlasmaLayoutManager


class TestPlasmaConfig(unittest.TestCase):
    def test_direct_ini_write(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            cfg = EngineConfig(config_dir=tmp)
            plasma_cfg = PlasmaConfigurator(cfg)
            # Force direct file write (ignoring kwriteconfig binary)
            plasma_cfg.has_kwriteconfig = False

            # Apply window decorations
            plasma_cfg.apply_window_decorations(mode=ThemeMode.DARK)

            kwinrc = tmp / "kwinrc"
            self.assertTrue(kwinrc.exists())
            content = kwinrc.read_text()
            self.assertIn("ButtonsOnLeft=XIA", content)
            self.assertIn("ButtonsOnRight=", content)
            self.assertIn("__aurorae__svg__MacTahoe-dark", content)

    def test_kvantum_config(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            cfg = EngineConfig(config_dir=tmp)
            plasma_cfg = PlasmaConfigurator(cfg)
            plasma_cfg.has_kwriteconfig = False

            plasma_cfg.configure_kvantum(mode=ThemeMode.DARK, profile=PerformanceProfile.FULL_LIQUID_GLASS)
            kvconfig = tmp / "Kvantum" / "kvantum.kvconfig"
            self.assertTrue(kvconfig.exists())
            content = kvconfig.read_text()
            self.assertIn("theme=MacTahoe", content)

    def test_layout_template_interpolation(self):
        cfg = EngineConfig()
        cfg.components.top_panel_height = 28
        cfg.components.dock_height = 60
        mgr = PlasmaLayoutManager(cfg)
        script = mgr.generate_script()
        self.assertIn("var topHeight = 28;", script)
        self.assertIn("var dockHeight = 60;", script)
        self.assertIn("org.kde.plasma.appmenu", script)
        self.assertIn("org.kde.plasma.icontasks", script)


if __name__ == "__main__":
    unittest.main()

#!/usr/bin/env python3
"""Tests for core.plasma_config and core.plasma_layout."""

import tempfile
import unittest
from pathlib import Path

from core.config import EngineConfig, PerformanceProfile, ThemeMode
from core.plasma_config import PlasmaConfigurator, _write_ini_key_inplace
from core.plasma_layout import PlasmaLayoutManager


class TestPlasmaConfig(unittest.TestCase):
    def test_direct_ini_write_preserves_comments_and_sections(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            ini_file = Path(tmpdir) / "kwinrc"
            initial_content = (
                "# Global KWin configuration\n"
                "[$Version]\n"
                "update_info=kwin.upd:kwin-6.0\n"
                "\n"
                "[Desktops]\n"
                "Number=2\n"
                "\n"
                "[org.kde.kdecoration2]\n"
                "# Button layout comment\n"
                "ButtonsOnLeft=X\n"
                "BorderSize=Normal\n"
            )
            ini_file.write_text(initial_content)

            # Update existing key in existing section
            success = _write_ini_key_inplace(ini_file, "org.kde.kdecoration2", "ButtonsOnLeft", "XIA")
            self.assertTrue(success)

            # Insert new key in existing section
            success = _write_ini_key_inplace(ini_file, "org.kde.kdecoration2", "ButtonsOnRight", "")
            self.assertTrue(success)

            # Insert new section and key
            success = _write_ini_key_inplace(ini_file, "Plugins", "blurEnabled", "true")
            self.assertTrue(success)

            content = ini_file.read_text()
            # Verify comments and headers were preserved
            self.assertIn("# Global KWin configuration", content)
            self.assertIn("[$Version]", content)
            self.assertIn("update_info=kwin.upd:kwin-6.0", content)
            self.assertIn("[Desktops]", content)
            self.assertIn("Number=2", content)
            self.assertIn("# Button layout comment", content)
            # Verify updated keys
            self.assertIn("ButtonsOnLeft=XIA", content)
            self.assertIn("ButtonsOnRight=", content)
            self.assertIn("[Plugins]", content)
            self.assertIn("blurEnabled=true", content)

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

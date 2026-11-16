#!/usr/bin/env python3
"""Tests for core.config."""

import json
import tempfile
import unittest
from pathlib import Path

from core.config import ComponentOptions, EngineConfig, PerformanceProfile, ThemeMode


class TestConfig(unittest.TestCase):
    def test_default_config(self):
        cfg = EngineConfig()
        self.assertEqual(cfg.mode, ThemeMode.DARK)
        self.assertEqual(cfg.profile, PerformanceProfile.FULL_LIQUID_GLASS)
        self.assertEqual(cfg.components.dock_height, 56)
        self.assertEqual(cfg.components.top_panel_height, 28)
        self.assertTrue(cfg.components.install_plasma_theme)
        self.assertTrue(cfg.components.install_kwin_shaders)

    def test_serialization(self):
        cfg = EngineConfig(
            mode=ThemeMode.LIGHT,
            profile=PerformanceProfile.LITE_PERFORMANCE,
            components=ComponentOptions(dock_height=48, install_kwin_shaders=False),
        )
        data = cfg.to_dict()
        self.assertEqual(data["mode"], "light")
        self.assertEqual(data["profile"], "lite_performance")
        self.assertEqual(data["components"]["dock_height"], 48)
        self.assertFalse(data["components"]["install_kwin_shaders"])

    def test_save_and_load(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = Path(tmpdir) / "test_config.json"
            cfg = EngineConfig(
                mode=ThemeMode.LIGHT,
                profile=PerformanceProfile.LITE_PERFORMANCE,
                components=ComponentOptions(dock_height=64),
            )
            cfg.save_to_file(config_file)
            self.assertTrue(config_file.exists())

            loaded = EngineConfig.load_from_file(config_file)
            self.assertEqual(loaded.mode, ThemeMode.LIGHT)
            self.assertEqual(loaded.profile, PerformanceProfile.LITE_PERFORMANCE)
            self.assertEqual(loaded.components.dock_height, 64)

    def test_xdg_environment_variables(self):
        import os
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            custom_config = tmp / "custom_config"
            custom_data = tmp / "custom_data"
            custom_cache = tmp / "custom_cache"

            orig_config = os.environ.get("XDG_CONFIG_HOME")
            orig_data = os.environ.get("XDG_DATA_HOME")
            orig_cache = os.environ.get("XDG_CACHE_HOME")

            try:
                os.environ["XDG_CONFIG_HOME"] = str(custom_config)
                os.environ["XDG_DATA_HOME"] = str(custom_data)
                os.environ["XDG_CACHE_HOME"] = str(custom_cache)

                cfg = EngineConfig()
                self.assertEqual(cfg.config_dir, custom_config)
                self.assertEqual(cfg.cache_dir, custom_cache / "plasmatahoe")
                self.assertEqual(cfg.backup_dir, custom_data / "plasmatahoe" / "backups")
            finally:
                if orig_config is not None:
                    os.environ["XDG_CONFIG_HOME"] = orig_config
                else:
                    os.environ.pop("XDG_CONFIG_HOME", None)

                if orig_data is not None:
                    os.environ["XDG_DATA_HOME"] = orig_data
                else:
                    os.environ.pop("XDG_DATA_HOME", None)

                if orig_cache is not None:
                    os.environ["XDG_CACHE_HOME"] = orig_cache
                else:
                    os.environ.pop("XDG_CACHE_HOME", None)


if __name__ == "__main__":
    unittest.main()

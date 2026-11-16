#!/usr/bin/env python3
"""Tests for core.backup."""

import json
import tempfile
import unittest
from pathlib import Path

from core.backup import BackupManager


class TestBackup(unittest.TestCase):
    def test_backup_and_restore(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            home_dir = tmp / "home"
            backup_dir = tmp / "backups"
            config_dir = home_dir / ".config"
            config_dir.mkdir(parents=True, exist_ok=True)

            # Create mock config files
            (config_dir / "kwinrc").write_text("[org.kde.kdecoration2]\nButtonsOnLeft=XIA\n")
            (config_dir / "kdeglobals").write_text("[KDE]\nwidgetStyle=Breeze\n")

            mgr = BackupManager(backup_dir=backup_dir, home_dir=home_dir)

            # 1. Create backup
            arc_path = mgr.create_backup()
            self.assertIsNotNone(arc_path)
            self.assertTrue(arc_path.exists())

            # Verify sidecar manifest
            sidecar = arc_path.with_suffix(".json")
            self.assertTrue(sidecar.exists())
            with open(sidecar, "r", encoding="utf-8") as f:
                manifest = json.load(f)
            self.assertIn("kwinrc", manifest["files"])
            self.assertIn("kdeglobals", manifest["files"])

            # 2. List backups
            backups = mgr.list_backups()
            self.assertEqual(len(backups), 1)
            self.assertEqual(backups[0].archive_path, arc_path)

            # 3. Simulate modifications
            (config_dir / "kwinrc").write_text("[org.kde.kdecoration2]\nButtonsOnLeft=MODIFIED\n")

            # 4. Restore backup
            success = mgr.restore_backup(arc_path)
            self.assertTrue(success)

            # Check that original content was restored
            restored_content = (config_dir / "kwinrc").read_text()
            self.assertIn("ButtonsOnLeft=XIA", restored_content)


if __name__ == "__main__":
    unittest.main()

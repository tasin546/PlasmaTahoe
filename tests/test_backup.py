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

    def test_restore_path_traversal_rejection(self):
        import tarfile
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            home_dir = tmp / "home"
            backup_dir = tmp / "backups"
            config_dir = home_dir / ".config"
            config_dir.mkdir(parents=True, exist_ok=True)
            backup_dir.mkdir(parents=True, exist_ok=True)

            mgr = BackupManager(backup_dir=backup_dir, home_dir=home_dir)

            # Create a malicious tarball with path traversal entry
            archive_path = backup_dir / "backup_malicious.tar.gz"
            with tarfile.open(archive_path, "w:gz") as tar:
                # Normal entry
                normal_file = tmp / "normal.txt"
                normal_file.write_text("safe content")
                tar.add(normal_file, arcname="config/normal.txt")

                # Traversal entry
                from io import BytesIO
                traversal_data = b"malicious content"
                tarinfo = tarfile.TarInfo(name="config/../../escape.txt")
                tarinfo.size = len(traversal_data)
                tar.addfile(tarinfo, BytesIO(traversal_data))

            # Attempt restore
            warnings = []
            success = mgr.restore_backup(archive_path, log_cb=lambda msg, lvl: warnings.append(msg))
            self.assertTrue(success)

            # Normal file must be restored
            self.assertTrue((config_dir / "normal.txt").exists())
            # Escaped file MUST NOT exist outside config dir
            self.assertFalse((tmp / "escape.txt").exists())
            self.assertFalse((home_dir / "escape.txt").exists())


if __name__ == "__main__":
    unittest.main()

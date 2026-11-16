#!/usr/bin/env python3
"""Tests for core.distro."""

import tempfile
import unittest
from pathlib import Path

from core.config import PerformanceProfile
from core.distro import DistroResolver


class TestDistro(unittest.TestCase):
    def test_arch_detection(self):
        with tempfile.NamedTemporaryFile("w+", delete=False) as f:
            f.write('NAME="Arch Linux"\nID=arch\nPRETTY_NAME="Arch Linux"\n')
            f.flush()
            resolver = DistroResolver(os_release_path=Path(f.name))
            self.assertTrue(resolver.distro.is_arch_based)
            self.assertEqual(resolver.distro.package_manager, "pacman")

            pkgs_mode_a = resolver.get_package_list(PerformanceProfile.FULL_LIQUID_GLASS)
            self.assertIn("git", pkgs_mode_a)
            self.assertIn("kwin", pkgs_mode_a)
            self.assertIn("libplasma", pkgs_mode_a)

            pkgs_mode_b = resolver.get_package_list(PerformanceProfile.LITE_PERFORMANCE)
            self.assertIn("git", pkgs_mode_b)
            self.assertNotIn("kwin", pkgs_mode_b)

    def test_fedora_detection(self):
        with tempfile.NamedTemporaryFile("w+", delete=False) as f:
            f.write('NAME="Fedora Linux"\nID=fedora\nID_LIKE=""\n')
            f.flush()
            resolver = DistroResolver(os_release_path=Path(f.name))
            self.assertTrue(resolver.distro.is_fedora_based)
            self.assertEqual(resolver.distro.package_manager, "dnf")

            pkgs = resolver.get_package_list(PerformanceProfile.FULL_LIQUID_GLASS)
            self.assertIn("kwin-devel", pkgs)
            self.assertIn("qt6-qtbase-devel", pkgs)

    def test_ubuntu_detection(self):
        with tempfile.NamedTemporaryFile("w+", delete=False) as f:
            f.write('NAME="Ubuntu"\nID=ubuntu\nID_LIKE="debian"\n')
            f.flush()
            resolver = DistroResolver(os_release_path=Path(f.name))
            self.assertTrue(resolver.distro.is_debian_based)
            self.assertEqual(resolver.distro.package_manager, "apt")

            pkgs = resolver.get_package_list(PerformanceProfile.FULL_LIQUID_GLASS)
            self.assertIn("kwin-dev", pkgs)
            self.assertIn("qt6-base-dev", pkgs)

    def test_install_command_generation(self):
        with tempfile.NamedTemporaryFile("w+", delete=False) as f:
            f.write('ID=arch\n')
            f.flush()
            resolver = DistroResolver(os_release_path=Path(f.name))
            cmd = resolver.get_install_command(["git", "cmake"], use_pkexec=False)
            self.assertEqual(cmd[0], "sudo")
            self.assertIn("pacman", cmd)
            self.assertIn("git", cmd)


if __name__ == "__main__":
    unittest.main()

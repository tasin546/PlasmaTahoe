#!/usr/bin/env python3
"""Tests for core.hardware."""

import os
import unittest
from unittest.mock import patch

from core.config import PerformanceProfile
from core.hardware import HardwareDetector, HardwareProfile


class TestHardware(unittest.TestCase):
    def test_display_server_wayland(self):
        with patch.dict(os.environ, {"XDG_SESSION_TYPE": "wayland"}):
            self.assertEqual(HardwareDetector.detect_display_server(), "wayland")

    def test_display_server_x11(self):
        with patch.dict(os.environ, {"XDG_SESSION_TYPE": "x11"}):
            self.assertEqual(HardwareDetector.detect_display_server(), "x11")

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_gpu_nvidia_detection(self, mock_run, mock_which):
        mock_which.return_value = "/usr/bin/lspci"
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "01:00.0 VGA compatible controller [0300]: NVIDIA Corporation AD106 [GeForce RTX 4060] [10de:28e0] (rev a1)\n"

        vendor, model, is_dedicated, is_vm = HardwareDetector.detect_gpu()
        self.assertEqual(vendor, "NVIDIA")
        self.assertTrue(is_dedicated)
        self.assertFalse(is_vm)

    @patch("shutil.which")
    @patch("subprocess.run")
    def test_gpu_vm_detection(self, mock_run, mock_which):
        mock_which.return_value = "/usr/bin/lspci"
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "00:02.0 VGA compatible controller [0300]: VMware SVGA II Adapter [15ad:0405]\n"

        vendor, model, is_dedicated, is_vm = HardwareDetector.detect_gpu()
        self.assertEqual(vendor, "Virtual / Emulated")
        self.assertFalse(is_dedicated)
        self.assertTrue(is_vm)


if __name__ == "__main__":
    unittest.main()

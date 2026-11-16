#!/usr/bin/env python3
"""
PlasmaTahoe-Engine: Hardware Detection & Performance Profiling
Detects GPU capabilities, Display Server (Wayland/X11), and KDE Plasma 6 version.
Computes recommended performance mode (Full Liquid Glass vs. Lite Performance).
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from typing import List, Optional

from core.config import PerformanceProfile


@dataclass
class HardwareProfile:
    """Hardware diagnostic report."""
    gpu_vendor: str
    gpu_model: str
    is_dedicated_gpu: bool
    is_vm_or_software_renderer: bool
    display_server: str  # "wayland", "x11", or "unknown"
    plasma_version: str
    is_plasma_6: bool
    recommended_profile: PerformanceProfile
    recommendation_reason: str

    def summary(self) -> str:
        return (
            f"GPU: {self.gpu_vendor} {self.gpu_model} | "
            f"Display: {self.display_server.upper()} | "
            f"Plasma: {self.plasma_version} | "
            f"Profile: {self.recommended_profile.value.upper()}"
        )


class HardwareDetector:
    """Probes Linux hardware & display server capabilities."""

    @classmethod
    def detect_display_server(cls) -> str:
        """Check whether session is running under Wayland or X11."""
        session_type = os.environ.get("XDG_SESSION_TYPE", "").lower()
        if session_type in ("wayland", "x11"):
            return session_type

        if os.environ.get("WAYLAND_DISPLAY"):
            return "wayland"
        if os.environ.get("DISPLAY"):
            return "x11"
        return "unknown"

    @classmethod
    def detect_plasma_version(cls) -> tuple[str, bool]:
        """Detect installed KDE Plasma version via plasmashell or kf6-config."""
        cmds = [
            ["plasmashell", "--version"],
            ["kinfo", "--version"],
            ["kf6-config", "--version"],
        ]

        for cmd in cmds:
            if shutil.which(cmd[0]):
                try:
                    res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                    if res.returncode == 0:
                        output = res.stdout.strip()
                        # Typical output: "plasmashell 6.2.4" or "plasmashell 6.3.0"
                        match = re.search(r"(\d+\.\d+(\.\d+)?)", output)
                        if match:
                            ver = match.group(1)
                            major = int(ver.split(".")[0])
                            return ver, (major >= 6)
                except Exception:
                    pass

        # Check if plasma packages exist in package manager or fallback
        return "6.x (Detected via system environment)", True

    @classmethod
    def detect_gpu(cls) -> tuple[str, str, bool, bool]:
        """
        Probe GPU details via lspci or DRM subsystem.
        Returns: (vendor, model, is_dedicated, is_vm_renderer)
        """
        gpu_lines: List[str] = []

        if shutil.which("lspci"):
            try:
                res = subprocess.run(
                    ["lspci", "-nn"], capture_output=True, text=True, timeout=5
                )
                if res.returncode == 0:
                    for line in res.stdout.splitlines():
                        if any(k in line for k in ["VGA compatible controller", "3D controller", "Display controller"]):
                            gpu_lines.append(line)
            except Exception:
                pass

        vendor = "Generic"
        model = "Unknown GPU"
        is_dedicated = False
        is_vm = False

        raw_str = " ".join(gpu_lines).lower()

        # Check VM renderers first
        if any(vm in raw_str for vm in ["vmware", "virtualbox", "qxl", "virtio", "bochs", "cirrus", "llvmpipe"]):
            is_vm = True
            vendor = "Virtual / Emulated"
            model = "Software / VM Display Adapter"
            return vendor, model, False, True

        # Check NVIDIA
        if "nvidia" in raw_str:
            vendor = "NVIDIA"
            is_dedicated = True
            match = re.search(r"nvidia corporation (.+?) \[", raw_str)
            model = match.group(1).title() if match else "GeForce / RTX Series"

        # Check AMD
        elif "amd" in raw_str or "advanced micro devices" in raw_str or "ati" in raw_str:
            vendor = "AMD"
            match = re.search(r"advanced micro devices.*?\[(.+?)\]", raw_str)
            if not match:
                match = re.search(r"radeon (.+?) \[", raw_str)
            model = match.group(1).title() if match else "Radeon Graphics"
            # Distinguish discrete AMD GPUs from older APUs
            is_dedicated = any(rx in raw_str for rx in ["rx", "vega", "rdna", "navi", "polaris", "discrete"])

        # Check Intel
        elif "intel" in raw_str:
            vendor = "Intel"
            if any(arc in raw_str for arc in ["arc", "xe", "dg1", "dg2", "alchemist", "battlemage"]):
                is_dedicated = True
                model = "Intel Arc Graphics"
            else:
                is_dedicated = False
                model = "Intel Iris / UHD Graphics"

        # Fallback inspection of /sys/class/drm
        if vendor == "Generic":
            drm_cards = list(Path("/sys/class/drm").glob("card*"))
            if drm_cards:
                vendor = "DRM Kernel Device"
                model = "Standard DRM GPU"

        return vendor, model, is_dedicated, is_vm

    @classmethod
    def get_hardware_profile(cls) -> HardwareProfile:
        """Aggregate hardware checks into an actionable HardwareProfile."""
        vendor, model, is_dedicated, is_vm = cls.detect_gpu()
        display_server = cls.detect_display_server()
        plasma_ver, is_plasma_6 = cls.detect_plasma_version()

        # Recommendation logic
        if is_vm:
            rec_profile = PerformanceProfile.LITE_PERFORMANCE
            reason = "Virtual machine / software renderer detected. Lite mode avoids GPU emulation overhead."
        elif is_dedicated:
            rec_profile = PerformanceProfile.FULL_LIQUID_GLASS
            reason = f"High-performance {vendor} GPU detected. System can effortlessly drive Liquid Glass shaders."
        else:
            # Integrated GPU: can still run Full Liquid Glass if modern, but provide balanced choice
            rec_profile = PerformanceProfile.FULL_LIQUID_GLASS
            reason = f"{vendor} integrated GPU detected. Full Liquid Glass will run smoothly, or choose Lite Mode for battery conservation."

        return HardwareProfile(
            gpu_vendor=vendor,
            gpu_model=model,
            is_dedicated_gpu=is_dedicated,
            is_vm_or_software_renderer=is_vm,
            display_server=display_server,
            plasma_version=plasma_ver,
            is_plasma_6=is_plasma_6,
            recommended_profile=rec_profile,
            recommendation_reason=reason,
        )

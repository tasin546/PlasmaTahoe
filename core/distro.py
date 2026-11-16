#!/usr/bin/env python3
"""
PlasmaTahoe-Engine: Multi-Distro Dependency Resolution
Parses /etc/os-release and maps package requirements across Arch, Fedora, Debian/Ubuntu, openSUSE.
Executes installation via PolicyKit (pkexec) or authenticated sudo.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, List, Optional

from core.config import PerformanceProfile


@dataclass
class DistroInfo:
    """Information parsed from /etc/os-release."""
    id: str
    id_like: List[str]
    name: str
    version_id: str
    package_manager: str

    @property
    def is_arch_based(self) -> bool:
        return self.id in ("arch", "cachyos", "endeavouros", "manjaro", "garuda") or "arch" in self.id_like

    @property
    def is_fedora_based(self) -> bool:
        return self.id in ("fedora", "nobara", "rhel", "centos") or "fedora" in self.id_like

    @property
    def is_debian_based(self) -> bool:
        return self.id in ("debian", "ubuntu", "neon", "kubuntu", "pop", "linuxmint") or any(
            x in self.id_like for x in ("debian", "ubuntu")
        )

    @property
    def is_suse_based(self) -> bool:
        return self.id in ("opensuse-tumbleweed", "opensuse-leap", "suse") or "suse" in self.id_like


class DistroResolver:
    """Detects system distribution and resolves/installs system dependencies."""

    # Core build and runtime dependencies mapped per package manager family
    PACKAGE_MAP: Dict[str, Dict[str, List[str]]] = {
        "pacman": {
            "core": [
                "git", "cmake", "extra-cmake-modules", "ninja", "gcc",
                "pkgconf", "qt6-base", "qt6-declarative", "qt6-svg",
                "kvantum", "sassc", "gtk-engine-murrine", "jq", "gettext"
            ],
            "plasma6_dev": [
                "kwin", "libplasma", "wayland-protocols"
            ],
            "pyqt6": [
                "python-pyqt6"
            ]
        },
        "dnf": {
            "core": [
                "git", "cmake", "extra-cmake-modules", "ninja-build", "gcc-c++",
                "qt6-qtbase-devel", "qt6-qtdeclarative-devel", "qt6-qtsvg-devel",
                "kvantum", "sassc", "gtk-murrine-engine", "jq", "gettext"
            ],
            "plasma6_dev": [
                "kwin-devel", "libplasma-devel"
            ],
            "pyqt6": [
                "python3-pyqt6"
            ]
        },
        "apt": {
            "core": [
                "git", "cmake", "extra-cmake-modules", "ninja-build", "g++",
                "qt6-base-dev", "qt6-declarative-dev", "qt6-svg-dev",
                "kvantum", "sassc", "gtk2-engines-murrine", "jq", "gettext"
            ],
            "plasma6_dev": [
                "kwin-dev", "libplasma-dev"
            ],
            "pyqt6": [
                "python3-pyqt6"
            ]
        },
        "zypper": {
            "core": [
                "git", "cmake", "extra-cmake-modules", "ninja", "gcc-c++",
                "qt6-base-devel", "qt6-declarative-devel", "qt6-svg-devel",
                "kvantum", "sassc", "gtk2-engine-murrine", "jq", "gettext-tools"
            ],
            "plasma6_dev": [
                "kwin6-devel", "libplasma6-devel"
            ],
            "pyqt6": [
                "python3-qt6"
            ]
        }
    }

    def __init__(self, os_release_path: Path = Path("/etc/os-release")) -> None:
        self.os_release_path = os_release_path
        self.distro = self.detect_distro()

    def detect_distro(self) -> DistroInfo:
        """Parse /etc/os-release or provide a safe fallback."""
        data: Dict[str, str] = {}
        if self.os_release_path.exists():
            with open(self.os_release_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    data[k.strip()] = v.strip().strip('"').strip("'")

        distro_id = data.get("ID", "unknown").lower()
        id_like = [x.lower() for x in data.get("ID_LIKE", "").split()]
        name = data.get("PRETTY_NAME", data.get("NAME", "Unknown Linux"))
        version_id = data.get("VERSION_ID", "rolling")

        # Determine package manager by distribution ID first, fallback to binary detection
        pm = "unknown"
        if distro_id in ("arch", "cachyos", "endeavouros", "manjaro", "garuda") or "arch" in id_like:
            pm = "pacman"
        elif distro_id in ("fedora", "nobara", "rhel", "centos") or "fedora" in id_like:
            pm = "dnf"
        elif distro_id in ("debian", "ubuntu", "neon", "kubuntu", "pop", "linuxmint") or any(x in id_like for x in ("debian", "ubuntu")):
            pm = "apt"
        elif distro_id in ("opensuse-tumbleweed", "opensuse-leap", "suse") or "suse" in id_like:
            pm = "zypper"
        elif shutil.which("pacman"):
            pm = "pacman"
        elif shutil.which("dnf"):
            pm = "dnf"
        elif shutil.which("apt"):
            pm = "apt"
        elif shutil.which("zypper"):
            pm = "zypper"

        return DistroInfo(
            id=distro_id,
            id_like=id_like,
            name=name,
            version_id=version_id,
            package_manager=pm,
        )

    def get_package_list(self, profile: PerformanceProfile, include_pyqt: bool = True) -> List[str]:
        """Compute the complete list of distro package names needed."""
        pm = self.distro.package_manager
        if pm not in self.PACKAGE_MAP:
            return []

        mapping = self.PACKAGE_MAP[pm]
        pkgs = list(mapping.get("core", []))

        # Only require kwin development headers if building Mode A (C++ shaders)
        if profile == PerformanceProfile.FULL_LIQUID_GLASS:
            pkgs.extend(mapping.get("plasma6_dev", []))

        if include_pyqt:
            pkgs.extend(mapping.get("pyqt6", []))

        return pkgs

    def get_install_command(self, packages: List[str], use_pkexec: bool = True) -> List[str]:
        """Construct the root command to install packages using pkexec or sudo."""
        if not packages:
            return []

        pm = self.distro.package_manager
        auth = "pkexec" if use_pkexec and shutil.which("pkexec") else "sudo"

        if pm == "pacman":
            return [auth, "pacman", "-S", "--needed", "--noconfirm"] + packages
        elif pm == "dnf":
            return [auth, "dnf", "install", "-y"] + packages
        elif pm == "apt":
            return [auth, "apt-get", "install", "-y", "--no-install-recommends"] + packages
        elif pm == "zypper":
            return [auth, "zypper", "--non-interactive", "install"] + packages

        raise RuntimeError(f"Unsupported package manager: {pm}")

    def check_development_headers(self, profile: PerformanceProfile) -> bool:
        """
        Check if KWin and Qt6 C++ development headers/cmake configs are installed.
        Only required when compiling C++ shaders in FULL_LIQUID_GLASS profile.
        """
        if profile != PerformanceProfile.FULL_LIQUID_GLASS:
            return True

        kwin_cmake_paths = [
            "/usr/lib/cmake/KWin",
            "/usr/lib64/cmake/KWin",
            "/usr/lib/x86_64-linux-gnu/cmake/KWin",
            "/usr/include/kwin",
            "/usr/include/KWin",
        ]
        return any(Path(p).exists() for p in kwin_cmake_paths)

    def check_missing_commands(self) -> List[str]:
        """Check essential CLI tools present on PATH."""
        required = ["git", "cmake", "sassc"]
        return [cmd for cmd in required if not shutil.which(cmd)]

    def install_dependencies(
        self,
        profile: PerformanceProfile,
        use_pkexec: bool = True,
        log_cb: Optional[Callable[[str, str], None]] = None,
        dry_run: bool = False,
    ) -> bool:
        """
        Execute package manager installation.
        Streams stdout/stderr to log_cb.
        """
        packages = self.get_package_list(profile)
        if not packages:
            if log_cb:
                log_cb(f"No package mapping found for distro: {self.distro.name}", "WARN")
            return False

        cmd = self.get_install_command(packages, use_pkexec=use_pkexec)
        if dry_run:
            if log_cb:
                log_cb(f"[DRY-RUN] Would execute package installation: {' '.join(cmd)}", "INFO")
            return True

        if log_cb:
            log_cb(f"Executing: {' '.join(cmd)}", "INFO")

        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )

            if process.stdout:
                for line in iter(process.stdout.readline, ""):
                    clean = line.strip()
                    if clean and log_cb:
                        log_cb(clean, "INFO")

            process.wait()
            if process.returncode == 0:
                if log_cb:
                    log_cb("Package installation completed successfully.", "SUCCESS")
                return True
            else:
                if log_cb:
                    log_cb(f"Package installation failed with exit code {process.returncode}", "ERROR")
                return False

        except Exception as e:
            if log_cb:
                log_cb(f"Failed to run installer: {str(e)}", "ERROR")
            return False

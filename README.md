# PlasmaTahoe-Engine 🌊🪟

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python: 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Target: KDE Plasma 6.2+](https://img.shields.io/badge/KDE%20Plasma-6.2+-5277C3.svg)](https://kde.org/plasma-desktop/)
[![Display: Wayland & X11](https://img.shields.io/badge/Display-Wayland%20%7C%20X11-success.svg)](https://wayland.freedesktop.org/)
[![Status: Production Ready](https://img.shields.io/badge/Status-Production%20Ready-brightgreen.svg)]()

> **PlasmaTahoe-Engine** is a complete, production-grade, open-source desktop customizer for **KDE Plasma 6.2+**. It transforms any standard KDE Plasma 6 desktop into a near-1:1 **macOS Tahoe "Liquid Glass"** environment—orchestrating native KWin GLSL refraction shaders, translucent Kvantum application styling, a top global menu bar, a floating dock, squircle icons, custom High-DPI cursors, and frosted glass QML desktop widgets.

---

## 🌟 Visual Preview

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│   File  Edit  View  Go  Window  Help               [Weather 21°C]  (Tray)  Nov 16 11:45 PM │
├────────────────────────────────────────────────────────────────────────────────────────┤
│                                                                                        │
│     ┌──────────────────────────────────────────────────────────────┐                   │
│     │  🔴 🟡 🟢  Dolphin                                   [Search] │                   │
│     ├──────────────┬───────────────────────────────────────────────┤                   │
│     │  Places      │   Name             Size       Modified        │                   │
│     │  📁 Home     │   📄 Documents     --         Today           │                   │
│     │  📁 Desktop  │   📄 Downloads     --         Yesterday       │                   │
│     │  📁 Code     │   📄 Pictures      --         Last week       │                   │
│     └──────────────┴───────────────────────────────────────────────┘                   │
│                                                                                        │
│                         ╭────────────────────────────────╮                             │
│                         │  Finder  Browser  Terminal  ⚙️ │  🗑️ │ (Floating Dock: 56px)  │
│                         ╰────────────────────────────────╯                             │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Key Architectural Features

- **Liquid Glass KWin Shaders & Refraction**:
  Compiles and enables native C++ KWin effects (`kwin-effects-better-blur-dx` and `KDE-Rounded-Corners`) for vibrant background blur, specular edge highlight reflections, and anti-aliased squircle window borders.
- **Hardware Performance Profiling**:
  Automatically detects discrete vs. integrated/virtual GPUs (`lspci -nn` / DRM) and selects:
  - **Mode A (Full Liquid Glass)**: Modern AMD Radeon, NVIDIA GeForce/RTX, and Intel Arc GPUs.
  - **Mode B (Lite / Performance)**: 60 FPS zero-bottleneck mode for older Intel HD iGPUs, Virtual Machines (VMware/VirtualBox/QEMU), or battery conservation.
- **Top Global Menu & Floating Dock Automation**:
  Programmatically removes default panels and applies a 28px Top Panel (Kickoff/KppleMenu, Global Menu, Spacer, System Tray, Digital Clock) and a 56px Floating Bottom Dock (`lengthMode = "fit"`, `hiding = "dodgewindows"`) via PlasmaShell's native D-Bus JS scripting engine.
- **Official Plasma 6 CLI Tools**:
  Uses `kwriteconfig6`, `lookandfeeltool`, `plasma-apply-colorscheme`, `plasma-apply-cursortheme`, and `qdbus6` rather than fragile regex text replacements.
- **Atomic Pre-Flight Backup & 1-Click Rollback**:
  Archives `~/.config/kdeglobals`, `kwinrc`, `plasmarc`, `dolphinrc`, `krunnerrc`, and `Kvantum/` into timestamped tarballs with SHA256 manifests before any changes occur.
- **Centered Spotlight Search**:
  Maps `Meta+Space` (or `Alt+Space`) to a centered, free-floating KRunner instance.
- **Dolphin macOS Styling**:
  Configures translucent sidebars, clean icon view defaults, and hides the legacy menu bar in favor of a sleek hamburger button.
- **Flatpak Consistency**:
  Applies user-level overrides (`flatpak override --user --filesystem=xdg-config/Kvantum:ro`) so sandboxed applications seamlessly inherit the Tahoe glass style.

---

## 📦 Supported Linux Distributions

| Distribution | Package Manager | Automatic Resolution |
| :--- | :---: | :---: |
| **Arch Linux / CachyOS / EndeavourOS / Manjaro** | `pacman` | ✅ Supported |
| **Fedora / Nobara / RHEL** | `dnf` | ✅ Supported |
| **Ubuntu / Debian / KDE Neon / Kubuntu** | `apt` | ✅ Supported |
| **openSUSE Tumbleweed / Leap** | `zypper` | ✅ Supported |

---

## 🛠️ Installation & Usage

### 1. Requirements

Ensure you are running **KDE Plasma 6.0+** on either **Wayland** (recommended) or **X11**.

```bash
# Clone the repository
git clone https://github.com/tasin/plasmatahoe.git
cd plasmatahoe

# (Optional) Install Python GUI dependency if not already installed by your package manager:
pip install -r requirements.txt
```

### 2. Launching the PyQt6 Graphical Wizard

Run without arguments to launch the Liquid Glass wizard:

```bash
python3 main.py
```

The GUI wizard includes:
- **System Check Page**: Shows your Distro, Plasma 6 version, Display Server, and GPU recommendation.
- **Customization Options Page**: Switch between Full Liquid Glass (Mode A) and Lite Mode (Mode B), adjust Dock height slider, and toggle components.
- **Live Execution Console**: Real-time progress bar and streaming logs on background worker threads without freezing the UI.
- **Backups & Restore Tab**: Inspect saved snapshots with manifests and perform one-click rollbacks.

### 3. Headless CLI Mode

PlasmaTahoe-Engine can be executed entirely via command-line flags without X11/Wayland GUI dependencies:

```bash
# Standard automated setup (Mode A: Full Liquid Glass, Dark Mode)
python3 main.py --headless

# Lite / Performance setup for Virtual Machines or older iGPUs
python3 main.py --headless --lite

# Light theme variant with 48px dock
python3 main.py --headless --light --dock-height 48

# Inspect detected hardware and recommended profile without modifying anything
python3 main.py --check-system

# Create an immediate pre-flight configuration backup
python3 main.py --backup-only

# List all saved configuration backups
python3 main.py --list-backups

# Rollback to the latest saved backup snapshot
python3 main.py --restore latest

# Rollback to a specific snapshot
python3 main.py --restore backup_20261116_235846.tar.gz
```

---

## ⚙️ CLI Flags Reference

| Flag | Description |
| :--- | :--- |
| `--headless` | Run transformation in terminal without GUI wizard |
| `--lite` | Activate Mode B (Lite / Performance mode for older GPUs/VMs) |
| `--full` | Activate Mode A (Full Liquid Glass mode with C++ shaders) |
| `--dark` | Force macOS Tahoe Dark variant (default) |
| `--light` | Force macOS Tahoe Light variant |
| `--dock-height <px>` | Customize bottom floating dock height (default: `56`) |
| `--check-system` | Print system, distro, display server, and GPU diagnostics |
| `--backup-only` | Create an atomic snapshot of current KDE configs and exit |
| `--list-backups` | List all saved desktop snapshots |
| `--restore [FILE]` | Rollback to specified backup snapshot (or `latest`) |
| `--skip-shaders` | Skip C++ KWin shader compilation |
| `--skip-layout` | Skip panel and dock layout re-creation |
| `--dry-run` | Simulate checks and installation without altering disk |
| `--verbose`, `-v` | Enable detailed debug output |

---

## 🗂️ Project Architecture

```
plasmatahoe-engine/
├── assets/
│   ├── icons/                  # Libre SVGs (Apple distributor logo, Tahoe badges)
│   ├── wallpapers/             # Libre 4K/5K Liquid Glass vector wallpapers
│   └── styles/
│       └── liquid_glass.qss    # Frosted glass stylesheet for PyQt6
├── core/
│   ├── __init__.py
│   ├── config.py               # Dataclass schemas and path definitions
│   ├── distro.py               # /etc/os-release parser & multi-distro package installer
│   ├── hardware.py             # GPU detection & hardware performance profiling
│   ├── backup.py               # Pre-flight atomic snapshot manager & manifest builder
│   ├── git_repos.py            # Upstream git cloner, updater & CMake/meson builder
│   ├── plasma_config.py        # Official KDE Plasma 6 CLI configuration tools
│   ├── plasma_layout.py        # Layout script evaluator via PlasmaShell D-Bus
│   ├── plasma_layout.js        # JavaScript layout for Top Panel & Floating Dock
│   └── runner.py               # Central multi-phase pipeline orchestrator
├── ui/
│   ├── __init__.py
│   ├── styles.py               # Liquid Glass dark/light theme stylesheet for PyQt6
│   └── wizard.py               # PyQt6 multi-page desktop wizard with worker threads
├── scripts/
│   ├── install_dependencies.sh # Defensive bash script for distro dependencies
│   ├── apply_plasma_layout.sh  # Standalone script to apply Plasma 6 JS layout
│   └── rollback.sh             # Snapshot rollback helper
├── tests/
│   ├── test_config.py          # Config serialization & options tests
│   ├── test_distro.py          # Multi-distro package mapping tests
│   ├── test_hardware.py        # GPU and display server probing tests
│   ├── test_backup.py          # Snapshot backup & checksum verification tests
│   └── test_plasma_config.py   # INI config & layout template interpolation tests
├── main.py                     # Unified CLI / GUI entry point
├── pyproject.toml              # Modern Python packaging configuration
├── requirements.txt            # Python dependencies
├── LICENSE                     # GNU General Public License v3.0 (GPL-3.0)
├── CHANGELOG.md                # Release history and notes
└── README.md                   # Project documentation
```

---

## 🛡️ Upstream Open-Source Projects & Author Attributions

PlasmaTahoe-Engine orchestrates real, actively maintained open-source projects. All licenses (GPL-3.0 / LGPL-3.0) and author copyrights are strictly preserved:

1. **[MacTahoe-kde](https://github.com/vinceliuice/MacTahoe-kde)** & **[WhiteSur-kde](https://github.com/vinceliuice/WhiteSur-kde)**
   *Author:* **Vince Liuice** — Plasma desktop themes, Kvantum themes, Aurorae window decorations, and wallpapers.
2. **[MacTahoe-gtk-theme](https://github.com/vinceliuice/MacTahoe-gtk-theme)** & **[MacTahoe-icon-theme](https://github.com/vinceliuice/MacTahoe-icon-theme)**
   *Author:* **Vince Liuice** — GTK3/4, Libadwaita stylesheets, squircle icons, and cursors.
3. **[liquidglass-kde-widgets](https://github.com/jaxparrow07/liquidglass-kde-widgets)**
   *Author:* **Jack Faith (jaxparrow07)** — Liquid Glass frosted QML plasmoids for KDE Plasma 6 (Calendar, Clock, Music, Weather).
4. **[kwin-effects-better-blur-dx](https://github.com/xarblu/kwin-effects-better-blur-dx)**
   *Author:* **xarblu / taj-ny** — C++ KWin shader effect providing glass refraction and force blur.
5. **[KDE-Rounded-Corners](https://github.com/matinlotfali/KDE-Rounded-Corners)**
   *Author:* **Matin Lotfali** — Shader-based anti-aliased rounded corner window clipping for KWin.
6. **[kppleMenu](https://github.com/ChrTall/kppleMenu)**
   *Author:* **ChrTall / kppleos** — macOS-style top bar application menu for KDE Plasma 6.
7. **[plasma-panel-colorizer](https://github.com/luisbocanegra/plasma-panel-colorizer)**
   *Author:* **Luis Bocanegra** — Dynamic widget island and panel background manager.

---

## ⚖️ Legal & Trademark Notice

PlasmaTahoe-Engine is an independent open-source configuration orchestrator for KDE Plasma.
- **No proprietary Apple Inc. assets** (such as San Francisco font files, official macOS wallpapers, or macOS system sounds) are bundled.
- All included icons, themes, and shaders are distributed under **GPL-3.0 / LGPL-3.0 / CC-BY-SA** by their respective open-source authors.
- macOS, Apple, and Tahoe are trademarks of Apple Inc., registered in the U.S. and other countries. This project is not affiliated with, endorsed by, or sponsored by Apple Inc.

---

## 📄 License

Licensed under the **GNU General Public License v3.0** (GPL-3.0). See [LICENSE](LICENSE) for full details.

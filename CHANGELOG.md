# Changelog

All notable changes to **PlasmaTahoe-Engine** will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2026-11-16

### Initial Public Release

#### Added
- **Multi-Distro Dependency Resolution (`core/distro.py`)**:
  - Automatic detection of Arch Linux, Fedora, Ubuntu/Debian, openSUSE via `/etc/os-release`.
  - Non-interactive and PolicyKit (`pkexec`) / `sudo` package installation.
- **Hardware Performance Profiles (`core/hardware.py`)**:
  - GPU vendor/model detection via `lspci -nn` and DRM subsystem.
  - **Mode A — Full Liquid Glass**: Compiles C++ KWin GLSL shaders (`better-blur-dx`, `KDE-Rounded-Corners`), activates refractive glass blur and edge highlights.
  - **Mode B — Lite / Performance Mode**: Tailored for virtual machines, older Intel HD iGPUs, and battery saving (60 FPS, opaque fallback).
- **KDE Plasma 6 Automation Engine (`core/plasma_config.py` & `core/plasma_layout.js`)**:
  - Official Plasma 6 CLI tooling (`kwriteconfig6`, `lookandfeeltool`, `plasma-apply-colorscheme`, `plasma-apply-cursortheme`, `qdbus6`).
  - Window traffic lights on the left (`ButtonsOnLeft XIA`).
  - Kvantum application styling and Flatpak sandboxed app overrides.
  - Dolphin file manager macOS-style layout (clean toolbar, hidden menubar, icons view).
  - Centered KRunner Spotlight search mapped to `Meta+Space`.
  - Programmatic Plasma 6 Top Panel (`height = 28`, Global Menu, Clock, Spacer, System Tray) and Bottom Floating Dock (`height = 56`, `lengthMode = fit`, `hiding = dodgewindows`, pinned favorites).
- **Atomic Pre-Flight Backup & Rollback (`core/backup.py`)**:
  - Creates timestamped tarball archives in `~/.local/share/plasmatahoe/backups/` before any file write.
  - Generates detailed `manifest.json` with file checksums, plasmoid inventory, and distro state.
  - 1-Click rollback restores files and gracefully restarts `plasmashell` & `kwin`.
- **PyQt6 Real-Time GUI Wizard (`ui/wizard.py` & `ui/styles.py`)**:
  - Sleek macOS Tahoe "Liquid Glass" translucent interface with custom QSS styling.
  - Live console streaming logs in background `QThread` with responsive progress bar.
  - Backup inspection and rollback tab.
- **Full Headless CLI Support**:
  - Flags for automation: `--headless`, `--lite`, `--full`, `--dark`, `--light`, `--restore`, `--backup-only`, `--check-system`.
- **Upstream Open-Source Integration**:
  - Vinceliuice (`MacTahoe-kde`, `MacTahoe-gtk-theme`, `MacTahoe-icon-theme`, `WhiteSur-cursors`).
  - Jaxparrow07 (`liquidglass-kde-widgets`).
  - Xarblu (`kwin-effects-better-blur-dx`).
  - Matin Lotfali (`KDE-Rounded-Corners`).
  - ChrTall (`kppleMenu`) and Luis Bocanegra (`plasma-panel-colorizer`).

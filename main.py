#!/usr/bin/env python3
"""
PlasmaTahoe-Engine: Open-Source KDE Plasma 6 macOS Tahoe Customizer
Main CLI and GUI entry point.
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.resolve()))

from core.backup import BackupManager
from core.config import ComponentOptions, EngineConfig, PerformanceProfile, ThemeMode
from core.distro import DistroResolver
from core.hardware import HardwareDetector
from core.runner import PipelineRunner
from ui.wizard import PYQT6_AVAILABLE, launch_gui


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="PlasmaTahoe-Engine: Transform KDE Plasma 6 into a macOS Tahoe Liquid Glass desktop.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )

    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run transformation in terminal without launching PyQt6 GUI wizard.",
    )
    parser.add_argument(
        "--lite",
        action="store_true",
        help="Mode B: Lite / Performance mode (disables C++ shaders, uses opaque style, 60 FPS for older GPUs/VMs).",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Mode A: Full Liquid Glass mode (compiles C++ BetterBlurDX shaders and Rounded Corners).",
    )
    parser.add_argument(
        "--dark",
        action="store_true",
        help="Apply macOS Tahoe Dark theme variant.",
    )
    parser.add_argument(
        "--light",
        action="store_true",
        help="Apply macOS Tahoe Light theme variant.",
    )
    parser.add_argument(
        "--dock-height",
        type=int,
        default=56,
        help="Height in pixels for the bottom floating dock.",
    )
    parser.add_argument(
        "--check-system",
        action="store_true",
        help="Print detected Linux distro, KDE version, Display Server, and GPU diagnostics then exit.",
    )
    parser.add_argument(
        "--backup-only",
        action="store_true",
        help="Create an atomic snapshot backup of existing KDE configs and exit.",
    )
    parser.add_argument(
        "--list-backups",
        action="store_true",
        help="List all saved KDE configuration snapshots.",
    )
    parser.add_argument(
        "--restore",
        nargs="?",
        const="latest",
        help="Rollback desktop to a saved backup snapshot (specify filename or omit for latest).",
    )
    parser.add_argument(
        "--skip-shaders",
        action="store_true",
        help="Skip C++ KWin shader compilation.",
    )
    parser.add_argument(
        "--skip-layout",
        action="store_true",
        help="Skip Plasma 6 panel & dock layout replacement.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform pre-flight checks and simulate installation without altering files.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable detailed verbose debug output.",
    )

    return parser.parse_args()


def print_system_info() -> None:
    print("=" * 65)
    print("  PlasmaTahoe-Engine: System Diagnostics")
    print("=" * 65)

    distro_res = DistroResolver()
    d = distro_res.distro
    print(f"  Distribution:      {d.name} (ID: {d.id})")
    print(f"  Package Manager:   {d.package_manager.upper()}")

    hw = HardwareDetector.get_hardware_profile()
    print(f"  Desktop:           KDE Plasma {hw.plasma_version}")
    print(f"  Display Server:    {hw.display_server.upper()}")
    print(f"  GPU Vendor:        {hw.gpu_vendor}")
    print(f"  GPU Model:         {hw.gpu_model}")
    print(f"  Dedicated GPU:     {'Yes' if hw.is_dedicated_gpu else 'No'}")
    print(f"  Virtual/Software:  {'Yes' if hw.is_vm_or_software_renderer else 'No'}")
    print(f"  Recommended Mode:  {hw.recommended_profile.value.upper()}")
    print(f"  Reason:            {hw.recommendation_reason}")
    print("=" * 65)


def handle_cli_mode(args: argparse.Namespace) -> int:
    config = EngineConfig()
    config.dry_run = args.dry_run
    config.verbose = args.verbose
    config.headless = True

    # Mode selection
    if args.light:
        config.mode = ThemeMode.LIGHT
    else:
        config.mode = ThemeMode.DARK

    # Profile selection
    if args.lite:
        config.profile = PerformanceProfile.LITE_PERFORMANCE
    elif args.full:
        config.profile = PerformanceProfile.FULL_LIQUID_GLASS
    else:
        # Detect recommended profile
        hw = HardwareDetector.get_hardware_profile()
        config.profile = hw.recommended_profile

    # Component options
    config.components.dock_height = args.dock_height
    if args.skip_shaders:
        config.components.install_kwin_shaders = False
    if args.skip_layout:
        config.components.apply_plasma_layout = False

    def cli_progress(pct: int, msg: str) -> None:
        bar_len = 30
        filled = int(bar_len * (pct / 100.0))
        bar = "█" * filled + "░" * (bar_len - filled)
        print(f"\r[{bar}] {pct:3d}% — {msg:<45}", end="", flush=True)
        if pct >= 100:
            print()

    def cli_log(text: str, level: str) -> None:
        if level == "DEBUG" and not config.verbose:
            return
        prefix = {
            "INFO": "\033[36m[INFO]\033[0m",
            "SUCCESS": "\033[32m[SUCCESS]\033[0m",
            "WARN": "\033[33m[WARN]\033[0m",
            "ERROR": "\033[31m[ERROR]\033[0m",
            "DEBUG": "\033[90m[DEBUG]\033[0m",
        }.get(level, f"[{level}]")
        print(f"\n{prefix} {text}")

    print("\nStarting PlasmaTahoe-Engine Transformation (Headless CLI Mode)")
    print(f"Mode: {config.mode.value.upper()} | Profile: {config.profile.value.upper()}")
    print(f"Dock Height: {config.components.dock_height}px\n")

    runner = PipelineRunner(config)
    success = runner.run(progress_cb=cli_progress, log_cb=cli_log)

    if success:
        print("\n\033[32m✔ PlasmaTahoe transformation completed successfully!\033[0m")
        return 0
    else:
        print("\n\033[31m✖ Transformation completed with errors. See output above.\033[0m")
        return 1


def main() -> int:
    args = parse_arguments()

    if args.check_system:
        print_system_info()
        return 0

    backup_mgr = BackupManager()

    if args.backup_only:
        print("Creating pre-flight snapshot backup...")
        arc = backup_mgr.create_backup(log_cb=lambda t, l: print(f"[{l}] {t}"))
        if arc:
            print(f"Backup created at: {arc}")
            return 0
        return 1

    if args.list_backups:
        backups = backup_mgr.list_backups()
        print(f"\nFound {len(backups)} configuration snapshot(s):")
        print("-" * 65)
        for b in backups:
            print(f"• {b.archive_path.name} | {b.formatted_date} | {b.size_human} ({b.files_count} files)")
        print("-" * 65)
        return 0

    if args.restore:
        backups = backup_mgr.list_backups()
        if not backups:
            print("No saved backups found in ~/.local/share/plasmatahoe/backups/")
            return 1

        target_arc: Optional[Path] = None
        if args.restore == "latest":
            target_arc = backups[0].archive_path
        else:
            for b in backups:
                if b.archive_path.name == args.restore or str(b.archive_path) == args.restore:
                    target_arc = b.archive_path
                    break

        if not target_arc or not target_arc.exists():
            print(f"Snapshot '{args.restore}' not found.")
            return 1

        print(f"Restoring desktop configuration from: {target_arc.name}...")
        ok = backup_mgr.restore_backup(target_arc, log_cb=lambda t, l: print(f"[{l}] {t}"))
        return 0 if ok else 1

    # Check whether to launch GUI or Headless CLI
    has_display = bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    if args.headless or not has_display or not PYQT6_AVAILABLE:
        if not args.headless and not PYQT6_AVAILABLE:
            print("Note: PyQt6 is not installed on this system. Falling back to CLI mode.")
        elif not args.headless and not has_display:
            print("Note: No graphical display server detected. Falling back to CLI mode.")
        return handle_cli_mode(args)

    # Launch PyQt6 GUI Wizard
    cfg = EngineConfig()
    cfg.mode = ThemeMode.LIGHT if args.light else ThemeMode.DARK
    if args.lite:
        cfg.profile = PerformanceProfile.LITE_PERFORMANCE
    elif args.full:
        cfg.profile = PerformanceProfile.FULL_LIQUID_GLASS
    cfg.components.dock_height = args.dock_height

    return launch_gui(config=cfg)


if __name__ == "__main__":
    sys.exit(main())

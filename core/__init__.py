"""PlasmaTahoe-Engine: Core Package"""
from core.config import EngineConfig, PerformanceProfile, ThemeMode, ComponentOptions
from core.distro import DistroResolver, DistroInfo
from core.hardware import HardwareDetector, HardwareProfile
from core.backup import BackupManager, BackupInfo
from core.git_repos import GitRepoManager
from core.plasma_config import PlasmaConfigurator
from core.plasma_layout import PlasmaLayoutManager
from core.runner import PipelineRunner

__all__ = [
    "EngineConfig",
    "PerformanceProfile",
    "ThemeMode",
    "ComponentOptions",
    "DistroResolver",
    "DistroInfo",
    "HardwareDetector",
    "HardwareProfile",
    "BackupManager",
    "BackupInfo",
    "GitRepoManager",
    "PlasmaConfigurator",
    "PlasmaLayoutManager",
    "PipelineRunner",
]

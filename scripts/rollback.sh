#!/usr/bin/env bash
# ==============================================================================
# PlasmaTahoe-Engine: 1-Click Rollback & Restore Script
# Restores KDE Plasma configuration snapshot and restarts desktop services
# ==============================================================================

set -Eeuo pipefail
IFS=$'\n\t'

BACKUP_DIR="${XDG_DATA_HOME:-${HOME}/.local/share}/plasmatahoe/backups"
CONFIG_DIR="${XDG_CONFIG_HOME:-${HOME}/.config}"
TARGET_SNAPSHOT="${1:-latest}"

log_info()    { printf "\033[36m[INFO]\033[0m %s\n" "$*"; }
log_success() { printf "\033[32m[SUCCESS]\033[0m %s\n" "$*"; }
log_error()   { printf "\033[31m[ERROR]\033[0m %s\n" "$*" >&2; }

trap 'log_error "Rollback failed at line $LINENO: exit code $?"' ERR

if [[ ! -d "$BACKUP_DIR" ]]; then
    log_error "No backups directory found at $BACKUP_DIR"
    exit 1
fi

ARCHIVE_PATH=""

if [[ "$TARGET_SNAPSHOT" == "latest" ]]; then
    ARCHIVE_PATH="$(find "$BACKUP_DIR" -name "backup_*.tar.gz" -type f | sort -r | head -n 1)"
    if [[ -z "$ARCHIVE_PATH" ]]; then
        log_error "No snapshot tarballs found in $BACKUP_DIR"
        exit 1
    fi
else
    if [[ -f "$TARGET_SNAPSHOT" ]]; then
        ARCHIVE_PATH="$TARGET_SNAPSHOT"
    elif [[ -f "${BACKUP_DIR}/${TARGET_SNAPSHOT}" ]]; then
        ARCHIVE_PATH="${BACKUP_DIR}/${TARGET_SNAPSHOT}"
    else
        log_error "Specified snapshot not found: $TARGET_SNAPSHOT"
        exit 1
    fi
fi

log_info "Restoring snapshot: $(basename "$ARCHIVE_PATH")..."

# Extract files back to config directory preserving structure
mkdir -p "$CONFIG_DIR"
tar -xzvf "$ARCHIVE_PATH" -C "$CONFIG_DIR" --strip-components=1 config/ 2>/dev/null || \
tar -xzvf "$ARCHIVE_PATH" -C "$CONFIG_DIR" --strip-components=1

log_info "Reloading desktop services..."

# Reconfigure KWin (strictly Plasma 6 qdbus6)
if command -v qdbus6 &>/dev/null; then
    qdbus6 org.kde.KWin /KWin reconfigure || true
fi

# Gracefully terminate Plasmashell
if command -v kquitapp6 &>/dev/null; then
    kquitapp6 plasmashell || true
    sleep 1
else
    killall -15 plasmashell 2>/dev/null || true
    sleep 1
fi

# Force kill only if still running
if pgrep -x plasmashell &>/dev/null; then
    killall -9 plasmashell 2>/dev/null || true
    sleep 0.5
fi

# Relaunch plasmashell
if command -v kstart6 &>/dev/null; then
    kstart6 plasmashell &>/dev/null &
elif command -v plasmashell &>/dev/null; then
    (setsid plasmashell &>/dev/null &)
fi

log_success "Desktop configuration restored successfully from $(basename "$ARCHIVE_PATH")!"

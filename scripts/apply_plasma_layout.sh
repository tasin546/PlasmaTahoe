#!/usr/bin/env bash
# ==============================================================================
# PlasmaTahoe-Engine: Apply Plasma 6 Panel & Dock Layout
# Evaluates JavaScript through PlasmaShell D-Bus interface
# ==============================================================================

set -Eeuo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
PROJECT_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd -P)"
readonly SCRIPT_DIR PROJECT_ROOT

log_info()    { printf "\033[36m[INFO]\033[0m %s\n" "$*"; }
log_success() { printf "\033[32m[SUCCESS]\033[0m %s\n" "$*"; }
log_error()   { printf "\033[31m[ERROR]\033[0m %s\n" "$*" >&2; }

trap 'log_error "Layout application failed at line $LINENO: exit code $?"' ERR

JS_TEMPLATE="${PROJECT_ROOT}/core/plasma_layout.js"

if [[ ! -f "$JS_TEMPLATE" ]]; then
    log_error "Layout template not found at: $JS_TEMPLATE"
    exit 1
fi

TOP_HEIGHT="${1:-28}"
DOCK_HEIGHT="${2:-56}"

# Generate runtime JS
TEMP_JS="$(mktemp --suffix=.js)"
trap 'rm -f "$TEMP_JS"' EXIT

sed -e "s/__TOP_PANEL_HEIGHT__/$TOP_HEIGHT/g" \
    -e "s/__DOCK_HEIGHT__/$DOCK_HEIGHT/g" \
    "$JS_TEMPLATE" > "$TEMP_JS"

# Locate QDBus CLI (Plasma 6 strictly uses qdbus6)
QDBUS_BIN=""
if command -v qdbus6 &>/dev/null; then
    QDBUS_BIN="qdbus6"
fi

if [[ -z "$QDBUS_BIN" ]]; then
    log_error "qdbus6 not found. Ensure KDE Plasma 6 desktop is active."
    exit 1
fi

log_info "Evaluating layout script in PlasmaShell (Top: ${TOP_HEIGHT}px, Dock: ${DOCK_HEIGHT}px)..."
SCRIPT_CONTENT="$(cat "$TEMP_JS")"

"$QDBUS_BIN" org.kde.plasmashell /PlasmaShell org.kde.PlasmaShell.evaluateScript "$SCRIPT_CONTENT"

log_success "Plasma 6 Top Panel and Floating Dock applied successfully!"

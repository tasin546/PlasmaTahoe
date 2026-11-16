#!/usr/bin/env bash
# ==============================================================================
# PlasmaTahoe-Engine: Automated Distro Dependency Installer
# Detects host distribution and installs required build and runtime dependencies.
# ==============================================================================

set -Eeuo pipefail
IFS=$'\n\t'

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
readonly SCRIPT_DIR

log_info()    { printf "\033[36m[INFO]\033[0m %s\n" "$*"; }
log_success() { printf "\033[32m[SUCCESS]\033[0m %s\n" "$*"; }
log_warn()    { printf "\033[33m[WARN]\033[0m %s\n" "$*"; }
log_error()   { printf "\033[31m[ERROR]\033[0m %s\n" "$*" >&2; }

trap 'log_error "Command failed at line $LINENO: exit code $?"' ERR

detect_auth() {
    if [[ $EUID -eq 0 ]]; then
        echo ""
    elif command -v pkexec &>/dev/null; then
        echo "pkexec"
    elif command -v sudo &>/dev/null; then
        echo "sudo"
    else
        log_error "Neither pkexec nor sudo found. Please run as root."
        exit 1
    fi
}

AUTH_CMD="$(detect_auth)"
readonly AUTH_CMD

run_as_root() {
    if [[ -n "$AUTH_CMD" ]]; then
        $AUTH_CMD "$@"
    else
        "$@"
    fi
}

if [[ ! -f /etc/os-release ]]; then
    log_error "/etc/os-release not found. Cannot determine distribution."
    exit 1
fi

# Source os-release
# shellcheck disable=SC1091
source /etc/os-release

DISTRO_ID="${ID:-unknown}"
ID_LIKE_VAL="${ID_LIKE:-}"

log_info "Detected Distribution: ${PRETTY_NAME:-$DISTRO_ID}"

case "$DISTRO_ID" in
    arch|cachyos|endeavouros|manjaro|garuda)
        log_info "Installing dependencies via pacman..."
        run_as_root pacman -S --needed --noconfirm \
            git cmake extra-cmake-modules ninja gcc pkgconf \
            qt6-base qt6-declarative qt6-svg kvantum sassc \
            gtk-engine-murrine kwin libplasma wayland-protocols \
            python-pyqt6 jq gettext
        ;;

    fedora|nobara|rhel|centos)
        log_info "Installing dependencies via dnf..."
        run_as_root dnf install -y \
            git cmake extra-cmake-modules ninja-build gcc-c++ \
            qt6-qtbase-devel qt6-qtdeclarative-devel qt6-qtsvg-devel \
            kvantum sassc gtk-murrine-engine kwin-devel libplasma-devel \
            python3-pyqt6 jq gettext
        ;;

    debian|ubuntu|neon|kubuntu|pop|linuxmint)
        log_info "Updating package lists via apt-get..."
        run_as_root apt-get update -y
        log_info "Installing dependencies via apt-get..."
        run_as_root apt-get install -y --no-install-recommends \
            git cmake extra-cmake-modules ninja-build g++ \
            qt6-base-dev qt6-declarative-dev qt6-svg-dev \
            qt6-style-kvantum sassc gtk2-engines-murrine \
            kwin-dev libplasma-dev python3-pyqt6 jq gettext
        ;;

    opensuse-tumbleweed|opensuse-leap|suse)
        log_info "Installing dependencies via zypper..."
        run_as_root zypper --non-interactive install \
            git cmake extra-cmake-modules ninja gcc-c++ \
            qt6-base-devel qt6-declarative-devel qt6-svg-devel \
            kvantum-manager sassc gtk2-engine-murrine \
            kwin6-devel libplasma6-devel python3-qt6 jq gettext-tools
        ;;

    *)
        # Check id_like fallback
        if [[ "$ID_LIKE_VAL" =~ arch ]]; then
            log_info "Arch-like distro detected. Installing via pacman..."
            run_as_root pacman -S --needed --noconfirm git cmake extra-cmake-modules ninja gcc pkgconf qt6-base qt6-declarative qt6-svg kvantum sassc gtk-engine-murrine kwin libplasma python-pyqt6 jq gettext
        elif [[ "$ID_LIKE_VAL" =~ (debian|ubuntu) ]]; then
            log_info "Debian-like distro detected. Installing via apt-get..."
            run_as_root apt-get update -y
            run_as_root apt-get install -y --no-install-recommends git cmake extra-cmake-modules ninja-build g++ qt6-base-dev qt6-declarative-dev qt6-svg-dev qt6-style-kvantum sassc gtk2-engines-murrine kwin-dev libplasma-dev python3-pyqt6 jq gettext
        elif [[ "$ID_LIKE_VAL" =~ fedora ]]; then
            log_info "Fedora-like distro detected. Installing via dnf..."
            run_as_root dnf install -y git cmake extra-cmake-modules ninja-build gcc-c++ qt6-qtbase-devel qt6-qtdeclarative-devel qt6-qtsvg-devel kvantum sassc gtk-murrine-engine kwin-devel libplasma-devel python3-pyqt6 jq gettext
        else
            log_warn "Unrecognized Linux distribution: $DISTRO_ID. Please install dependencies manually."
            exit 1
        fi
        ;;
esac

log_success "All build and runtime dependencies successfully installed!"

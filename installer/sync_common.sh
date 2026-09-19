#!/bin/bash
# sync_common.sh — mirror the live source tree into installer/common/.
#
# installer/common/ is copied verbatim onto the device, so it IS the shipped
# code for SD-card installs. See "Keeping common/ current" in README.md.
#
#   ./installer/sync_common.sh           # sync, then report
#   ./installer/sync_common.sh --check   # report only, non-zero if stale

set -eu

REPO_DIR="$(cd "$(dirname "$0")/.." && pwd)"
COMMON_DIR="$REPO_DIR/installer/common"

# The modules that ship to a device. Driven by the repo root, NOT by whatever
# is already in common/ — a mirror-driven loop can only refresh files it
# already has, so a newly written module would silently never ship and
# --check would still pass green.
#
# code.py is excluded deliberately: install_code.py synthesises its own entry
# point on the device rather than copying this one.
SHIP_FILES=(
    machine.py
    hardware_config.py
    display_manager.py
    audio_player.py
    input_manager.py
    sleep_manager.py
    menu_parser.py
    action.py
    storage_manager.py
    config_reader.py
    es8311.py
)

CHECK_ONLY=false
for arg in "$@"; do
    case "$arg" in
        --check) CHECK_ONLY=true ;;
        *)
            echo "sync_common.sh: unknown argument '$arg'" >&2
            echo "usage: sync_common.sh [--check]" >&2
            exit 2
            ;;
    esac
done

stale=0

for name in "${SHIP_FILES[@]}"; do
    live="$REPO_DIR/$name"
    mirror="$COMMON_DIR/$name"

    if [ ! -f "$live" ]; then
        echo "ERROR $name — listed in SHIP_FILES but missing from the repo root" >&2
        exit 1
    fi

    if [ -f "$mirror" ] && cmp -s "$live" "$mirror"; then
        continue
    fi

    stale=$((stale + 1))
    if [ ! -f "$mirror" ]; then
        $CHECK_ONLY && echo "MISSING $name — not shipped at all" || {
            cp "$live" "$mirror"; echo "add   $name"; }
    else
        $CHECK_ONLY && echo "STALE   $name" || { cp "$live" "$mirror"; echo "sync  $name"; }
    fi
done

# Anything in common/ that SHIP_FILES no longer lists is a leftover that will
# still be copied onto devices.
for mirror in "$COMMON_DIR"/*.py; do
    name="${mirror##*/}"
    listed=false
    for want in "${SHIP_FILES[@]}"; do
        [ "$name" = "$want" ] && listed=true && break
    done
    $listed || echo "ORPHAN $name — in common/ but not in SHIP_FILES"
done

echo
if $CHECK_ONLY; then
    if [ "$stale" -gt 0 ]; then
        echo "installer/common is STALE ($stale file(s)) — run ./installer/sync_common.sh"
        exit 1
    fi
    echo "installer/common is up to date."
else
    echo "Synced $stale file(s); installer/common now matches the repo root."
fi

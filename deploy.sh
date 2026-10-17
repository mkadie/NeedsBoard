#!/bin/bash
# deploy.sh — Deploy AAC production code to connected devices.
#
# Finds all CIRCUITPY drives and deploys the production code.
#
# Each device keeps its own config.txt (never overwritten once it exists).
# hardware_config.py IS overwritten, so its DEFAULT_VARIANT is NOT per-device
# — a device that isn't the default must pin itself with `variant = NAME` in
# its own config.txt, otherwise this script will retarget it on every deploy.
#
# Usage:
#   ./deploy.sh              # Deploy to all connected devices
#   ./deploy.sh CIRCUITPY1           # only that drive
#   ./deploy.sh FRUITJAM_CLONE_18    # only boards declaring that variant
#   ./deploy.sh --code-only  # Deploy only Python files (skip menus/sounds)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Production Python files to deploy
PY_FILES=(
    code.py
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
)

CODE_ONLY=false
TARGET=""
for arg in "$@"; do
    case "$arg" in
        --code-only) CODE_ONLY=true ;;
        fruitjam|badge) TARGET="$arg" ;;
    esac
done

deploy_to() {
    local mount="$1"
    local name="$2"

    if [ ! -d "$mount" ]; then
        echo "  SKIP: $mount not found"
        return
    fi

    # An unmounted board leaves its mount point behind as an empty root-owned
    # directory, which looks like a device but fails the first copy. With
    # set -e that aborted the whole run before the real board was reached.
    if [ ! -w "$mount" ]; then
        echo "  SKIP: $mount is not writable (stale mount point?)"
        return
    fi

    echo "Deploying to $name ($mount)..."

    # Python files
    for f in "${PY_FILES[@]}"; do
        if [ -f "$SCRIPT_DIR/$f" ]; then
            cp "$SCRIPT_DIR/$f" "$mount/$f"
        fi
    done
    echo "  Python files deployed"

    # Config — only deploy if device doesn't have one yet
    if [ ! -f "$mount/config.txt" ]; then
        cp "$SCRIPT_DIR/config.txt" "$mount/config.txt"
        echo "  config.txt created (new)"
    else
        echo "  config.txt preserved (existing)"
    fi

    if [ "$CODE_ONLY" = false ]; then
        # Menus, menu images and per-menu sounds, in one copy. images/ and
        # sounds/ used to be skipped here, which is why every Food/Drink
        # submenu item was silent: the menu resolves `sound = sounds/food/
        # x.mp3` to /menus/sounds/food/x.mp3, and that tree never reached
        # the device at all.
        mkdir -p "$mount/menus"
        cp -r "$SCRIPT_DIR/menus/." "$mount/menus/"
        echo "  Menus, images and sounds deployed"

        # Button sounds
        mkdir -p "$mount/button_sounds"
        for f in "$SCRIPT_DIR"/button_sounds/*.mp3; do
            [ -f "$f" ] && cp "$f" "$mount/button_sounds/"
        done
        echo "  Button sounds deployed"

        # Copying never removes, so a renamed asset leaves its old name on
        # the device forever -- that is how retired board art kept shipping.
        # Report rather than delete: the device legitimately carries content
        # the repo does not have (button_sounds/languages/, for one), so
        # deciding what is stale is a human's call.
        orphans=""
        for sub in menus button_sounds; do
            [ -d "$mount/$sub" ] || continue
            while IFS= read -r dev; do
                rel="${dev#$mount/}"
                [ -e "$SCRIPT_DIR/$rel" ] || orphans="$orphans  $rel"$'\n'
            done < <(find "$mount/$sub" -type f ! -name '.*' 2>/dev/null)
        done
        if [ -n "$orphans" ]; then
            echo "  NOTE: on the device but not in the repo (stale?):"
            printf '%s' "$orphans"
        fi
    fi

    sync
    echo "  Done."
    echo ""
}

echo "=============================================="
echo "AAC Device — Deploy Production Code"
echo "=============================================="
echo ""

if [ "$CODE_ONLY" = false ]; then
    if ! python3 "$SCRIPT_DIR/check_menus.py"; then
        echo ""
        echo "ABORT: a menu references assets that do not exist."
        echo "On the device this fails silently -- the cell just does nothing."
        exit 1
    fi
    echo ""
fi

# Every mounted CIRCUITPY drive, named by what the board says it is.
#
# The old fixed table (CIRCUITPY = "Fruit Jam", CIRCUITPY1 = "OLED Badge")
# could not see a third board at all, and udisks hands out the numeric
# suffix by mount order -- so the labels move between sessions and the names
# were regularly wrong about which board was which. A device already
# declares its identity in its own config.txt; read that instead.
found=0
for mount in "/media/$USER"/CIRCUITPY*; do
    [ -d "$mount" ] || continue

    label="$(basename "$mount")"
    variant="$(sed -n 's/^[[:space:]]*variant[[:space:]]*=[[:space:]]*//p' \
                   "$mount/config.txt" 2>/dev/null | head -1)"
    uid="$(sed -n 's/^UID:*//p' "$mount/boot_out.txt" 2>/dev/null | head -1)"
    name="${variant:-unconfigured}"
    [ -n "$uid" ] && name="$name  [UID $uid]"

    # A target argument matches the drive label or the declared variant, so
    # "./deploy.sh FRUITJAM_CLONE_18" picks a board regardless of where it
    # happens to have mounted this time.
    if [ -n "$TARGET" ]; then
        case "$TARGET" in
            "$label"|"$variant") ;;
            *) continue ;;
        esac
    fi

    found=$((found + 1))
    deploy_to "$mount" "$name"
done

if [ "$found" -eq 0 ]; then
    if [ -n "$TARGET" ]; then
        echo "No CIRCUITPY drive matching '$TARGET'."
    else
        echo "No CIRCUITPY drive found under /media/$USER/."
    fi
fi

echo "Deploy complete."
echo "Devices will auto-reload."

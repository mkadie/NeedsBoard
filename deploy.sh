#!/bin/bash
# deploy.sh — Deploy AAC production code to connected devices.
#
# Finds all CIRCUITPY drives and deploys the production code.
# Each device keeps its own config.txt and hardware_config.py
# DEFAULT_VARIANT setting.
#
# Usage:
#   ./deploy.sh              # Deploy to all connected devices
#   ./deploy.sh fruitjam     # Deploy only to Fruit Jam (CIRCUITPY)
#   ./deploy.sh badge        # Deploy only to Badge (CIRCUITPY1)
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
        # Menus
        mkdir -p "$mount/menus"
        cp "$SCRIPT_DIR"/menus/*.menu "$mount/menus/" 2>/dev/null || true
        echo "  Menu files deployed"

        # Menu images (if they exist on device)
        if [ -d "$mount/menus/images" ]; then
            echo "  Menu images preserved (existing)"
        fi

        # Button sounds
        mkdir -p "$mount/button_sounds"
        for f in "$SCRIPT_DIR"/button_sounds/*.mp3; do
            [ -f "$f" ] && cp "$f" "$mount/button_sounds/"
        done
        echo "  Button sounds deployed"
    fi

    sync
    echo "  Done."
    echo ""
}

echo "=============================================="
echo "AAC Device — Deploy Production Code"
echo "=============================================="
echo ""

if [ -z "$TARGET" ] || [ "$TARGET" = "fruitjam" ]; then
    deploy_to "/media/$USER/CIRCUITPY" "Fruit Jam"
fi

if [ -z "$TARGET" ] || [ "$TARGET" = "badge" ]; then
    deploy_to "/media/$USER/CIRCUITPY1" "OLED Badge"
fi

echo "Deploy complete."
echo "Devices will auto-reload."

#!/bin/bash
# deploy.sh — Deploy ES8311 driver and examples to the ES3C28P board.
#
# Usage:
#   ./deploy.sh                  # Deploy driver + last-used example (play_tone)
#   ./deploy.sh tone             # Deploy driver + play_tone example
#   ./deploy.sh mic              # Deploy driver + mic_level example
#   ./deploy.sh both             # Deploy driver + play_and_record example
#   ./deploy.sh test             # Deploy driver + hardware test suite
#   ./deploy.sh lib              # Deploy only the driver to lib/
#
# The script finds the CIRCUITPY drive automatically.
# After deploying, the board auto-reloads and runs code.py.

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOCAL_DIR="$SCRIPT_DIR/es8311_local"
DRIVER="$LOCAL_DIR/es8311.py"

# Find CIRCUITPY mount
CIRCUITPY=""
for path in /media/*/CIRCUITPY; do
    if [ -d "$path" ]; then
        CIRCUITPY="$path"
        break
    fi
done

if [ -z "$CIRCUITPY" ]; then
    echo "ERROR: CIRCUITPY drive not found. Is the board plugged in?"
    exit 1
fi

echo "Found CIRCUITPY at: $CIRCUITPY"

# Always deploy the driver to lib/
mkdir -p "$CIRCUITPY/lib"
cp "$DRIVER" "$CIRCUITPY/lib/es8311.py"
echo "  Deployed es8311.py -> lib/"

# Also put a copy at root for imports that don't use lib/
cp "$DRIVER" "$CIRCUITPY/es8311.py"

# Determine which example to deploy as code.py
EXAMPLE="${1:-tone}"

case "$EXAMPLE" in
    tone)
        cp "$LOCAL_DIR/examples/play_tone.py" "$CIRCUITPY/code.py"
        echo "  Deployed play_tone.py -> code.py"
        ;;
    mic)
        cp "$LOCAL_DIR/examples/mic_level.py" "$CIRCUITPY/code.py"
        echo "  Deployed mic_level.py -> code.py"
        ;;
    both)
        cp "$LOCAL_DIR/examples/play_and_record.py" "$CIRCUITPY/code.py"
        echo "  Deployed play_and_record.py -> code.py"
        ;;
    test)
        cp "$LOCAL_DIR/tests/test_hardware.py" "$CIRCUITPY/code.py"
        echo "  Deployed test_hardware.py -> code.py"
        ;;
    lib)
        echo "  Driver only — no code.py change."
        ;;
    *)
        echo "ERROR: Unknown example '$EXAMPLE'"
        echo "Usage: $0 {tone|mic|both|test|lib}"
        exit 1
        ;;
esac

echo "Done. Board will auto-reload."

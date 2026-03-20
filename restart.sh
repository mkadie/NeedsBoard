#!/bin/bash
# restart.sh — Recreate the ES8311 CircuitPython library from scratch.
#
# This script documents every step needed to reproduce the ES8311 driver
# and deploy it to the ES3C28P board. Run it if you need to rebuild
# everything from a clean state.
#
# Prerequisites:
#   - ES3C28P board connected via USB (shows up as CIRCUITPY)
#   - CircuitPython 10.x installed on the board
#   - neopixel.mpy in CIRCUITPY/lib/ (for mic_level example)
#   - Python 3 + pytest on the host (for PC tests)
#
# What this script does:
#   1. Verifies the board is connected
#   2. Runs the PC-based unit tests
#   3. Deploys the driver to the board
#   4. Runs the hardware test suite on the board
#   5. Deploys the tone example to verify audio output
#
# Usage:
#   ./restart.sh           # Full rebuild + test
#   ./restart.sh --quick   # Just deploy, skip tests

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
BUNDLE_DIR="$SCRIPT_DIR/circuitpython_es8311"
LOCAL_DIR="$SCRIPT_DIR/es8311_local"
DEPLOY="$SCRIPT_DIR/deploy.sh"

QUICK=false
if [ "$1" = "--quick" ]; then
    QUICK=true
fi

echo "=============================================="
echo "ES8311 CircuitPython Library — Restart Script"
echo "=============================================="
echo ""

# ── Step 1: Verify board connection ──
echo "Step 1: Checking for CIRCUITPY drive..."
CIRCUITPY=""
for path in /media/*/CIRCUITPY; do
    if [ -d "$path" ]; then
        CIRCUITPY="$path"
        break
    fi
done

if [ -z "$CIRCUITPY" ]; then
    echo "  WARNING: CIRCUITPY not found. Board tests will be skipped."
    echo "  Plug in the ES3C28P and re-run to test on hardware."
    BOARD_CONNECTED=false
else
    echo "  Found: $CIRCUITPY"
    cat "$CIRCUITPY/boot_out.txt" 2>/dev/null | head -1
    BOARD_CONNECTED=true
fi
echo ""

# ── Step 2: Verify files exist ──
echo "Step 2: Verifying project files..."
MISSING=false
for f in \
    "$BUNDLE_DIR/es8311.py" \
    "$BUNDLE_DIR/README.md" \
    "$BUNDLE_DIR/LICENSE" \
    "$BUNDLE_DIR/setup.py" \
    "$BUNDLE_DIR/tests/test_registers.py" \
    "$BUNDLE_DIR/tests/test_hardware.py" \
    "$BUNDLE_DIR/examples/es8311_tone.py" \
    "$BUNDLE_DIR/examples/es8311_mic_level.py" \
    "$BUNDLE_DIR/examples/es8311_play_and_record.py" \
    "$LOCAL_DIR/es8311.py" \
    "$LOCAL_DIR/README.md" \
    "$LOCAL_DIR/tests/test_hardware.py" \
    "$LOCAL_DIR/examples/play_tone.py" \
    "$LOCAL_DIR/examples/mic_level.py" \
    "$LOCAL_DIR/examples/play_and_record.py"; do
    if [ ! -f "$f" ]; then
        echo "  MISSING: $f"
        MISSING=true
    fi
done

if [ "$MISSING" = true ]; then
    echo "  ERROR: Some files are missing. Cannot continue."
    exit 1
fi
echo "  All files present."
echo ""

# ── Step 3: Run PC unit tests ──
if [ "$QUICK" = false ]; then
    echo "Step 3: Running PC unit tests..."
    cd "$BUNDLE_DIR"
    if command -v python3 &>/dev/null && python3 -m pytest --version &>/dev/null 2>&1; then
        python3 -m pytest tests/test_registers.py -v 2>&1 | tail -5
    else
        echo "  SKIPPED: pytest not installed (pip install pytest)"
    fi
    echo ""
else
    echo "Step 3: SKIPPED (--quick mode)"
    echo ""
fi

# ── Step 4: Deploy driver to board ──
if [ "$BOARD_CONNECTED" = true ]; then
    echo "Step 4: Deploying driver to board..."
    bash "$DEPLOY" lib
    echo ""

    # ── Step 5: Run hardware tests ──
    if [ "$QUICK" = false ]; then
        echo "Step 5: Running hardware tests on board..."
        bash "$DEPLOY" test
        echo "  Waiting for board to run tests (15s)..."

        # Give the board time to auto-reload and run
        sleep 3

        # Read serial output
        if command -v python3 &>/dev/null; then
            python3 -c "
import serial, time
try:
    ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
    ser.write(b'\x03'); time.sleep(0.5)
    ser.write(b'\x04'); time.sleep(1)
    end = time.time() + 30
    while time.time() < end:
        data = ser.read(ser.in_waiting or 1)
        if data:
            text = data.decode('utf-8', errors='replace')
            print(text, end='')
            if 'Results:' in text:
                time.sleep(1)
                # Read any remaining output
                data = ser.read(ser.in_waiting or 1)
                if data:
                    print(data.decode('utf-8', errors='replace'), end='')
                break
    ser.close()
except Exception as e:
    print('  Could not read serial: {}'.format(e))
" 2>&1 | grep -E '(PASS|FAIL|Results|==)' || echo "  (Could not capture serial output)"
        fi
        echo ""
    else
        echo "Step 5: SKIPPED (--quick mode)"
        echo ""
    fi

    # ── Step 6: Deploy tone example ──
    echo "Step 6: Deploying tone example..."
    bash "$DEPLOY" tone
    echo ""
else
    echo "Steps 4-6: SKIPPED (board not connected)"
    echo ""
fi

# ── Summary ──
echo "=============================================="
echo "Restart complete."
echo ""
echo "Project structure:"
echo "  circuitpython_es8311/   Community bundle (generic, publishable)"
echo "  es8311_local/           Board-local (ES3C28P defaults)"
echo ""
echo "Deploy commands:"
echo "  ./deploy.sh tone    Play 440Hz tone"
echo "  ./deploy.sh mic     Mic level on NeoPixel"
echo "  ./deploy.sh both    Tone + mic monitoring"
echo "  ./deploy.sh test    Run hardware tests"
echo ""
echo "Key pin assignments (ES3C28P):"
echo "  I2C: SCL=GPIO15, SDA=GPIO16"
echo "  I2S: MCLK=GPIO4, BCLK=GPIO5, WS=GPIO7"
echo "  I2S DOUT=GPIO8 (DAC), DIN=GPIO6 (ADC/mic)"
echo "  Amp enable: GPIO1 (LOW=on)"
echo "  NeoPixel: GPIO42"
echo "=============================================="

#!/bin/bash
# restart.sh — Rebuild and verify the AAC production system.
#
# This script documents every step needed to deploy and verify
# the AAC device from a clean state. Run it after major changes
# or when setting up a new device.
#
# Prerequisites:
#   - Device connected via USB (shows up as CIRCUITPY or CIRCUITPY1)
#   - CircuitPython installed on the device
#   - Python 3 + pyserial on the host
#
# What this script does:
#   1. Verifies device connections
#   2. Deploys production code
#   3. Reboots each device and captures boot output
#   4. Verifies successful boot
#
# Usage:
#   ./restart.sh              # Full deploy + verify
#   ./restart.sh --quick      # Deploy code only, skip verify
#   ./restart.sh --verify     # Just verify (no deploy)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

QUICK=false
VERIFY_ONLY=false
for arg in "$@"; do
    case "$arg" in
        --quick) QUICK=true ;;
        --verify) VERIFY_ONLY=true ;;
    esac
done

echo "=============================================="
echo "AAC Device — Restart & Verify"
echo "=============================================="
echo ""

# ── Step 1: Find devices ──
echo "Step 1: Checking for connected devices..."

DEVICES=()
for port in /dev/ttyACM*; do
    [ -e "$port" ] || continue
    model=$(udevadm info -q property "$port" 2>/dev/null | grep "ID_MODEL=" | head -1 | cut -d= -f2)
    echo "  $port: $model"
    DEVICES+=("$port:$model")
done

if [ ${#DEVICES[@]} -eq 0 ]; then
    echo "  No devices found."
    exit 1
fi

FRUITJAM_PORT=""
BADGE_PORT=""
for dev in "${DEVICES[@]}"; do
    port="${dev%%:*}"
    model="${dev#*:}"
    case "$model" in
        *Fruit_Jam*) FRUITJAM_PORT="$port" ;;
        *Pico*) BADGE_PORT="$port" ;;
    esac
done

echo ""

# ── Step 2: Deploy ──
if [ "$VERIFY_ONLY" = false ]; then
    echo "Step 2: Deploying production code..."
    if [ "$QUICK" = true ]; then
        bash "$SCRIPT_DIR/deploy.sh" --code-only
    else
        bash "$SCRIPT_DIR/deploy.sh"
    fi
else
    echo "Step 2: SKIPPED (--verify mode)"
    echo ""
fi

# ── Step 3: Verify boot ──
if [ "$QUICK" = false ]; then
    echo "Step 3: Verifying device boot..."

    verify_device() {
        local port="$1"
        local name="$2"

        if [ -z "$port" ]; then
            echo "  $name: not connected, skipping"
            return
        fi

        echo "  $name ($port): rebooting..."
        python3 -c "
import serial, time
ser = serial.Serial('$port', 115200, timeout=1)
ser.write(b'\x03'); time.sleep(0.3)
ser.write(b'\x04')
start = time.monotonic()
lines = []
while time.monotonic() - start < 15:
    data = ser.read(1024)
    if data:
        for line in data.decode('utf-8', errors='replace').splitlines():
            line = line.strip()
            if line and 'AAC Device ready' in line:
                lines.append(line)
            elif 'Traceback' in line or 'Error' in line:
                lines.append('ERROR: ' + line)
    if any('ready' in l.lower() for l in lines):
        break
    if any('ERROR' in l for l in lines):
        break
ser.close()
for l in lines:
    print('    ' + l)
if not lines:
    print('    WARNING: No output captured')
" 2>&1 || echo "    Could not connect to serial"
        echo ""
    }

    verify_device "$FRUITJAM_PORT" "Fruit Jam"
    verify_device "$BADGE_PORT" "OLED Badge"
else
    echo "Step 3: SKIPPED (--quick mode)"
    echo ""
fi

# ── Summary ──
echo "=============================================="
echo "Restart complete."
echo ""
echo "Supported devices:"
echo "  FRUITJAM_V2          — Color LCD, TLV320 DAC, encoder"
echo "  RP2350_OLED_BADGE_V3 — OLED 128x32, direct I2S, encoder"
echo "  CYD_PLUS             — Touch screen, ES8311 codec"
echo "  RP2350_V2            — LCD, buttons + encoder"
echo ""
echo "Deploy commands:"
echo "  ./deploy.sh              Deploy to all devices"
echo "  ./deploy.sh fruitjam     Deploy to Fruit Jam only"
echo "  ./deploy.sh badge        Deploy to Badge only"
echo "  ./deploy.sh --code-only  Python files only (keep config)"
echo ""
echo "Configuration:"
echo "  config.txt  — User settings (per device)"
echo "  NOTES.md    — Development notes and future ideas"
echo "=============================================="

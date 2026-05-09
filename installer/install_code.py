"""AAC Device Auto-Installer

Drop this file as code.py on a freshly flashed CircuitPython device.
It reads boot_out.txt to identify the board, copies the right files
from the SD card, and configures the device automatically.

SD Card Layout:
    /sd/installer/
        common/           <- Python source files (all devices)
        configs/          <- Per-variant config.txt files
        content/          <- Menus, images, sounds (all devices)

Usage:
    1. Flash CircuitPython onto the device
    2. Copy this file as code.py to CIRCUITPY
    3. Insert SD card with installer/ directory
    4. Reboot — installer runs automatically
    5. Remove SD card and reboot to run the AAC software
"""

import os
import time

# Board ID to variant mapping
BOARD_MAP = {
    "yd_esp32_s3_n16r8": "CYD_PLUS",
    "adafruit_fruit_jam": "FRUITJAM_V2",
    "raspberry_pi_pico2": "RP2350_OLED_BADGE_V3",
    "adafruit_feather_rp2350": "FEATHER_RP2350_V1",
}

def read_board_id():
    """Read Board ID from boot_out.txt."""
    try:
        with open("/boot_out.txt", "r") as f:
            for line in f:
                if line.startswith("Board ID:"):
                    return line.split(":", 1)[1].strip()
    except:
        pass
    return None


def copy_file(src, dst):
    """Copy a single file, creating parent directories as needed."""
    # Create parent directory
    parts = dst.rsplit("/", 1)
    if len(parts) == 2 and parts[0]:
        _makedirs(parts[0])

    try:
        with open(src, "rb") as sf:
            with open(dst, "wb") as df:
                while True:
                    chunk = sf.read(4096)
                    if not chunk:
                        break
                    df.write(chunk)
        return True
    except Exception as e:
        print("  FAIL: {} -> {}: {}".format(src, dst, e))
        return False


def _makedirs(path):
    """Recursive mkdir."""
    parts = path.split("/")
    current = ""
    for part in parts:
        if not part:
            current = "/"
            continue
        current = current + "/" + part if current else part
        if current == "/":
            continue
        try:
            os.mkdir(current)
        except OSError:
            pass  # Already exists


def copy_tree(src_dir, dst_dir):
    """Recursively copy all files from src_dir to dst_dir."""
    count = 0
    try:
        entries = os.listdir(src_dir)
    except OSError:
        print("  Directory not found:", src_dir)
        return 0

    for entry in entries:
        src_path = src_dir + "/" + entry
        dst_path = dst_dir + "/" + entry
        stat = os.stat(src_path)
        if stat[0] & 0x4000:  # Is directory
            count += copy_tree(src_path, dst_path)
        else:
            if copy_file(src_path, dst_path):
                count += 1
                print("  {} -> {}".format(entry, dst_path))
    return count


def install():
    """Main installer logic."""
    print()
    print("=" * 40)
    print("  AAC Device Auto-Installer")
    print("=" * 40)
    print()

    # Identify board
    board_id = read_board_id()
    if not board_id:
        print("ERROR: Cannot read Board ID from boot_out.txt")
        return False
    print("Board ID:", board_id)

    variant = BOARD_MAP.get(board_id)
    if not variant:
        print("ERROR: Unknown board '{}'\n".format(board_id))
        print("Known boards:")
        for bid, var in BOARD_MAP.items():
            print("  {} -> {}".format(bid, var))
        return False
    print("Variant:", variant)
    print()

    # Mount SD card
    sd_base = None
    for path in ["/sd/installer", "/installer"]:
        try:
            os.listdir(path)
            sd_base = path
            break
        except OSError:
            pass

    if not sd_base:
        # Try to mount SD card
        try:
            import board
            import busio
            import sdcardio
            import storage

            # Try common SD card pins
            spi = board.SPI()
            for cs_name in ["SD_CS", "RX", "GP21", "D10"]:
                try:
                    cs = getattr(board, cs_name)
                    sdcard = sdcardio.SDCard(spi, cs)
                    vfs = storage.VfsFat(sdcard)
                    storage.mount(vfs, "/sd")
                    sd_base = "/sd/installer"
                    os.listdir(sd_base)
                    print("SD card mounted, installer found at", sd_base)
                    break
                except:
                    continue
        except:
            pass

    if not sd_base:
        print("ERROR: installer/ directory not found")
        print("Expected on SD card at /sd/installer/")
        print("Or on flash at /installer/")
        return False

    print("Installer source:", sd_base)
    print()

    # Step 1: Copy common Python files
    print("--- Step 1: Python source files ---")
    n = copy_tree(sd_base + "/common", "/")
    print("Copied {} files\n".format(n))

    # Step 2: Set the variant in hardware_config.py
    print("--- Step 2: Setting variant to {} ---".format(variant))
    try:
        with open("/hardware_config.py", "r") as f:
            content = f.read()
        # Find and replace DEFAULT_VARIANT
        lines = content.split("\n")
        for i, line in enumerate(lines):
            if "DEFAULT_VARIANT" in line and "=" in line:
                lines[i] = 'DEFAULT_VARIANT = "{}"'.format(variant)
                break
        with open("/hardware_config.py", "w") as f:
            f.write("\n".join(lines))
        print("  Set DEFAULT_VARIANT =", variant)
    except Exception as e:
        print("  ERROR setting variant:", e)
    print()

    # Step 3: Copy config.txt for this variant
    print("--- Step 3: Device configuration ---")
    config_src = sd_base + "/configs/" + variant + ".txt"
    if copy_file(config_src, "/config.txt"):
        print("  Installed config.txt for", variant)
    else:
        print("  No config found for", variant, "— using defaults")
    print()

    # Step 4: Copy content (menus, images, sounds)
    print("--- Step 4: Content files ---")
    n = copy_tree(sd_base + "/content", "/")
    print("Copied {} content files\n".format(n))

    # Step 5: Create code.py (the real entry point)
    print("--- Step 5: Creating code.py ---")
    with open("/code.py", "w") as f:
        f.write('"""AAC Communication Device."""\n')
        f.write("from machine import Machine\n")
        f.write("app = Machine()\n")
        f.write("app.run()\n")
    print("  code.py written")
    print()

    # Step 6: Create settings.toml if missing
    try:
        os.stat("/settings.toml")
    except OSError:
        with open("/settings.toml", "w") as f:
            f.write("")
        print("  Created empty settings.toml")

    print()
    print("=" * 40)
    print("  Installation complete!")
    print("  Variant: {}".format(variant))
    print("  Remove SD card and reboot.")
    print("=" * 40)
    return True


# Run installer
success = install()
if not success:
    print("\nInstallation FAILED. Check errors above.")

# Blink to indicate done
try:
    import board
    import digitalio
    led = None
    for pin_name in ["LED", "GPIO42", "D13", "NEOPIXEL"]:
        try:
            led = digitalio.DigitalInOut(getattr(board, pin_name))
            led.direction = digitalio.Direction.OUTPUT
            break
        except:
            continue
    if led:
        for _ in range(10):
            led.value = not led.value
            time.sleep(0.3)
except:
    pass

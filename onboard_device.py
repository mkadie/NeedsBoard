#!/usr/bin/env python3
"""Onboarding script for new AAC device variants.

Reads the device variant from hardware_config.py, creates the appropriate
image directory (image_WxH/), and generates scaled images from master_images/.

Usage:
    python onboard_device.py                    # Onboard DEFAULT_VARIANT
    python onboard_device.py FRUITJAM_V2        # Onboard specific variant
    python onboard_device.py --all              # Onboard all variants
    python onboard_device.py --list             # List available variants
    python onboard_device.py --deploy FRUITJAM_V2 /media/CIRCUITPY  # Deploy to device
"""

import os
import sys
import shutil

# Add project dir to path so we can import hardware_config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from hardware_config import VARIANTS, DEFAULT_VARIANT
from image_tools import ImageScaler

MASTER_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "master_images")


def image_dir_name(width, height):
    """Return the image directory name for a resolution."""
    return "image_{}x{}".format(width, height)


def onboard_variant(variant_name):
    """Generate scaled images for a device variant.

    Creates image_WxH/ directory and scales all master_images into it.

    Args:
        variant_name: Key in VARIANTS dict.

    Returns:
        Path to the generated image directory.
    """
    if variant_name not in VARIANTS:
        print("ERROR: Unknown variant '{}'".format(variant_name))
        print("Available:", ", ".join(sorted(VARIANTS.keys())))
        return None

    config = VARIANTS[variant_name]
    width = config["screen_width"]
    height = config["screen_height"]
    dir_name = image_dir_name(width, height)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    dst_dir = os.path.join(base_dir, dir_name)

    print("=" * 50)
    print("Onboarding: {} ({}x{})".format(variant_name, width, height))
    print("  Source: {}".format(MASTER_DIR))
    print("  Target: {}".format(dst_dir))
    print("=" * 50)

    if not os.path.isdir(MASTER_DIR):
        print("ERROR: master_images/ directory not found")
        print("  Expected at:", MASTER_DIR)
        return None

    scaler = ImageScaler(width, height)
    converted, skipped, errors = scaler.convert_tree(MASTER_DIR, dst_dir)

    print("\n  Result: {} converted, {} skipped, {} errors".format(
        converted, skipped, errors))
    print("  Output: {}\n".format(dst_dir))
    return dst_dir


def deploy_to_device(variant_name, mount_point):
    """Deploy menus, images, and sounds to a mounted CIRCUITPY device.

    Copies:
      - menus/*.menu files
      - Scaled images from image_WxH/ to menus/images/ on device
      - Sound files from menus/sounds/ to device
      - Button sounds from button_sounds/ if present

    Args:
        variant_name: Key in VARIANTS dict.
        mount_point: Path to mounted CIRCUITPY drive.
    """
    if variant_name not in VARIANTS:
        print("ERROR: Unknown variant '{}'".format(variant_name))
        return False

    config = VARIANTS[variant_name]
    width = config["screen_width"]
    height = config["screen_height"]
    dir_name = image_dir_name(width, height)
    base_dir = os.path.dirname(os.path.abspath(__file__))
    img_dir = os.path.join(base_dir, dir_name)

    if not os.path.isdir(mount_point):
        print("ERROR: Mount point not found:", mount_point)
        return False

    if not os.path.isdir(img_dir):
        print("Image directory {} not found, running onboard first...".format(dir_name))
        onboard_variant(variant_name)

    print("=" * 50)
    print("Deploying {} to {}".format(variant_name, mount_point))
    print("=" * 50)

    menus_src = os.path.join(base_dir, "menus")
    menus_dst = os.path.join(mount_point, "menus")

    # Create target directories
    for d in ["menus", "menus/images", "menus/sounds", "button_sounds"]:
        os.makedirs(os.path.join(mount_point, d), exist_ok=True)

    # Copy menu files
    count = 0
    for f in os.listdir(menus_src):
        if f.endswith(".menu"):
            src = os.path.join(menus_src, f)
            dst = os.path.join(menus_dst, f)
            shutil.copy2(src, dst)
            print("  Menu: {}".format(f))
            count += 1
    print("  {} menu files copied".format(count))

    # Copy scaled images
    if os.path.isdir(img_dir):
        count = 0
        for root, dirs, files in os.walk(img_dir):
            rel = os.path.relpath(root, img_dir)
            dst_root = os.path.join(menus_dst, "images", rel) if rel != "." \
                else os.path.join(menus_dst, "images")
            os.makedirs(dst_root, exist_ok=True)
            for f in files:
                if f.endswith(".bmp"):
                    shutil.copy2(os.path.join(root, f), os.path.join(dst_root, f))
                    count += 1
        print("  {} images deployed".format(count))

    # Copy board background as needs_small.bmp at root
    board_path = os.path.join(img_dir, "base", "base_board.bmp")
    if os.path.exists(board_path):
        shutil.copy2(board_path, os.path.join(mount_point, "needs_small.bmp"))
        print("  Board background -> needs_small.bmp")

    # Copy sounds
    sounds_src = os.path.join(menus_src, "sounds")
    if os.path.isdir(sounds_src):
        count = 0
        for root, dirs, files in os.walk(sounds_src):
            rel = os.path.relpath(root, sounds_src)
            dst_root = os.path.join(menus_dst, "sounds", rel) if rel != "." \
                else os.path.join(menus_dst, "sounds")
            os.makedirs(dst_root, exist_ok=True)
            for f in files:
                if f.endswith(".mp3"):
                    shutil.copy2(os.path.join(root, f), os.path.join(dst_root, f))
                    count += 1
        print("  {} sound files deployed".format(count))

    # Copy button_sounds
    bsounds_src = os.path.join(base_dir, "button_sounds")
    if os.path.isdir(bsounds_src):
        count = 0
        bsounds_dst = os.path.join(mount_point, "button_sounds")
        os.makedirs(bsounds_dst, exist_ok=True)
        for f in os.listdir(bsounds_src):
            if f.endswith(".mp3"):
                shutil.copy2(os.path.join(bsounds_src, f),
                             os.path.join(bsounds_dst, f))
                count += 1
        print("  {} button sounds deployed".format(count))

    print("\nDeploy complete!")
    return True


def list_variants():
    """Print all available variants with their resolutions."""
    print("Available variants:")
    print("-" * 50)
    for name, config in sorted(VARIANTS.items()):
        w = config["screen_width"]
        h = config["screen_height"]
        dir_name = image_dir_name(w, h)
        base_dir = os.path.dirname(os.path.abspath(__file__))
        exists = os.path.isdir(os.path.join(base_dir, dir_name))
        status = "ready" if exists else "needs onboarding"
        default = " (DEFAULT)" if name == DEFAULT_VARIANT else ""
        print("  {}{}: {}x{} [{}] {}".format(
            name, default, w, h, dir_name, status))


def main():
    if len(sys.argv) < 2:
        # Default: onboard the default variant
        onboard_variant(DEFAULT_VARIANT)
        return

    arg = sys.argv[1]

    if arg == "--list":
        list_variants()
    elif arg == "--all":
        for name in sorted(VARIANTS.keys()):
            onboard_variant(name)
    elif arg == "--deploy":
        if len(sys.argv) < 4:
            print("Usage: python onboard_device.py --deploy <VARIANT> <MOUNT_POINT>")
            sys.exit(1)
        deploy_to_device(sys.argv[2], sys.argv[3])
    elif arg in VARIANTS:
        onboard_variant(arg)
    else:
        print("Unknown argument: {}".format(arg))
        print("Usage:")
        print("  python onboard_device.py                    # Onboard default variant")
        print("  python onboard_device.py VARIANT_NAME       # Onboard specific variant")
        print("  python onboard_device.py --all              # Onboard all variants")
        print("  python onboard_device.py --list             # List variants")
        print("  python onboard_device.py --deploy VARIANT MOUNT  # Deploy to device")
        sys.exit(1)


if __name__ == "__main__":
    main()

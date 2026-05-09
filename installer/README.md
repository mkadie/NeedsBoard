# AAC Device Installer

Auto-configures a new AAC device from an SD card.

## Quick Start

1. **Flash CircuitPython** onto the target device (see SETUP.md for version)
2. **Prepare SD card:** Copy the entire `installer/` directory to the SD card root
3. **Copy `install_code.py`** to the device as `code.py`
4. **Insert the SD card** into the device
5. **Reboot** — the installer runs automatically
6. **Remove SD card** and reboot to use the device

## How It Works

The installer reads `boot_out.txt` to identify the board and automatically:

- Copies all Python source files
- Sets the correct `DEFAULT_VARIANT` in hardware_config.py
- Copies the right `config.txt` for the device
- Copies all menus, images, and sounds
- Creates the production `code.py` entry point

## Supported Boards

| Board ID | Variant | Device |
|----------|---------|--------|
| `yd_esp32_s3_n16r8` | CYD_PLUS | ESP32-S3 touch screen |
| `adafruit_fruit_jam` | FRUITJAM_V2 | Fruit Jam color LCD |
| `raspberry_pi_pico2` | RP2350_OLED_BADGE_V3 | OLED badge |
| `adafruit_feather_rp2350` | FEATHER_RP2350_V1 | Feather with buttons |

## SD Card Layout

```
SD Card Root/
    installer/
        install_code.py     ← Copy this as code.py to the device
        README.md           ← This file
        common/             ← Python source files (all devices)
            machine.py
            display_manager.py
            audio_player.py
            input_manager.py
            ... (all .py files)
        configs/            ← Per-device config.txt files
            CYD_PLUS.txt
            FRUITJAM_V2.txt
            RP2350_OLED_BADGE_V3.txt
            FEATHER_RP2350_V1.txt
        content/            ← Menus, images, sounds
            needs_small.bmp
            menus/
                base.menu
                food.menu
                base_fruitjam.menu
                food_fruitjam.menu
                images/
                    ... (button images)
                sounds/
                    food/
                        ... (food sound files)
            button_sounds/
                thirsty.mp3
                ... (all sound files)
```

## Customizing for a Specific User

1. Edit the config file in `configs/` for the target device
2. Add custom menus to `content/menus/`
3. Add custom sounds to `content/button_sounds/` or `content/menus/sounds/`
4. Run the installer — it copies everything

## After Installation

- The device auto-detects its board and configures itself
- Teachers can edit `config.txt` on the CIRCUITPY drive to adjust settings
- See GUIDE_FOR_TEACHERS.md for customization instructions

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "installer/ not found" | Make sure the SD card has `installer/` at the root level |
| "Unknown board" | The board isn't in the BOARD_MAP — add it to install_code.py |
| SD card not detected | Check the SD card is formatted as FAT32 and properly seated |
| Files didn't copy | Check SD card isn't write-protected; check free space on CIRCUITPY |

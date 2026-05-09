# AAC Device — Setup Guide

Step-by-step instructions for setting up a new AAC communication device.

## What You Need

- AAC device (CYD_PLUS, Fruit Jam, OLED Badge, or Feather RP2350)
- USB cable (USB-C or Micro-USB depending on the device)
- Computer (Windows, Mac, or Linux)

## Step 1: Install CircuitPython

### CYD_PLUS (ESP32-S3)

**CircuitPython 10.1.4** — Board: `yd_esp32_s3_n16r8`


1. Download the firmware:
   - Go to https://circuitpython.org/board/yd_esp32_s3_n16r8/
   - Download the `.bin` file for version **10.1.4**

2. Put the device in bootloader mode:
   - Hold the **BOOT** button while plugging in USB
   - The device shows up as a serial/JTAG device (not a drive)

3. Flash the firmware:
   ```bash
   pip install esptool
   esptool -p /dev/ttyACM0 --chip esp32s3 write-flash 0x0 adafruit-circuitpython-yd_esp32_s3_n16r8-en_US-10.1.4.bin
   ```
   On Windows, replace `/dev/ttyACM0` with `COM3` (or whichever port appears).

4. Unplug and replug the device (without holding any buttons).

5. A **CIRCUITPY** drive should appear on your computer.

### Fruit Jam (RP2350)

**CircuitPython 10.1.4** — Board: `adafruit_fruit_jam`

1. Download the `.uf2` file from https://circuitpython.org/board/adafruit_fruit_jam/
2. Hold BOOT button while plugging in USB — a **RPI-RP2** drive appears
3. Drag the `.uf2` file onto the drive
4. The device reboots and **CIRCUITPY** appears

### OLED Badge (Pico 2)

**CircuitPython 9.2.9** — Board: `raspberry_pi_pico2`

1. Download the `.uf2` file from https://circuitpython.org/board/raspberry_pi_pico2/
2. Hold BOOTSEL button while plugging in USB — a **RPI-RP2** drive appears
3. Drag the `.uf2` file onto the drive
4. **CIRCUITPY** appears

## Step 2: Install Libraries

The device needs CircuitPython libraries to work. Download the library bundle
that matches your CircuitPython version from https://circuitpython.org/libraries.

Copy these libraries to the `CIRCUITPY/lib/` folder:

### All Devices
- `neopixel.mpy` (if device has NeoPixels)
- `adafruit_bus_device/` (folder)
- `adafruit_register/` (folder)
- `adafruit_display_text/` (folder — for hint text overlay)

### CYD_PLUS (touch screen)
- `adafruit_focaltouch.mpy`
- `adafruit_ili9341.mpy`

### Fruit Jam
- `adafruit_fruitjam/` (folder)
- `adafruit_tlv320.mpy`
- `adafruit_st7735r.mpy`

### OLED Badge
- `adafruit_displayio_ssd1306.mpy`

### Feather RP2350 (Moana's device)
- `adafruit_ili9341.mpy`
- `i2c_expanders/` (folder)

## Step 3: Copy the Software

Copy all `.py` files from the `cyd_plus/` project directory to the **CIRCUITPY** drive:

```
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
```

Or use the deploy script:
```bash
cd cyd_plus
./deploy.sh
```

## Step 4: Set the Device Variant

Edit `hardware_config.py` on the CIRCUITPY drive. Find the last line:

```python
DEFAULT_VARIANT = "FRUITJAM_V2"
```

Change it to match your device:

| Device | Variant Name |
|--------|-------------|
| CYD_PLUS (touch screen) | `CYD_PLUS` |
| Fruit Jam (color LCD + encoder) | `FRUITJAM_V2` |
| OLED Badge (small mono screen) | `RP2350_OLED_BADGE_V3` |
| Feather RP2350 (Moana's device) | `FEATHER_RP2350_V1` |

## Step 5: Copy Menus and Sounds

Create the folder structure on CIRCUITPY and copy all content files:

```
CIRCUITPY/
    menus/
        base.menu               ← Main menu (4x2)
        food.menu               ← Food submenu (4x2)
        base_fruitjam.menu      ← Main menu (3x2, smaller screens)
        food_fruitjam.menu      ← Food submenu (3x2)
        images/                 ← Button images for base menu
            thirsty.bmp
            hungry.bmp
            more.bmp
            bathroom.bmp
            stinky.bmp
            yes.bmp
            no.bmp
            please.bmp
            food/               ← Button images for food menu
                food_board.bmp
                water.bmp
                juice.bmp
                apple.bmp
                milk.bmp
                banana.bmp
                cracker.bmp
                yogurt.bmp
                back.bmp
        sounds/
            food/               ← Sound files for food menu
                water.mp3
                juice.mp3
                apple.mp3
                milk.mp3
                banana.mp3
                cracker.mp3
                yogurt.mp3
    button_sounds/              ← Sound files for base menu
        thirsty.mp3
        hungry.mp3
        bathroom.mp3
        stinky.mp3
        yes.mp3
        no.mp3
        please.mp3
        more.mp3
        read.mp3
        emergency.mp3
    needs_small.bmp             ← Background image (4x2 grid)
```

**Important:** Both images AND sounds must be present, or buttons will
show errors. The food submenu sounds are in `menus/sounds/food/`, not
in `button_sounds/`.

## Step 6: Create config.txt

Create a `config.txt` file on the CIRCUITPY drive:

```
# Basic configuration
sleep_enabled = true
sleep_timeout = 120
volume = 80
start_menu = base.menu
emergency_push_enabled = true
emergency_push_sound = /button_sounds/emergency.mp3
```

See the [Guide for Teachers](GUIDE_FOR_TEACHERS.md) for all available settings.

## Step 7: Test

1. Safely eject the CIRCUITPY drive
2. The device restarts automatically
3. You should see the menu appear on screen within 5 seconds
4. Touch a button (or rotate the encoder) to test

## Troubleshooting

| Problem | Solution |
|---------|----------|
| CIRCUITPY drive doesn't appear | Reflash CircuitPython (Step 1) |
| Device shows Python error on serial | Check that all `.py` files are copied |
| "Unknown variant" error | Check `DEFAULT_VARIANT` in hardware_config.py |
| No sound | Check sound files exist in button_sounds/ |
| Touch doesn't respond | Check `adafruit_focaltouch.mpy` is in lib/ |
| Screen is blank | Check display libraries are in lib/ |

## SD Card Auto-Installer (Recommended)

The easiest way to set up a new device:

1. Flash CircuitPython (Step 1 above)
2. Copy `installer/install_code.py` to the device as `code.py`
3. Insert an SD card containing the `installer/` directory
4. Reboot — the installer detects the board and copies everything
5. Remove the SD card and reboot

The installer automatically:
- Identifies the board from `boot_out.txt`
- Copies the right Python files, config, menus, images, and sounds
- Sets the correct device variant

See `installer/README.md` for details.

## Quick Deploy Script (Developer)

For subsequent updates from a computer:

```bash
cd cyd_plus
./deploy.sh              # Deploy to all connected devices
./deploy.sh --code-only  # Update only Python files (keep config)
```

## Multi-Lingual Language Packs

To deploy language packs to a new Feather RP2350 device:

1. Generate language sounds and menus using the tools in the T-Rex_talker_interactive repo
   (`tools/generate_language_sounds.py` and `tools/generate_language_menus.py`)
2. Language WAV files (~3MB for 96 files across 12 languages) go on the SD card under
   `sd/button_sounds/languages/<lang_code>/`
3. Since the files are too large to fit on flash, use the `move_to_sd` staging mechanism:
   - Copy a batch of language files to `CIRCUITPY/move_to_sd/button_sounds/languages/`
   - Eject and reboot — files auto-copy to the SD card
   - Reconnect and delete the `move_to_sd/` directory from flash
   - Repeat for additional batches if total exceeds free flash space
4. Language display images (1-bit BMP, 320x240, ~113KB total) go directly on flash
   under `menus/images/languages/`
5. Language menu files (`lang_<code>.menu`) go in `menus/`
6. Enable in `hardware_config.py`: `language_switcher_enabled = true`

The language switcher is currently supported on FEATHER_RP2350_V1 only.

## Version Info

| Component | Version |
|-----------|---------|
| CircuitPython (CYD/Fruit Jam) | 10.1.4 |
| CircuitPython (Badge/Feather) | 9.2.x |
| Software | See `git log` for latest |

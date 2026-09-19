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
| *(none — see below)* | FRUITJAM_CLONE_18 | Fruit Jam **clone**, 1.8" ZJY180SN00 panel |

### Picking a variant by hand (`VARIANT.txt`)

Board ID is not always enough. The Fruit Jam **clone** reports the same
`adafruit_fruit_jam` as a genuine Fruit Jam, but needs a different build: its
3V3 rail enable is on `D10` and its encoder button is on `BUTTON1`, where the
genuine board uses `A4` and `D10`. Installing the wrong one of the two gives a
device with a dark screen or a dead button.

To choose explicitly, create a `VARIANT.txt` naming the variant. Two places
are checked, **device first**:

| Location | Scope |
|----------|-------|
| `/VARIANT.txt` on the CIRCUITPY drive | that one device |
| `installer/VARIANT.txt` on the SD card | every device installed from this card |

Put it on the device when one card installs a mix of boards — that is the
usual case for a clone sitting alongside genuine hardware, and it keeps the
card a read-only build artifact.

Either the bare name or the `config.txt` spelling works:

```
FRUITJAM_CLONE_18
```
```
variant = FRUITJAM_CLONE_18
```

Blank lines and `#` comments are ignored. When present this **overrides** the
Board ID table above. The installer prints which source it used (`from
VARIANT.txt` vs `from Board ID`) and refuses to install a variant that is not
in `common/hardware_config.py`, listing the valid names — so a typo fails
loudly instead of producing a device that raises "Unknown variant" at boot.

Delete `VARIANT.txt` to go back to Board ID auto-detection.

## SD Card Layout

```
SD Card Root/
    installer/
        install_code.py     ← Copy this as code.py to the device
        README.md           ← This file
        VARIANT.txt         ← Optional: forces a variant (see above)
        common/             ← Python source files (all devices)
            machine.py
            display_manager.py
            audio_player.py
            input_manager.py
            ... (all .py files)
        configs/            ← Per-device config.txt files
            CYD_PLUS.txt
            FRUITJAM_V2.txt
            FRUITJAM_CLONE_18.txt
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
| "Unknown board" | The board isn't in the BOARD_MAP — add it to install_code.py, or name a variant in `VARIANT.txt` |
| "variant ... is not defined" | Typo in `VARIANT.txt`; it must match a key in `common/hardware_config.py` exactly |
| Installed device is missing a recent fix | `common/` was not re-synced — run `./installer/sync_common.sh` in the repo and rebuild the SD card |
| SD card not detected | Check the SD card is formatted as FAT32 and properly seated |
| Files didn't copy | Check SD card isn't write-protected; check free space on CIRCUITPY |

## Keeping `common/` current

`installer/common/` is copied verbatim onto the device, so **it is the shipped
code** for SD-card installs. Nothing syncs it automatically, and when it drifts
the symptom is confusing: a freshly installed device behaves like an old build,
missing variants and fixes that are plainly present in the repo.

After changing any module at the repo root, run:

```bash
./installer/sync_common.sh          # copy repo root -> installer/common/
./installer/sync_common.sh --check  # report only; exits non-zero if stale
```

Commit the synced files alongside the change that prompted them.

The list of modules that ship lives in `SHIP_FILES` at the top of the script —
add a new module there, not just to `common/`. `--check` reports `STALE` (a
mirrored file is behind), `MISSING` (a shipped module absent from the mirror)
and `ORPHAN` (a file in `common/` nothing ships any more), and exits non-zero
for the first two.

There is currently no CI and no git hook running `--check`, so keeping the
mirror current is still a manual step — see the note in the PR about replacing
the committed mirror with a build step.

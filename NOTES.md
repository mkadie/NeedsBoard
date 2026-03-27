# Development Notes & Future Considerations

## CircuitPython Version Notes

- CYD_PLUS and Fruit Jam use **CircuitPython 10.1.4** (10.x branch)
- OLED Badge (Pico 2) uses **CircuitPython 9.2.9**
- Feather RP2350 uses **CircuitPython 9.2.6**
- The 10.1 branch was reported as not working 100% on some configurations — test thoroughly before upgrading existing devices
- Board ID for CYD_PLUS: `yd_esp32_s3_n16r8`
- Flash command: `esptool -p /dev/ttyACMx --chip esp32s3 write-flash 0x0 <firmware>.bin`

## Pocket Activation / Accidental Presses

The device can be triggered accidentally when carried in a pocket or bag. Consider:

- **Lock mode**: Require a specific gesture (e.g., encoder press + rotate) to unlock
- **Proximity sensor**: Detect when screen is covered (face-down/pocket) and ignore input
- **Motion-based lock**: Use accelerometer to detect when device is being carried vs. held
- **Sleep-on-flip**: If device has an accelerometer, sleep when face-down
- **Configurable lock timeout**: Auto-lock after N seconds in pocket (detected by no meaningful interaction pattern — random touches vs. deliberate presses)
- **Emergency bypass**: Emergency hold should ALWAYS work even when locked — that's the point

## Emergency Sound Considerations

- Current emergency message: "Please Stand Back, I cannot speak right now, but I am OK. Crowding me makes it worse. Thank you."
- Consider multiple emergency messages configurable per user
- Consider a "repeat" feature — if the emergency sound just played, a quick press replays it
- The 3-second hold time may need adjustment per user — some users have motor difficulties that make long holds hard. Make `emergency_hold_seconds` configurable (already done)
- Consider visual feedback during the hold — count-down on OLED or progress bar on color screen

## Audio Quality

- MP3 decoding competes with display updates for CPU time — emergency sound plays before any display init to avoid choppiness
- Direct I2S (badge) gives instant audio; TLV320 DAC (Fruit Jam) needs ~0.2s minimal init
- Full Peripherals import takes 1.3s — bypass for emergency path
- Consider pre-decoded audio (WAV) for critical sounds — faster to start but larger files

## Display Considerations

- OLED 128x32: Max 21 chars per line at terminalio.FONT scale=1
- All text_description fields must be ≤21 chars for OLED compatibility
- 3-line mode (show_border=false) is more usable for navigation
- Color screens: hint text overlay appears at bottom — may overlap with button images. Consider semi-transparent background or positioning based on grid layout
- Consider larger font option for users with visual impairments

## Power Management

- FULL_POWER pin (A4 on Fruit Jam) gates 3V3_Switched rail — active low
- Sleep wake does microcontroller.reset() — full reboot takes ~5s
- Emergency push check happens on every boot, so wake-by-button triggers it automatically
- Badge (Pico 2) doesn't have alarm module — need software idle polling
- Consider measuring battery voltage if ADC is available

## Multi-Device Architecture

- config.txt is per-device (lives on CIRCUITPY drive)
- hardware_config.py has ALL variants but DEFAULT_VARIANT selects one
- When deploying to a new device, only need to change DEFAULT_VARIANT and config.txt
- Consider auto-detection: read board.board_id to pick variant automatically

## Menu System

- Current limit: menus must fit in RAM — large vocabularies may need pagination
- SD card support exists but not all devices have one
- Consider caching parsed menu data to speed up boot
- Sound files referenced in menus must exist or playback fails silently
- Food submenu sounds are in menus/sounds/food/ — easy to miss when deploying

## Encoder Navigation

- encoder_direction_flip differs between Fruit Jam and Badge — hardware dependent
- Each device needs its own config.txt with the right flip setting
- Consider auto-calibrating: on first boot, show "turn right" prompt

## Deployment Strategy

Three ways to deploy to a new device:

1. **SD Card Auto-Installer** (recommended for production)
   - Prepare SD card with `installer/` directory once
   - Flash CircuitPython, copy install_code.py as code.py, insert SD, reboot
   - Installer auto-detects board and copies everything
   - See `installer/README.md`

2. **deploy.sh** (developer, USB connected)
   - Run `./deploy.sh` from the repo on a computer
   - Deploys to all connected CIRCUITPY drives

3. **Manual copy** (one-off)
   - Copy files individually per the checklist below

## Deployment Checklist for New Devices

**Common mistake:** Deploying Python code but forgetting content files.
The device needs ALL of these to work properly:

- [ ] CircuitPython firmware (correct version for the board)
- [ ] CircuitPython libraries in `lib/` (device-specific, see SETUP.md)
- [ ] All `.py` production code files
- [ ] `hardware_config.py` with correct `DEFAULT_VARIANT`
- [ ] `config.txt` with device-appropriate settings
- [ ] `needs_small.bmp` background image (4x2 grid devices)
- [ ] `menus/*.menu` files
- [ ] `menus/images/*.bmp` — base menu button images
- [ ] `menus/images/food/*.bmp` — food menu images + board
- [ ] `menus/sounds/food/*.mp3` — food menu sound files
- [ ] `button_sounds/*.mp3` — base menu sound files + emergency.mp3

**Note:** Food sounds are in `menus/sounds/food/`, NOT in `button_sounds/`.
This is a common source of "no sound on food menu" bugs.

**Note:** `needs_small.bmp` must be the 16-color palette BMP (mode=P) from
the working device. The master_images version is a different image (shows
"Talker" branding). The correct file is saved in the repo root. Do NOT
regenerate from master_images — always copy from the repo or a working device.

## Testing Checklist for New Devices

1. Verify serial port detection (udevadm info)
2. Check display init (correct driver, rotation, I2C vs SPI)
3. Test audio playback (correct I2S pins, DAC config)
4. Test encoder direction (flip if needed in config.txt)
5. Test emergency push (hold button during boot)
6. Test emergency hold (hold button 3s while active)
7. Test sleep/wake cycle
8. Test submenu navigation and back
9. Verify all sound files present (base AND food menus)
10. Verify all image files present (base AND food menus)
11. Check text_description display on OLED / hint text on color

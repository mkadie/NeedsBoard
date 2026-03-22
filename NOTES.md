# Development Notes & Future Considerations

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

## Testing Checklist for New Devices

1. Verify serial port detection (udevadm info)
2. Check display init (correct driver, rotation, I2C vs SPI)
3. Test audio playback (correct I2S pins, DAC config)
4. Test encoder direction (flip if needed in config.txt)
5. Test emergency push (hold button during boot)
6. Test emergency hold (hold button 3s while active)
7. Test sleep/wake cycle
8. Test submenu navigation and back
9. Verify all sound files present
10. Check text_description display on OLED / hint text on color

# T-Rex Talk — Version History

## Version 3.0 — "T-Rex Talk" (March 2026)

**Status: Working Release**

Complete rewrite of the AAC software with multi-device support, modular
architecture, and production deployment tools.

### Supported Devices
| Device | Display | Input | Audio |
|--------|---------|-------|-------|
| CYD_PLUS (ESP32-S3) | 320x240 ILI9341 touch | Touch + optional encoder | ES8311 codec |
| FRUITJAM_V2 (RP2350B) | 160x128 ST7735R | Rotary encoder | TLV320 DAC |
| RP2350_OLED_BADGE_V3 (Pico 2) | 128x32 SSD1306 OLED | Rotary encoder | Direct I2S |
| FEATHER_RP2350_V1 (Feather RP2350) | 320x240 ILI9341 | 8 I2C buttons + encoder | Direct I2S |

### Key Features
- **Menu system**: INI-style .menu files editable by teachers — no code needed
- **Grid and list menus**: 4x2, 3x2, or scrollable text lists
- **Submenus**: Navigate between topic boards (food, feelings, etc.)
- **Emergency push**: Hold button at boot for instant help message (~1.2s)
- **Emergency hold**: Hold button 3 seconds while active for help message
- **config.txt**: Plain text configuration for volume, sleep, speed, encoder direction
- **Playback speed**: Adjustable 25-200% for pre-verbal learners
- **Text descriptions**: OLED text display with 3-line scrolling, hint text on color screens
- **Zoom images**: Full-screen button image during sound playback (configurable)
- **Sleep/wake**: Light sleep on ESP32, software idle on RP2350, touch/button wake
- **SD card auto-installer**: Drop files on SD, auto-detects board and configures
- **Multi-language**: Thai/English bilingual support (Moana's device)
- **Multi-lingual language pack switcher**: 12 languages with full-screen display images (1-bit BMP)
- **move_to_sd staging mechanism**: Auto-copy files from flash staging dir to SD card on boot
- **WAV-only audio on Feather RP2350**: MP3 decoder bug — WAV 16kHz 16-bit mono as workaround
- **NeoPixel feedback**: Button light animations during playback
- **WAV and MP3**: Both audio formats supported

### Architecture
- `machine.py` — Main orchestrator
- `hardware_config.py` — All device variants in one file
- `config.txt` — User-editable settings (overlays hardware defaults)
- `display_manager.py` — SPI color + I2C OLED display support
- `audio_player.py` — MP3/WAV with speed control
- `input_manager.py` — Touch, encoder (hardware + software), I2C expander buttons
- `sleep_manager.py` — Light sleep, software idle, FULL_POWER gating
- `menu_parser.py` — INI-style .menu file reader
- `action.py` — Press actions: sound, image, vibrate, light, navigate

---

## Version 2.0 — "NeedsBoard" (2025)

**Status: Archived**

Original NeedsBoard project with sprite-based menu system on ESP32-S3.

### Hardware
- ESP32-S3 (YD-ESP32-S3 N16R8) or RP2040
- ILI9341 320x240 display
- I2S audio output
- PCA9555 I2C button expanders (8 buttons)
- NeoPixel LED feedback (32 LEDs, 4 per button)
- Rotary encoder for menu navigation
- SD card for additional storage
- SSD1306 OLED (optional, on some builds)

### Features
- Sprite sheet menu system (fast tile switching)
- WAV audio playback
- NeoPixel chase animations per button
- I2C button expander support via PCA9555
- Rotary encoder navigation
- SD card file storage
- Button configuration via Python file (button_config.py)
- Thai language support (Moana's device)

### Software
- `code.py` — Monolithic main loop
- `SpriteMenu.py` — Sprite sheet tile-based menu display
- `button_config.py` — Hardcoded button-to-sound mapping
- `FileUtils.py` — BMP file utilities
- `IO_Expander.py` — I2C expander driver

### Limitations
- Single-file architecture (not modular)
- No teacher-editable configuration
- No sleep/power management
- No emergency features
- No text-only display support
- Button layout hardcoded in Python

---

## Version 1.0 — "Badge" (2024-2025)

**Status: Archived**

Simple badge-style device with OLED display and direct I2S audio.

### Hardware
- Raspberry Pi Pico 2 (RP2350) or RP2040
- SSD1306 128x32 OLED display (I2C)
- I2S audio output
- Rotary encoder
- SD card (optional)

### Features
- Text-based menu on OLED
- MP3 and WAV playback
- Encoder scroll and select
- "Good morning" startup greeting
- Basic button configuration

### Software
- Single `code.py` with inline initialization
- No modular architecture
- No configuration files

---

## Version 0.x — Early Prototypes (2024)

- MSP430-based button latch boards
- LED matrix experiments
- Initial 3D printed enclosure designs
- First Thai voice recordings
- Hardware button decoder (3-bit binary)

---

## Project Origins

This project was started by Michael Kadie to help individuals with
special needs communicate. In the early 1990s, Michael built two speech
boards for children with different abilities. The current project
continues that mission with modern hardware and open-source software,
making AAC devices accessible and customizable by teachers and parents.

The name "T-Rex Talk" reflects the goal: giving a voice to those who
need one, with the strength and persistence of a T-Rex.

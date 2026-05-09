"""Hardware configuration for AAC device machine variants.

Each variant is a dictionary of hardware settings. Pin names are strings
resolved at runtime via getattr(board, name) to keep this file import-free.
"""

VARIANTS = {
    "CYD_PLUS": {
        "name": "CYD_PLUS",

        # Display
        "display_type": "ILI9341",
        "screen_width": 320,
        "screen_height": 240,
        "display_rotation": 180,
        "display_inverted": True,  # IPS panel needs INVON (0x21)
        "background_image": "/needs_small.bmp",
        "lcd_cs": "GPIO10",
        "lcd_dc": "GPIO46",
        "lcd_sclk": "GPIO12",
        "lcd_mosi": "GPIO11",
        "lcd_miso": "GPIO13",
        "lcd_backlight": "GPIO45",
        "lcd_reset": None,

        # Audio
        "sound_system": "ES8311",
        "codec_sample_rate": 22050,
        "volume": 80,
        "i2s_bclk": "GPIO5",
        "i2s_ws": "GPIO7",
        "i2s_dout": "GPIO8",
        "i2s_mclk": "GPIO4",
        "amp_en_pin": "GPIO1",
        "amp_en_active_low": True,

        # SD Card (no onboard slot; set True if external breakout wired)
        "sd_card": False,
        "sd_cs": None,
        "sd_sclk": None,
        "sd_mosi": None,
        "sd_miso": None,
        "sd_shares_display_spi": False,

        # Shared I2C bus (touch + codec)
        "i2c_scl": "GPIO15",
        "i2c_sda": "GPIO16",
        "i2c_freq": 400_000,

        # Touch screen
        "touch_screen": True,
        "touch_type": "FT6336G",
        "touch_rst": "GPIO18",
        "touch_int": "GPIO17",
        "touch_swap_xy": True,
        "touch_flip_x": True,
        "touch_flip_y": False,

        # Physical buttons
        "max_buttons": 0,

        # Rotary encoder — optional, on expansion port
        # IO2=A, IO3=B, IO14=button, IO21=GND (driven low)
        "rotary_encoder": False,
        "encoder_navigation": False,
        "encoder_pin_a": "GPIO2",
        "encoder_pin_b": "GPIO3",
        "encoder_button_pin": "GPIO14",
        "encoder_button_index": 0,
        "encoder_gnd_pin": "GPIO21",  # Drive low as ground for encoder

        # Wake / extra button
        "wake_button_pin": "GPIO0",
        "wake_button_index": 8,

        # Status LED
        "neopixel_pin": "GPIO42",

        # Button grid layout
        "button_cols": 4,
        "button_rows": 2,
        "debounce_time": 0.5,

        # Sleep / power saving
        # sleep_enabled: True to auto-sleep after inactivity
        # sleep_timeout: seconds of inactivity before sleeping
        # sleep_mode: "light" (fast wake, program resumes) or
        #             "deep" (lowest power, full restart on wake)
        # sleep_wake_pins: list of pin names that wake the device
        #   - touch_int pin wakes on screen touch
        #   - wake_button_pin wakes on boot button press
        "sleep_enabled": True,
        "sleep_timeout": 120,
        "sleep_mode": "light",
        "sleep_wake_pins": ["GPIO0", "GPIO17"],
        "wake_ignore_seconds": 1.0,  # Grace period — instant wake needs this
    },

    "RP2350_V2": {
        "name": "RP2350_V2",

        # Display
        "display_type": "ILI9341",
        "screen_width": 320,
        "screen_height": 240,
        "display_rotation": 0,
        "display_inverted": False,
        "background_image": "/needs_small.bmp",
        "lcd_cs": "GP3",
        "lcd_dc": "GP26",
        "lcd_sclk": "GP14",
        "lcd_mosi": "GP15",
        "lcd_miso": "GP12",
        "lcd_backlight": None,
        "lcd_reset": "GP22",

        # Audio
        "sound_system": "I2S_DIRECT",
        "codec_sample_rate": 22050,
        "volume": 80,
        "i2s_bclk": "GP4",
        "i2s_ws": "GP5",
        "i2s_dout": "GP6",
        "i2s_mclk": None,
        "amp_en_pin": None,
        "amp_en_active_low": False,

        # SD Card (shares SPI bus with display)
        "sd_card": True,
        "sd_cs": "GP21",
        "sd_sclk": "GP14",
        "sd_mosi": "GP15",
        "sd_miso": "GP12",
        "sd_shares_display_spi": True,

        # I2C
        "i2c_scl": "GP17",
        "i2c_sda": "GP16",
        "i2c_freq": 400_000,

        # Touch screen
        "touch_screen": False,

        # Physical buttons (3-bit hardware decoder)
        "max_buttons": 8,
        "button_data_pins": ["GP8", "GP9", "GP10"],
        "button_int_pin": "GP7",
        "button_latch_reset_pin": "GP11",

        # Rotary encoder
        "rotary_encoder": True,
        "encoder_pin_a": "GP0",
        "encoder_pin_b": "GP1",
        "encoder_button_pin": "GP2",
        "encoder_button_index": 8,

        # Wake / extra button
        "wake_button_pin": None,
        "wake_button_index": 8,

        # Status LED
        "neopixel_pin": None,

        # Button grid layout
        "button_cols": 4,
        "button_rows": 2,
        "debounce_time": 0.5,

        # Sleep / power saving
        # RP2040/RP2350 does not support alarm module — sleep disabled
        "sleep_enabled": False,
        "sleep_timeout": 120,
        "sleep_mode": "light",
        "sleep_wake_pins": [],
    },

    "FRUITJAM_V2": {
        "name": "FRUITJAM_V2",

        # Display — ST7735S 1.77" 160x128 (landscape via rotation=90)
        "display_type": "ST7735R",
        "screen_width": 160,
        "screen_height": 128,
        "display_rotation": 90,
        "display_inverted": False,
        "background_image": None,  # Menu system provides background
        "lcd_cs": "A3",
        "lcd_dc": "A2",
        "lcd_sclk": "SCK",
        "lcd_mosi": "MOSI",
        "lcd_miso": "MISO",
        "lcd_backlight": None,  # Backlight on 3V3_SWITCHED rail
        "lcd_reset": "A1",
        # ST7735R-specific settings
        "st7735_colstart": 2,
        "st7735_rowstart": 1,
        "st7735_bgr": True,
        "spi_baudrate": 24_000_000,

        # Audio — TLV320DAC3100 via Fruit Jam Peripherals
        "sound_system": "FRUITJAM_DAC",
        "codec_sample_rate": 22050,
        "volume": 80,
        "dac_volume": -10,       # dB
        "speaker_volume": 0,     # dB
        "speaker_gain": 24,      # dB
        # I2S pins not used directly — Peripherals handles them
        "i2s_bclk": None,
        "i2s_ws": None,
        "i2s_dout": None,
        "i2s_mclk": None,
        "amp_en_pin": None,
        "amp_en_active_low": False,

        # FULL_POWER — gates 3V3_SWITCHED rail (LCD VCC, IOVCC, backlight)
        # Active low: LOW = power on, HIGH = power off
        "full_power_pin": "A4",
        "full_power_active_low": True,
        "full_power_settle_ms": 100,

        # Peripherals reset — must be HIGH for DAC operation
        "periph_reset_pin": "PERIPH_RESET",

        # SD Card — none on current daughterboard
        "sd_card": False,
        "sd_cs": None,
        "sd_sclk": None,
        "sd_mosi": None,
        "sd_miso": None,
        "sd_shares_display_spi": False,

        # I2C (for Peripherals / DAC)
        "i2c_scl": "SCL",
        "i2c_sda": "SDA",
        "i2c_freq": 400_000,

        # Touch screen — none
        "touch_screen": False,

        # Physical buttons — not connected on current daughterboard
        "max_buttons": 0,
        # "direct_button_pins": ["A4", "A5", "D6", "D7"],  # Enable when tested
        "direct_buttons_active_low": True,

        # Rotary encoder — navigation mode: rotate to select, press to activate
        "rotary_encoder": True,
        "encoder_navigation": True,
        "encoder_pin_a": "D8",
        "encoder_pin_b": "D9",
        "encoder_button_pin": "D10",
        "encoder_button_index": 0,

        # Wake / extra button
        "wake_button_pin": None,
        "wake_button_index": 5,

        # Status LED — NeoPixel not connected via 32-pin socket
        "neopixel_pin": None,

        # Button grid layout — 3x2 for 160x128 display
        "button_cols": 3,
        "button_rows": 2,

        # Defaults below can be overridden in config.txt
        "debounce_time": 0.5,
        "start_menu": "base_fruitjam.menu",
        "volume": 80,
        "emergency_push_enabled": True,
        "emergency_push_sound": "/button_sounds/emergency.mp3",
        "emergency_hold_enabled": True,
        "emergency_hold_seconds": 3,
        "sleep_enabled": True,
        "sleep_timeout": 120,

        # Hardware-specific sleep settings (not in config.txt)
        "sleep_mode": "software_idle",
        "sleep_wake_pins": [],
    },

    "RP2350_OLED_BADGE_V3": {
        "name": "RP2350_OLED_BADGE_V3",

        # Display — SSD1306 OLED 128x32 monochrome via I2C
        "display_type": "SSD1306",
        "screen_width": 128,
        "screen_height": 32,
        "display_rotation": 180,
        "display_inverted": False,
        "background_image": None,  # Text-only display
        "display_text_mode": True,  # Use text_description instead of images

        # I2C bus (OLED + EEPROM)
        "i2c_scl": "GP17",
        "i2c_sda": "GP16",
        "i2c_freq": 400_000,

        # Audio — direct I2S (no codec, no Peripherals)
        "sound_system": "I2S_DIRECT",
        "codec_sample_rate": 22050,
        "i2s_bclk": "GP4",
        "i2s_ws": "GP5",
        "i2s_dout": "GP6",
        "i2s_mclk": None,
        "amp_en_pin": None,
        "amp_en_active_low": False,

        # No FULL_POWER pin — always on
        "full_power_pin": None,

        # SD Card
        "sd_card": True,
        "sd_cs": "GP21",
        "sd_sclk": "GP14",
        "sd_mosi": "GP15",
        "sd_miso": "GP12",
        "sd_shares_display_spi": False,

        # Touch screen — none
        "touch_screen": False,

        # Physical buttons — none (badge has no external buttons)
        "max_buttons": 0,

        # Rotary encoder — navigation mode
        "rotary_encoder": True,
        "encoder_navigation": True,
        "encoder_pin_a": "GP0",
        "encoder_pin_b": "GP1",
        "encoder_button_pin": "GP2",
        "encoder_button_index": 0,

        # Wake / extra button
        "wake_button_pin": None,
        "wake_button_index": 0,

        # Status LED — none
        "neopixel_pin": None,

        # Button grid layout — single column for text scrolling
        "button_cols": 1,
        "button_rows": 6,

        # Defaults (overridable in config.txt)
        "debounce_time": 0.5,
        "start_menu": "base_fruitjam.menu",
        "volume": 80,
        "emergency_push_enabled": True,
        "emergency_push_sound": "/button_sounds/emergency.mp3",
        "emergency_hold_enabled": True,
        "emergency_hold_seconds": 3,
        "sleep_enabled": True,
        "sleep_timeout": 120,

        # Hardware-specific sleep settings
        "sleep_mode": "light",
        "sleep_wake_pins": [],
    },

    "FEATHER_RP2350_V1": {
        "name": "FEATHER_RP2350_V1",

        # Display — ILI9341 320x240 SPI
        "display_type": "ILI9341",
        "screen_width": 320,
        "screen_height": 240,
        "display_rotation": 180,
        "display_inverted": False,
        "background_image": "/lcd_images/0_needs_small_unc.bmp",
        "lcd_cs": "D10",
        "lcd_dc": "TX",
        "lcd_sclk": "SCK",
        "lcd_mosi": "MOSI",
        "lcd_miso": "MISO",
        "lcd_backlight": None,
        "lcd_reset": "A0",
        "spi_baudrate": None,

        # Sprite sheet for fast menu switching
        "sprite_sheet": "/lcd_images/needs.bmp",
        "sprite_tile_width": 320,
        "sprite_tile_height": 200,
        "sprite_default_tile": 8,

        # Audio — direct I2S
        "sound_system": "I2S_DIRECT",
        "codec_sample_rate": 22050,
        "i2s_bclk": "A1",
        "i2s_ws": "A2",
        "i2s_dout": "A3",
        "i2s_mclk": None,
        "amp_en_pin": None,
        "amp_en_active_low": False,

        # No FULL_POWER pin
        "full_power_pin": None,

        # SD Card — shares SPI bus
        "sd_card": True,
        "sd_cs": "RX",
        "sd_sclk": "SCK",
        "sd_mosi": "MOSI",
        "sd_miso": "MISO",
        "sd_shares_display_spi": True,

        # I2C (PCA9555 expanders, EEPROM)
        "i2c_scl": "SCL",
        "i2c_sda": "SDA",
        "i2c_freq": 400_000,

        # Touch screen — none
        "touch_screen": False,

        # Physical buttons — 8 via dual PCA9555 I2C expanders
        "max_buttons": 8,
        "button_type": "i2c_expander",
        "i2c_expander_addresses": [0x20, 0x24],
        "i2c_expander_pins": [4, 5, 6, 7],  # Pins on each expander
        "button_int_pin": "D25",
        "button_latch_reset_pin": "D24",

        # Rotary encoder
        "rotary_encoder": True,
        "encoder_navigation": True,
        "encoder_pin_a": "D6",
        "encoder_pin_b": "D5",
        "encoder_button_pin": "D9",
        "encoder_button_index": 0,

        # Wake / extra button
        "wake_button_pin": None,
        "wake_button_index": 0,

        # NeoPixel — 32 LEDs (4 per button)
        "neopixel_pin": "D13",
        "neopixel_count": 32,
        "neopixel_per_button": 4,

        # Vibration motor
        "vibration_pin": None,  # TODO: wire up vibration motor pin
        "vibration_enabled": True,

        # Button grid layout — 4x2
        "button_cols": 4,
        "button_rows": 2,

        # Defaults (overridable in config.txt)
        "debounce_time": 0.5,
        "start_menu": "base.menu",
        "volume": 80,
        "emergency_push_enabled": True,
        "emergency_push_sound": "/button_sounds/emergency.mp3",
        "emergency_hold_enabled": True,
        "emergency_hold_seconds": 3,
        "language_switcher_enabled": True,
        "sleep_enabled": True,
        "sleep_timeout": 120,

        # Hardware-specific sleep settings
        "sleep_mode": "light",
        "sleep_wake_pins": [],
    },

    "FRUITJAM_DVI_KBD": {
        "name": "FRUITJAM_DVI_KBD",

        # Display — onboard DVI/HDMI output. The RP2350B firmware only
        # accepts a fixed set of framebuffer sizes:
        #   {(320,240), (360,200), (640,480), (720,400)}.
        # 320x240 is auto-2x-scaled to 640x480 HDMI at 16 bpp.
        # Bring-up:
        #     import displayio, supervisor
        #     from adafruit_fruitjam.peripherals import request_display_config
        #     displayio.release_displays()
        #     request_display_config(320, 240)
        #     display = supervisor.runtime.display   # NOT board.DISPLAY
        "display_type": "FRUITJAM_DVI",
        "screen_width": 320,
        "screen_height": 240,
        "framebuffer_pixel_scale": 2,    # 320x240 -> 640x480 HDMI signal
        "framebuffer_color_depth": 16,
        "display_rotation": 0,
        "display_inverted": False,
        # Initial background while menu loads — overridden by menu.background.
        "background_image": "/menus/images/needs_small.bmp",
        "start_menu": "base_moana.menu",   # canonical Moana 8-button board
        # SPI-display pins are unused (DVI uses dedicated CKP/CKN/D0..2 P/N pairs)
        "lcd_cs": None,
        "lcd_dc": None,
        "lcd_sclk": None,
        "lcd_mosi": None,
        "lcd_miso": None,
        "lcd_backlight": None,
        "lcd_reset": None,

        # Audio — TLV320DAC3100 via Fruit Jam Peripherals (matches FRUITJAM_V2)
        "sound_system": "FRUITJAM_DAC",
        "codec_sample_rate": 22050,
        "volume": 80,
        "dac_volume": -10,
        "speaker_volume": 0,
        "speaker_gain": 24,
        "i2s_bclk": None,
        "i2s_ws": None,
        "i2s_dout": None,
        "i2s_mclk": None,
        "amp_en_pin": None,
        "amp_en_active_low": False,

        # No daughterboard rail to gate on bare Fruit Jam
        "full_power_pin": None,
        "full_power_active_low": False,
        "full_power_settle_ms": 0,

        # Peripherals reset — must be HIGH for DAC operation
        "periph_reset_pin": "PERIPH_RESET",

        # SD Card — onboard SDIO slot present but disabled here until tested.
        "sd_card": False,
        "sd_cs": "SD_CS",
        "sd_sclk": "SD_SCK",
        "sd_mosi": "SD_MOSI",
        "sd_miso": "SD_MISO",
        "sd_shares_display_spi": False,

        # I2C (DAC + STEMMA peripherals)
        "i2c_scl": "SCL",
        "i2c_sda": "SDA",
        "i2c_freq": 400_000,

        # No touch screen on a DVI monitor
        "touch_screen": False,

        # Input — USB HID keyboard via the Fruit Jam USB host port.
        # Requires /boot.py with usb_host.Port() — see docs.
        "input_type": "USB_HID_KEYBOARD",
        "usb_host_dp": "USB_HOST_DATA_PLUS",
        "usb_host_dm": "USB_HOST_DATA_MINUS",
        "usb_host_5v_power": "USB_HOST_5V_POWER",

        # Onboard buttons — 3 tactile buttons on the Fruit Jam PCB.
        # Active-LOW with internal pull-up. max_buttons here counts decoder-bus
        # buttons (none here); the 3 onboard ones are direct GPIO.
        "max_buttons": 0,
        "direct_button_pins": ["BUTTON1", "BUTTON2", "BUTTON3"],
        "direct_buttons_active_low": True,

        # Rotary encoder — not used in this variant (keyboard handles navigation)
        "rotary_encoder": False,
        "encoder_navigation": False,
        "encoder_pin_a": None,
        "encoder_pin_b": None,
        "encoder_button_pin": None,
        "encoder_button_index": 0,

        "wake_button_pin": "BUTTON1",
        "wake_button_index": 0,

        # Onboard 5x NeoPixel strip
        "neopixel_pin": "NEOPIXEL",
        "neopixel_count": 5,

        # 4x2 = 8 cells, mapped 1:1 to keypad keys 1..8
        "button_cols": 4,
        "button_rows": 2,
        "debounce_time": 0.05,

        # Sleep — software idle (RP2350B has no alarm module).
        "sleep_enabled": False,
        "sleep_timeout": 120,
        "sleep_mode": "software_idle",
        "sleep_wake_pins": [],
    },
}

# Change this single line to switch machine variant
DEFAULT_VARIANT = "FRUITJAM_V2"

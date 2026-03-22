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
        "display_rotation": 0,
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
        "touch_flip_x": False,
        "touch_flip_y": True,

        # Physical buttons
        "max_buttons": 0,
        "rotary_encoder": False,

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
        "sleep_enabled": True,
        "sleep_timeout": 120,

        # Hardware-specific sleep settings (not in config.txt)
        "sleep_mode": "software_idle",
        "sleep_wake_pins": [],
    },
}

# Change this single line to switch machine variant
DEFAULT_VARIANT = "FRUITJAM_V2"

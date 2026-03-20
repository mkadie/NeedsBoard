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
    },

    "TALKER_PICO2": {
        "name": "TALKER_PICO2",

        # Display
        "display_type": "ILI9341",
        "screen_width": 320,
        "screen_height": 240,
        "display_rotation": 180,
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
    },
}

# Change this single line to switch machine variant
DEFAULT_VARIANT = "CYD_PLUS"

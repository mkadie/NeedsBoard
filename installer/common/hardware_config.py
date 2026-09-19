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
        # sleep_wake_pins: list of pin names that wake the device. Active
        #   low, internally pulled up. Falls back to the emergency-push /
        #   encoder button if left empty.
        #   - touch_int pin wakes on screen touch
        #   - wake_button_pin wakes on boot button press
        # full_power_feeds_inputs: True when the FULL_POWER rail also powers
        #   the wake inputs. Sleep then blanks the panel but leaves the rail
        #   up, because cutting it would remove the only way to wake.
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

        # Display — ZJY180SN00: a cheap bare 1.8" TFT panel, ST7735(S/R)
        # controller, 128x160 native portrait -> 160x128 landscape via
        # rotation=90. Sold as "1.8 inch" (the 180 in the part number is the
        # size, not the pixel count); often listed loosely as a 2" panel.
        # Datasheet filename seen in the wild: ZJY180SN009.pdf.
        # Wired into the same daughterboard socket as the 2.8" ILI9341 used by
        # FRUITJAM_LCD_28 — only the controller, resolution and grid differ,
        # so swapping panels means switching between those two variants.
        # Needs the 160x128 asset set (image_160x128/, 3x2 grid), NOT the
        # 320x240 one; the colstart/rowstart offsets below are what centres
        # this particular panel's visible window.
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
        # Route audio out of the headphone jack rather than the speaker.
        # Without this the AudioPlayer falls back to "speaker" (headset
        # auto-detect is off on this variant, so the route stays fixed).
        "audio_output_default": "headphone",
        "headphone_volume": 0,           # dB
        "headphone_left_gain": 9,        # dB
        "headphone_right_gain": 9,       # dB
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

    "FRUITJAM_CLONE_18": {
        "name": "FRUITJAM_CLONE_18",
        # Fruit Jam *clone* (bench unit UID 62AB3604F4D0B8E6, CircuitPython
        # 10.2.1). Same ZJY180SN00 1.8" panel and encoder as FRUITJAM_V2, but
        # the board differs in three ways that all force config changes:
        #
        #   1. The auxiliary 3V3 rail (screen + other optional devices) is
        #      gated by an ACTIVE-LOW-enable load switch on GPIO10 (=board.D10)
        #      with an external pull-up (new board rev): drive D10 LOW to enable
        #      the rail, RELEASE D10 to high-Z to disable it (the pull-up floats
        #      the enable off). Same polarity as FRUITJAM_V2's active-low
        #      FULL_POWER (on A4); only the pin differs. (An earlier rev of this
        #      board used an active-HIGH TPS22917 here; the design inverted it.)
        #   2. That steals D10, which FRUITJAM_V2 uses as the encoder button.
        #      The clone's encoder button is instead wired to BUTTON1 (= GPIO0,
        #      verified on the bench 2026-09-18). Peripherals() claims BUTTON1
        #      as one of its three buttons, but machine._init_fruitjam_
        #      peripherals() deinits those right after init, so InputManager
        #      can claim it. Rotation stays on D8/D9.
        #   3. The I2C pull-ups were originally unpopulated, which made the
        #      TLV320 DAC unreachable and forced sound_system = "NONE". They
        #      are now FITTED, so audio is enabled below (bench-verified
        #      2026-09-18 on both the speakers and the headphone jack).
        #      See documents/tps22917_load_switch_processed.md.

        # Display — identical panel + wiring to FRUITJAM_V2.
        "display_type": "ST7735R",
        "screen_width": 160,
        "screen_height": 128,
        "display_rotation": 90,
        "display_inverted": False,
        "background_image": None,
        "start_menu": "base_fruitjam.menu",
        "lcd_cs": "A3",
        "lcd_dc": "A2",
        "lcd_sclk": "SCK",
        "lcd_mosi": "MOSI",
        "lcd_miso": "MISO",
        "lcd_backlight": None,
        "lcd_reset": "A1",
        "st7735_colstart": 2,
        "st7735_rowstart": 1,
        "st7735_bgr": True,
        "spi_baudrate": 24_000_000,

        # Rail enable — ACTIVE LOW (new board rev): drive D10 LOW to power the
        # screen + optional devices; RELEASE the pin (high-Z) to cut the rail,
        # where an external pull-up holds the load switch off.
        "full_power_pin": "D10",
        "full_power_active_low": True,
        "full_power_off_release": True,   # disable by releasing, not driving high
        "full_power_settle_ms": 100,
        "periph_reset_pin": None,

        # Audio — TLV320DAC3100 via Fruit Jam Peripherals, now that the I2C
        # pull-ups are fitted (see note 3 above). Levels match FRUITJAM_V2;
        # periph_reset_pin stays None here (the clone has no PERIPH_RESET net
        # and Peripherals() brings the DAC up without it).
        "sound_system": "FRUITJAM_DAC",
        "codec_sample_rate": 22050,
        "volume": 80,
        "playback_speed": 100,
        "dac_volume": -10,       # dB
        "speaker_volume": 0,     # dB
        "speaker_gain": 24,      # dB
        # Auto-route on plug/unplug: the TLV320 reports jack state and
        # AudioPlayer.poll_headset_detect() switches between the onboard
        # speakers and the 3.5 mm jack. audio_output_default is only the
        # starting route, used until the first poll settles.
        "headset_detect_enabled": True,
        # Poll fast, settle slow. The jack detector chatters hard while a
        # plug moves — measured 3/0/1/0/3/0/1/0 across four seconds on one
        # insertion — so the debounce window has to span many samples, not
        # two. At 0.1 s a 1 s settle needs ten consecutive agreeing reads;
        # at the old 0.5 s it needed two, and rarely got them.
        "headset_poll_interval": 0.1,    # s between jack reads
        "headset_debounce": 1.0,         # s a reading must hold to count
        "audio_output_default": "headphone",
        "headphone_volume": 0,           # dB
        "headphone_left_gain": 9,        # dB
        "headphone_right_gain": 9,       # dB
        # I2S pins not used directly — Peripherals handles them
        "i2s_bclk": None,
        "i2s_ws": None,
        "i2s_dout": None,
        "i2s_mclk": None,
        "amp_en_pin": None,
        "amp_en_active_low": False,

        # I2C — pull-ups now fitted; the DAC answers at 0x18. Peripherals()
        # opens the bus itself via board.I2C(), so these are declarative.
        "i2c_scl": "SCL",
        "i2c_sda": "SDA",

        "sd_card": False,
        "sd_cs": None,
        "sd_sclk": None,
        "sd_mosi": None,
        "sd_miso": None,
        "sd_shares_display_spi": False,

        "touch_screen": False,

        # Encoder-only input; no USB HID keyboard, no seesaw expander.
        "input_type": None,
        "max_buttons": 0,
        "direct_button_pins": [],
        "direct_buttons_active_low": True,
        "seesaw_buttons": False,

        # Rotary encoder — A/B as on FRUITJAM_V2; button on BUTTON1/GPIO0
        # rather than V2's D10, which this board uses for the rail (note 2).
        "rotary_encoder": True,
        "encoder_navigation": True,
        "encoder_pin_a": "D8",
        "encoder_pin_b": "D9",
        "encoder_button_pin": "BUTTON1",   # = GPIO0 (see note 2)
        "encoder_button_index": 0,

        "wake_button_pin": None,
        "wake_button_index": 0,
        "neopixel_pin": None,
        "neopixel_count": 0,

        # 3x2 = 6 cells, matching base_fruitjam.menu and the 160x128 assets.
        "button_cols": 3,
        "button_rows": 2,
        "debounce_time": 0.05,

        # Emergency push/hold — live now that audio works and the encoder
        # button resolves to BUTTON1. Both route through encoder_button_pin.
        "emergency_push_enabled": True,
        "emergency_push_sound": "/button_sounds/emergency.mp3",
        "emergency_hold_enabled": True,
        "emergency_hold_seconds": 3,

        "sleep_enabled": False,
        "sleep_timeout": 120,
        "sleep_mode": "software_idle",
        # Rotary encoder button (BUTTON1 = GPIO0); rotation also wakes.
        # The planned MSPM0 input companion joins this list — wire its line
        # active-low open-drain, which is what the poll expects.
        "sleep_wake_pins": ["BUTTON1"],
        # The D10 rail feeds the encoder and its button, so sleep must not
        # cut it — doing so removes the only thing that can wake the board.
        "full_power_feeds_inputs": True,

        "language_switcher_enabled": False,
    },

    "FRUITJAM_CLONE_18_SILENT": {
        "name": "FRUITJAM_CLONE_18_SILENT",
        # Fruit Jam *clone* (bench unit UID 62AB3604F4D0B8E6, CircuitPython
        # 10.2.1). Same ZJY180SN00 1.8" panel and encoder as FRUITJAM_V2, but
        # the board differs in three ways that all force config changes:
        #
        #   1. The auxiliary 3V3 rail (screen + other optional devices) is
        #      gated by an ACTIVE-LOW-enable load switch on GPIO10 (=board.D10)
        #      with an external pull-up (new board rev): drive D10 LOW to enable
        #      the rail, RELEASE D10 to high-Z to disable it (the pull-up floats
        #      the enable off). Same polarity as FRUITJAM_V2's active-low
        #      FULL_POWER (on A4); only the pin differs. (An earlier rev of this
        #      board used an active-HIGH TPS22917 here; the design inverted it.)
        #   2. That steals D10, which FRUITJAM_V2 uses as the encoder button.
        #      The clone's encoder button is instead wired to BUTTON1 (= GPIO0,
        #      verified on the bench 2026-09-18). Peripherals() claims BUTTON1
        #      as one of its three buttons, but machine._init_fruitjam_
        #      peripherals() deinits those right after init, so InputManager
        #      can claim it. Rotation stays on D8/D9.
        #   3. The I2C pull-ups are NOT fitted on this unit. SDA/SCL read
        #      high only from the MCU's internal pulls, busio.I2C() raises
        #      "No pull up found", and the resulting Peripherals() failure is
        #      a hard CORE crash -> safe mode (GC_ALLOC_OUTSIDE_VM), not a
        #      Python exception, so machine.py's try/except cannot catch it.
        #      The only safe course is to never open the bus: audio off, I2C
        #      pins None. Display, menus and the encoder all still work.
        #
        #      This is FRUITJAM_CLONE_18 minus audio. Fit the pull-ups and
        #      switch config.txt to FRUITJAM_CLONE_18 to get sound; nothing
        #      else about the board differs.
        #      Bench unit UID 21F5C34F3D14325B, confirmed 2026-09-18.
        #      See documents/tps22917_load_switch_processed.md.

        # Display — identical panel + wiring to FRUITJAM_V2.
        "display_type": "ST7735R",
        "screen_width": 160,
        "screen_height": 128,
        "display_rotation": 90,
        "display_inverted": False,
        "background_image": None,
        "start_menu": "base_fruitjam.menu",
        "lcd_cs": "A3",
        "lcd_dc": "A2",
        "lcd_sclk": "SCK",
        "lcd_mosi": "MOSI",
        "lcd_miso": "MISO",
        "lcd_backlight": None,
        "lcd_reset": "A1",
        "st7735_colstart": 2,
        "st7735_rowstart": 1,
        "st7735_bgr": True,
        "spi_baudrate": 24_000_000,

        # Rail enable — ACTIVE LOW (new board rev): drive D10 LOW to power the
        # screen + optional devices; RELEASE the pin (high-Z) to cut the rail,
        # where an external pull-up holds the load switch off.
        "full_power_pin": "D10",
        "full_power_active_low": True,
        "full_power_off_release": True,   # disable by releasing, not driving high
        "full_power_settle_ms": 100,
        "periph_reset_pin": None,

        # Audio — OFF. See the header note: without pull-ups the DAC is
        # unreachable and Peripherals() takes the board into safe mode.
        "sound_system": "NONE",
        "codec_sample_rate": 22050,
        "volume": 80,
        "playback_speed": 100,
        "dac_volume": -10,       # dB
        "speaker_volume": 0,     # dB
        "speaker_gain": 24,      # dB
        # Headset auto-detect is off here, so pin the route to the jack —
        # without this AudioPlayer falls back to "speaker".
        "audio_output_default": "headphone",
        "headphone_volume": 0,           # dB
        "headphone_left_gain": 9,        # dB
        "headphone_right_gain": 9,       # dB
        # I2S pins not used directly — Peripherals handles them
        "i2s_bclk": None,
        "i2s_ws": None,
        "i2s_dout": None,
        "i2s_mclk": None,
        "amp_en_pin": None,
        "amp_en_active_low": False,

        # I2C — nothing may open this bus on an unfitted board.
        "i2c_scl": None,
        "i2c_sda": None,

        "sd_card": False,
        "sd_cs": None,
        "sd_sclk": None,
        "sd_mosi": None,
        "sd_miso": None,
        "sd_shares_display_spi": False,

        "touch_screen": False,

        # Encoder-only input; no USB HID keyboard, no seesaw expander.
        "input_type": None,
        "max_buttons": 0,
        "direct_button_pins": [],
        "direct_buttons_active_low": True,
        "seesaw_buttons": False,

        # Rotary encoder — A/B as on FRUITJAM_V2; button on BUTTON1/GPIO0
        # rather than V2's D10, which this board uses for the rail (note 2).
        "rotary_encoder": True,
        "encoder_navigation": True,
        "encoder_pin_a": "D8",
        "encoder_pin_b": "D9",
        "encoder_button_pin": "BUTTON1",   # = GPIO0 (see note 2)
        "encoder_button_index": 0,

        "wake_button_pin": None,
        "wake_button_index": 0,
        "neopixel_pin": None,
        "neopixel_count": 0,

        # 3x2 = 6 cells, matching base_fruitjam.menu and the 160x128 assets.
        "button_cols": 3,
        "button_rows": 2,
        "debounce_time": 0.05,

        # Emergency push/hold — live now that audio works and the encoder
        # button resolves to BUTTON1. Both route through encoder_button_pin.
        "emergency_push_enabled": False,
        "emergency_hold_enabled": False,

        "sleep_enabled": False,
        "sleep_timeout": 120,
        "sleep_mode": "software_idle",
        # Same board as FRUITJAM_CLONE_18, so the same sleep rules.
        "sleep_wake_pins": ["BUTTON1"],
        "full_power_feeds_inputs": True,

        "language_switcher_enabled": False,
    },


    "FRUITJAM_CLONE_18_A4": {
        "name": "FRUITJAM_CLONE_18_A4",
        # Fruit Jam *clone*, second board revision (bench unit UID
        # 21F5C34F3D14325B). Same 1.8" ST7735R panel, same encoder, same
        # TLV320 audio as FRUITJAM_CLONE_18 — but the panel rail is gated on
        # A4, the way a genuine Fruit Jam does it, NOT on D10.
        #
        # Bench-verified 2026-09-19 by driving each pin in turn and reading
        # the label the panel showed: it lights with A4 low and stays dark
        # with only D10 low. Running FRUITJAM_CLONE_18 on this board leaves
        # A4 floating, and its external pull-up then holds the rail OFF, so
        # the screen never lights — which looks exactly like a dead backlight.
        #
        # The encoder button is still BUTTON1 (= GPIO0), not FRUITJAM_V2's
        # D10, so this is neither variant unmodified. D10 is unused here.
        #
        # Identify by UID, not by CIRCUITPY label: the labels move between
        # sessions and these boards are otherwise indistinguishable.
        # Display — identical panel + wiring to FRUITJAM_V2.
        "display_type": "ST7735R",
        "screen_width": 160,
        "screen_height": 128,
        "display_rotation": 90,
        "display_inverted": False,
        "background_image": None,
        "start_menu": "base_fruitjam.menu",
        "lcd_cs": "A3",
        "lcd_dc": "A2",
        "lcd_sclk": "SCK",
        "lcd_mosi": "MOSI",
        "lcd_miso": "MISO",
        # D10 is a separate, active-high BACKLIGHT enable on this board --
        # independent of the A4 panel rail, verified by holding A4 low and
        # toggling D10 alone (the backlight blinked while the image stayed).
        # Note the trap: FRUITJAM_CLONE_18 uses D10 as its *panel rail*.
        # Same pin, opposite job, two board revisions.
        "lcd_backlight": "D10",
        "lcd_reset": "A1",
        "st7735_colstart": 2,
        "st7735_rowstart": 1,
        "st7735_bgr": True,
        "spi_baudrate": 24_000_000,

        # Rail enable — ACTIVE LOW (new board rev): drive D10 LOW to power the
        # screen + optional devices; RELEASE the pin (high-Z) to cut the rail,
        # where an external pull-up holds the load switch off.
        "full_power_pin": "A4",
        "full_power_active_low": True,
        "full_power_off_release": True,   # disable by releasing, not driving high
        "full_power_settle_ms": 100,
        "periph_reset_pin": None,

        # Audio — OFF. See the header note: without pull-ups the DAC is
        # unreachable and Peripherals() takes the board into safe mode.
        "sound_system": "FRUITJAM_DAC",
        "codec_sample_rate": 22050,
        "volume": 80,
        "playback_speed": 100,
        "dac_volume": -10,       # dB
        "speaker_volume": 0,     # dB
        "speaker_gain": 24,      # dB
        # Headset auto-detect is off here, so pin the route to the jack —
        # without this AudioPlayer falls back to "speaker".
        # Same jack auto-routing as FRUITJAM_CLONE_18: poll fast,
        # settle slow — the detector chatters while a plug moves.
        "headset_detect_enabled": True,
        "headset_poll_interval": 0.1,
        "headset_debounce": 1.0,
        "audio_output_default": "headphone",
        "headphone_volume": 0,           # dB
        "headphone_left_gain": 9,        # dB
        "headphone_right_gain": 9,       # dB
        # I2S pins not used directly — Peripherals handles them
        "i2s_bclk": None,
        "i2s_ws": None,
        "i2s_dout": None,
        "i2s_mclk": None,
        "amp_en_pin": None,
        "amp_en_active_low": False,

        # I2C — nothing may open this bus on an unfitted board.
        "i2c_scl": "SCL",
        "i2c_sda": "SDA",

        "sd_card": False,
        "sd_cs": None,
        "sd_sclk": None,
        "sd_mosi": None,
        "sd_miso": None,
        "sd_shares_display_spi": False,

        "touch_screen": False,

        # Encoder-only input; no USB HID keyboard, no seesaw expander.
        "input_type": None,
        "max_buttons": 0,
        "direct_button_pins": [],
        "direct_buttons_active_low": True,
        "seesaw_buttons": False,

        # Rotary encoder — A/B as on FRUITJAM_V2; button on BUTTON1/GPIO0
        # rather than V2's D10, which this board uses for the rail (note 2).
        "rotary_encoder": True,
        "encoder_navigation": True,
        "encoder_pin_a": "D8",
        "encoder_pin_b": "D9",
        "encoder_button_pin": "BUTTON1",   # = GPIO0 (see note 2)
        "encoder_button_index": 0,

        "wake_button_pin": None,
        "wake_button_index": 0,
        "neopixel_pin": None,
        "neopixel_count": 0,

        # 3x2 = 6 cells, matching base_fruitjam.menu and the 160x128 assets.
        "button_cols": 3,
        "button_rows": 2,
        "debounce_time": 0.05,

        # Emergency push/hold — live now that audio works and the encoder
        # button resolves to BUTTON1. Both route through encoder_button_pin.
        "emergency_push_enabled": False,
        "emergency_hold_enabled": False,

        "sleep_enabled": False,
        "sleep_timeout": 120,
        "sleep_mode": "software_idle",
        "sleep_wake_pins": ["BUTTON1"],
        # The A4 rail powers the panel and nothing re-initialises the display
        # after a power cut, so sleep leaves it up. That costs nothing now:
        # the backlight is on its own pin, so sleep darkens the screen by
        # switching D10 rather than by pulling the panel's power.
        "full_power_feeds_display": True,

        "language_switcher_enabled": False,
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
        "speaker_gain": 24,         # max analog speaker amp gain
        "headphone_volume": 0,      # max analog headphone volume
        "headphone_left_gain": 9,   # max analog HP amp gain (chip cap)
        "headphone_right_gain": 9,  # max analog HP amp gain (chip cap)
        # 3.5 mm jack auto-detect: speaker by default, swap to headphone
        # when something is plugged in. AudioPlayer polls the codec's
        # headset_status from the main loop.
        "headset_detect_enabled": True,
        "headset_poll_interval": 0.5,
        "headset_debounce": 1.0,
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

    "FRUITJAM_DVI_ENC": {
        "name": "FRUITJAM_DVI_ENC",

        # Display — onboard DVI/HDMI output, 320x240 fb -> 640x480 HDMI.
        # See FRUITJAM_DVI_KBD for the bring-up sequence rationale.
        "display_type": "FRUITJAM_DVI",
        "screen_width": 320,
        "screen_height": 240,
        "framebuffer_pixel_scale": 2,
        "framebuffer_color_depth": 16,
        "display_rotation": 0,
        "display_inverted": False,
        "background_image": "/menus/images/needs_small.bmp",
        "start_menu": "base_moana.menu",
        "lcd_cs": None,
        "lcd_dc": None,
        "lcd_sclk": None,
        "lcd_mosi": None,
        "lcd_miso": None,
        "lcd_backlight": None,
        "lcd_reset": None,

        # Audio — TLV320DAC3100 via Fruit Jam Peripherals.
        "sound_system": "FRUITJAM_DAC",
        "codec_sample_rate": 22050,
        "volume": 80,
        "dac_volume": -10,
        "speaker_volume": 0,
        "speaker_gain": 24,
        "headphone_volume": 0,
        "headphone_left_gain": 9,
        "headphone_right_gain": 9,
        "headset_detect_enabled": True,
        "headset_poll_interval": 0.5,
        "headset_debounce": 1.0,
        "i2s_bclk": None,
        "i2s_ws": None,
        "i2s_dout": None,
        "i2s_mclk": None,
        "amp_en_pin": None,
        "amp_en_active_low": False,

        "full_power_pin": None,
        "full_power_active_low": False,
        "full_power_settle_ms": 0,
        "periph_reset_pin": "PERIPH_RESET",

        # SD card — enabled, content overrides flash.
        "sd_card": True,
        "sd_cs": "SD_CS",
        "sd_sclk": "SD_SCK",
        "sd_mosi": "SD_MOSI",
        "sd_miso": "SD_MISO",
        "sd_shares_display_spi": False,

        "i2c_scl": "SCL",
        "i2c_sda": "SDA",
        "i2c_freq": 400_000,

        "touch_screen": False,

        # USB HID keyboard kept for digit-key cell selection (1..8).
        "input_type": "USB_HID_KEYBOARD",
        "usb_host_dp": "USB_HOST_DATA_PLUS",
        "usb_host_dm": "USB_HOST_DATA_MINUS",
        "usb_host_5v_power": "USB_HOST_5V_POWER",

        # Direct buttons OFF — BUTTON1/BUTTON2/BUTTON3 GPIOs are repurposed
        # as the rotary encoder. Same physical hardware, different reading
        # mode: BUTTON1 = encoder A, BUTTON2 = encoder B, BUTTON3 = click.
        "max_buttons": 0,
        "direct_button_pins": [],
        "direct_buttons_active_low": True,

        # Rotary encoder — drives the language switcher overlay. Encoder
        # navigation is FALSE so rotation doesn't move a menu highlight
        # (we want it to open the language picker instead).
        "rotary_encoder": True,
        "encoder_navigation": False,
        "encoder_pin_a": "BUTTON1",
        "encoder_pin_b": "BUTTON2",
        "encoder_button_pin": "BUTTON3",
        "encoder_button_index": 0,

        "wake_button_pin": None,
        "wake_button_index": 0,

        # Peripherals already owns the onboard 5-pixel strip — leave None
        # so Machine doesn't try to re-claim board.NEOPIXEL.
        "neopixel_pin": None,
        "neopixel_count": 0,

        # 4x2 = 8 cells, mapped 1:1 to keypad keys 1..8.
        "button_cols": 4,
        "button_rows": 2,
        "debounce_time": 0.05,

        # Sleep — software idle (RP2350B has no alarm module).
        "sleep_enabled": False,
        "sleep_timeout": 120,
        "sleep_mode": "software_idle",
        "sleep_wake_pins": [],

        # Multi-lingual: matches the CYD_PLUS asset layout the subprogram
        # already expects (/lang_images/lang_<code>.bmp, /menus/lang_<code>.menu,
        # /button_sounds/languages/<code>/*.wav).
        "language_switcher_enabled": True,
    },

    "FRUITJAM_LCD_28": {
        "name": "FRUITJAM_LCD_28",

        # Display — 2.8" 320x240 ILI9341 SPI on the Fruit Jam daughterboard.
        # Same daughterboard socket pinout as FRUITJAM_V2 (which used the
        # 1.77" ST7735R) — only the controller and resolution differ.
        "display_type": "ILI9341",
        "screen_width": 320,
        "screen_height": 240,
        "display_rotation": 0,            # flip if image is upside-down
        "display_inverted": False,        # set True if IPS panel (colors inverted)
        "background_image": None,         # menu provides background
        "start_menu": "base_moana.menu",
        "lcd_cs": "A3",
        "lcd_dc": "A2",
        "lcd_sclk": "SCK",
        "lcd_mosi": "MOSI",
        "lcd_miso": "MISO",
        "lcd_backlight": None,            # backlight on 3V3_SWITCHED rail
        "lcd_reset": "A1",
        "spi_baudrate": 24_000_000,

        # Audio — TLV320DAC3100 via Fruit Jam Peripherals.
        "sound_system": "FRUITJAM_DAC",
        "codec_sample_rate": 22050,
        "volume": 80,
        "dac_volume": -10,
        "speaker_volume": 0,
        "speaker_gain": 24,
        "headphone_volume": 0,
        "headphone_left_gain": 9,
        "headphone_right_gain": 9,
        "headset_detect_enabled": True,
        "headset_poll_interval": 0.5,
        "headset_debounce": 1.0,
        "i2s_bclk": None,
        "i2s_ws": None,
        "i2s_dout": None,
        "i2s_mclk": None,
        "amp_en_pin": None,
        "amp_en_active_low": False,

        # FULL_POWER — gates 3V3_SWITCHED rail (LCD VCC, IOVCC, backlight).
        # Active low: LOW = power on, HIGH = power off. Same as FRUITJAM_V2.
        "full_power_pin": None,  # disabled: FULL_POWER hardwired via pull-down (was "A4")
        "full_power_active_low": True,
        "full_power_settle_ms": 100,
        # Hold A4 (FULL_POWER / seesaw BUTTON1 net) as an input with pull-up.
        "input_pullup_pins": ["A4"],
        # MSPM0 Seesaw button expander on the I2C bus: buttons 0..7 drive menu
        # selections 0..7 when present (auto-skipped if not powered/found).
        "seesaw_buttons": True,

        # Peripherals reset — must be HIGH for DAC operation.
        "periph_reset_pin": "PERIPH_RESET",

        # SD card — daughterboard doesn't expose one.
        "sd_card": False,
        "sd_cs": None,
        "sd_sclk": None,
        "sd_mosi": None,
        "sd_miso": None,
        "sd_shares_display_spi": False,

        # I2C (DAC + headset detect).
        "i2c_scl": "SCL",
        "i2c_sda": "SDA",
        "i2c_freq": 400_000,

        # No touch screen on this build.
        "touch_screen": False,

        # USB HID keyboard via the Fruit Jam USB host port.
        # Requires /boot.py with usb_host.Port().
        "input_type": "USB_HID_KEYBOARD",
        "usb_host_dp": "USB_HOST_DATA_PLUS",
        "usb_host_dm": "USB_HOST_DATA_MINUS",
        "usb_host_5v_power": "USB_HOST_5V_POWER",

        # Onboard tactile buttons — daughterboard doesn't route them.
        "max_buttons": 0,
        "direct_button_pins": [],
        "direct_buttons_active_low": True,

        # Rotary encoder on the daughterboard at D8/D9/D10 (same as FRUITJAM_V2).
        "rotary_encoder": True,
        "encoder_navigation": True,
        "encoder_pin_a": "D8",
        "encoder_pin_b": "D9",
        "encoder_button_pin": "D10",
        "encoder_button_index": 0,

        "wake_button_pin": None,
        "wake_button_index": 0,

        # NeoPixel — Peripherals owns the onboard strip; leave None so
        # Machine doesn't try to re-claim board.NEOPIXEL.
        "neopixel_pin": None,
        "neopixel_count": 0,

        # 4x2 = 8 cells, mapped 1:1 to keypad keys 1..8.
        "button_cols": 4,
        "button_rows": 2,
        "debounce_time": 0.05,

        # Sleep — software idle (RP2350B has no alarm module).
        "sleep_enabled": False,
        "sleep_timeout": 120,
        "sleep_mode": "software_idle",
        "sleep_wake_pins": [],

        "language_switcher_enabled": True,
    },

    "PI_BLINKA": {
        "name": "PI_BLINKA",
        # Linux/Blinka target: Raspberry Pi 4 / 400 / Zero 2 W under Raspberry
        # Pi OS. Runs on CPython3 (not the CircuitPython VM). machine.py swaps in
        # the pi_blinka/ audio + input backends for platform=blinka; the display
        # uses the BLINKA_PYGAME branch in display_manager.py.
        "platform": "blinka",

        # Display — HDMI via PyGameDisplay. App draws at LOGICAL 320x240 and
        # reuses the existing 320x240 menus/assets; platform_detect.py picks the
        # physical HDMI mode (Pi 4/400/Zero 2 W -> 1280x720 x3 -> 960x720
        # pillarbox). Set hdmi_width/height/framebuffer_pixel_scale to override.
        "display_type": "BLINKA_PYGAME",
        "screen_width": 320,
        "screen_height": 240,
        "auto_profile": True,
        "blinka_fullscreen": True,
        # Mirror the UI to a second HDMI monitor when one is connected at
        # startup; falls back to single-display automatically when absent.
        "mirror_display": True,
        "display_rotation": 0,
        "display_inverted": False,
        "background_image": None,        # menu provides background (avoid direct load)
        "start_menu": "base_moana.menu",

        # fs_base — absolute repo root, injected at runtime by pi_blinka/run_app.py
        # so the app's "/menus", "/button_sounds" paths resolve under Linux.
        "fs_base": None,

        # Audio — Blinka backend (ALSA via pygame.mixer). Marker only; machine.py
        # selects BlinkaAudioPlayer for platform=blinka.
        "sound_system": "BLINKA_AUDIO",
        "codec_sample_rate": 22050,
        "volume": 80,
        "playback_speed": 100,

        # Input — two USB keyboards merged via Linux evdev. machine.py selects
        # EvdevKeyboardInput for platform=blinka.
        "input_type": "EVDEV_KEYBOARD",
        "evdev_grab": False,             # True to stop the console seeing keys

        # No SPI display / SD / I2C / codec / encoder / touch / NeoPixel here —
        # keep these off so the CircuitPython-only init paths are skipped.
        "lcd_cs": None, "lcd_dc": None, "lcd_sclk": None, "lcd_mosi": None,
        "lcd_miso": None, "lcd_backlight": None, "lcd_reset": None,
        "sd_card": False,
        "i2c_scl": None, "i2c_sda": None,
        "touch_screen": False,
        "rotary_encoder": False,
        "max_buttons": 0,
        "direct_button_pins": [],
        "seesaw_buttons": False,
        "neopixel_pin": None,
        "full_power_pin": None,
        "wake_button_pin": None,

        # Button grid — 4x2 = 8 cells (matches base_moana.menu).
        "button_cols": 4,
        "button_rows": 2,
        "debounce_time": 0.05,

        # Emergency + sleep off (no GPIO emergency button; Linux doesn't sleep
        # the CircuitPython way).
        "emergency_push_enabled": False,
        "emergency_hold_enabled": False,
        "sleep_enabled": False,
        "sleep_timeout": 120,
        "sleep_mode": "software_idle",
        "sleep_wake_pins": [],

        "language_switcher_enabled": False,
    },
}

# Change this single line to switch machine variant.
# Fruit Jam daughterboard builds share a socket, so pick by fitted panel:
#   FRUITJAM_V2      -> 1.8" ST7735 (ZJY180SN00), 160x128, 3x2 grid
#   FRUITJAM_LCD_28  -> 2.8" ILI9341, 320x240, 4x2 grid (+ MSPM0 seesaw)
DEFAULT_VARIANT = "FRUITJAM_V2"

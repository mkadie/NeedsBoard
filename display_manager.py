"""Display management for AAC device.

Handles display initialization, background image loading,
and screen-coordinate-to-button-grid mapping.
"""

import displayio
import fourwire
import busio
import board


def _pin(name):
    """Resolve pin name string to board pin. Returns None if name is None."""
    if name is None:
        return None
    return getattr(board, name)


class DisplayManager:
    """Manages display hardware, background images, and button grid geometry.

    Supports SPI color displays (ILI9341, ST7735R) and I2C OLED (SSD1306).
    Text-mode displays show text_description instead of images.
    """

    def __init__(self, config, spi=None):
        """Initialize display hardware from config dict.

        Args:
            config: Hardware config dictionary.
            spi: Optional shared SPI bus (e.g., from StorageManager when
                 SD card shares the display SPI bus). If None, creates its own.
        """
        self._config = config
        self._width = config["screen_width"]
        self._height = config["screen_height"]
        self._cols = config["button_cols"]
        self._rows = config["button_rows"]
        self._zone_width = self._width // self._cols
        self._zone_height = self._height // self._rows
        self._text_mode = config.get("display_text_mode", False)
        self._text_area = None
        self._text_lines = []

        displayio.release_displays()

        display_type = config.get("display_type", "ILI9341")

        if display_type == "SSD1306":
            self._init_ssd1306(config)
        else:
            self._init_spi_display(config, spi)

        # Display group
        self._splash = displayio.Group()
        self._display.root_group = self._splash

        if self._text_mode:
            self._init_text_display()
        else:
            bg = config.get("background_image")
            if bg:
                try:
                    self._load_background(bg)
                except Exception as e:
                    print("Initial background skipped:", e)

        # Selection highlight overlay
        self._highlight = None
        self._highlight_index = -1

    def _init_ssd1306(self, config):
        """Initialize SSD1306 OLED via I2C."""
        from i2cdisplaybus import I2CDisplayBus
        import adafruit_displayio_ssd1306

        i2c = busio.I2C(_pin(config["i2c_scl"]), _pin(config["i2c_sda"]))
        display_bus = I2CDisplayBus(i2c, device_address=0x3C)
        self._display = adafruit_displayio_ssd1306.SSD1306(
            display_bus,
            width=self._width,
            height=self._height,
            rotation=config.get("display_rotation", 0),
        )

    def _init_spi_display(self, config, spi):
        """Initialize SPI color display (ILI9341 or ST7735R)."""
        # SPI bus — use shared bus if provided, otherwise create one
        if spi is not None:
            self._spi = spi
        else:
            spi_kwargs = {"MOSI": _pin(config["lcd_mosi"])}
            miso = _pin(config.get("lcd_miso"))
            if miso:
                spi_kwargs["MISO"] = miso
            self._spi = busio.SPI(_pin(config["lcd_sclk"]), **spi_kwargs)

        # FourWire display bus
        fw_kwargs = {
            "command": _pin(config["lcd_dc"]),
            "chip_select": _pin(config["lcd_cs"]),
        }
        reset = _pin(config.get("lcd_reset"))
        if reset:
            fw_kwargs["reset"] = reset
        baudrate = config.get("spi_baudrate")
        if baudrate:
            fw_kwargs["baudrate"] = baudrate
        self._display_bus = fourwire.FourWire(self._spi, **fw_kwargs)

        # Display driver — select by type
        display_type = config.get("display_type", "ILI9341")

        if display_type == "ST7735R":
            from adafruit_st7735r import ST7735R
            self._display = ST7735R(
                self._display_bus,
                width=self._width,
                height=self._height,
                colstart=config.get("st7735_colstart", 0),
                rowstart=config.get("st7735_rowstart", 0),
                rotation=config["display_rotation"],
                bgr=config.get("st7735_bgr", False),
            )
        else:
            import adafruit_ili9341
            self._display = adafruit_ili9341.ILI9341(
                self._display_bus,
                width=self._width,
                height=self._height,
                rotation=config["display_rotation"],
            )

        # Fix color inversion for IPS panels
        if config.get("display_inverted", False):
            self._display_bus.send(0x21, b"")

        # Backlight
        self._backlight = None
        bl_pin = _pin(config.get("lcd_backlight"))
        if bl_pin:
            import digitalio
            self._backlight = digitalio.DigitalInOut(bl_pin)
            self._backlight.direction = digitalio.Direction.OUTPUT
            self._backlight.value = True

    def _init_text_display(self):
        """Set up text-mode display (OLED).

        Two modes controlled by show_border config:
          True:  White border, single centered line (V1 style)
          False: 3-line list — prev (dim), current (inverted), next (dim)
        """
        import terminalio
        from adafruit_display_text import label

        self._show_border = self._config.get("show_border", True)
        self._text_lines = []

        if self._show_border:
            # --- Single-line bordered mode ---
            border = 5
            bg = displayio.Bitmap(self._width, self._height, 1)
            bg_pal = displayio.Palette(1)
            bg_pal[0] = 0xFFFFFF
            self._splash.append(displayio.TileGrid(bg, pixel_shader=bg_pal))

            inner = displayio.Bitmap(
                self._width - border * 2, self._height - border * 2, 1)
            inner_pal = displayio.Palette(1)
            inner_pal[0] = 0x000000
            self._splash.append(displayio.TileGrid(
                inner, pixel_shader=inner_pal, x=border, y=border))

            self._text_area = label.Label(
                terminalio.FONT,
                text="Ready",
                color=0xFFFFFF,
                x=10,
                y=self._height // 2 - 1,
            )
            self._splash.append(self._text_area)
        else:
            # --- 3-line scrolling list mode ---
            # Black background
            bg = displayio.Bitmap(self._width, self._height, 1)
            bg_pal = displayio.Palette(1)
            bg_pal[0] = 0x000000
            self._splash.append(displayio.TileGrid(bg, pixel_shader=bg_pal))

            # Highlight bar behind middle line (white bar, black text)
            bar = displayio.Bitmap(self._width, 10, 1)
            bar_pal = displayio.Palette(1)
            bar_pal[0] = 0xFFFFFF
            self._splash.append(displayio.TileGrid(
                bar, pixel_shader=bar_pal, x=0, y=11))

            # 3 text lines at y=5, y=16, y=27
            for i, (y, color) in enumerate([
                (5, 0xFFFFFF),    # prev — white on black
                (16, 0x000000),   # current — black on white bar
                (27, 0xFFFFFF),   # next — white on black
            ]):
                line = label.Label(
                    terminalio.FONT,
                    text="",
                    color=color,
                    x=2,
                    y=y,
                )
                self._splash.append(line)
                self._text_lines.append(line)

    def set_text_lines(self, prev_text, current_text, next_text):
        """Update the 3-line text display or single-line display."""
        if self._text_lines:
            self._text_lines[0].text = prev_text
            self._text_lines[1].text = current_text
            self._text_lines[2].text = next_text
        elif self._text_area is not None:
            self._text_area.text = current_text

    def set_text(self, text):
        """Update text on any display.

        On 3-line OLED, updates the current (middle) line.
        On bordered OLED, updates the single text area.
        On color displays, creates a text overlay at the bottom.
        """
        if self._text_lines:
            self._text_lines[1].text = text
            return
        if self._text_area is None and not self._text_mode:
            # Create overlay for color screens — only if hint text enabled
            if not self._config.get("display_hint_text", True):
                return
            import terminalio
            from adafruit_display_text import label
            self._text_area = label.Label(
                terminalio.FONT,
                text="",
                color=0xFFFFFF,
                background_color=0x000000,
                x=2,
                y=self._height - 8,
            )
            self._splash.append(self._text_area)
        if self._text_area is not None:
            self._text_area.text = text

    def _load_background(self, image_path):
        """Load and display a BMP background image."""
        import gc
        print("Loading background:", image_path)
        # Clear existing content
        while len(self._splash):
            self._splash.pop()
        gc.collect()
        odb = displayio.OnDiskBitmap(image_path)
        face = displayio.TileGrid(odb, pixel_shader=odb.pixel_shader)
        self._splash.append(face)
        # Re-add highlight overlay if it existed
        if self._highlight is not None:
            self._splash.append(self._highlight)
        print("Background loaded")

    def set_background(self, image_path):
        """Swap the background image. No-op for text-mode displays."""
        if self._text_mode:
            return
        self._load_background(image_path)

    def _create_highlight(self):
        """Create a border-only highlight rectangle for cell selection."""
        w = self._zone_width
        h = self._zone_height
        border = max(2, min(w, h) // 16)

        bmp = displayio.Bitmap(w, h, 2)
        pal = displayio.Palette(2)
        pal[0] = 0x000000
        pal.make_transparent(0)
        pal[1] = 0xFFFF00  # Yellow highlight

        # Draw border only
        for x in range(w):
            for b in range(border):
                bmp[x, b] = 1
                bmp[x, h - 1 - b] = 1
        for y in range(h):
            for b in range(border):
                bmp[b, y] = 1
                bmp[w - 1 - b, y] = 1

        self._highlight = displayio.TileGrid(bmp, pixel_shader=pal, x=0, y=0)
        self._splash.append(self._highlight)

    def set_highlight(self, index):
        """Move the selection highlight to a grid cell by index.

        No-op for text-mode displays (text scrolling handles selection).
        Args:
            index: Grid cell index (0-based), or -1 to hide.
        """
        if self._text_mode:
            return
        if index == self._highlight_index:
            return

        if self._highlight is None:
            self._create_highlight()

        self._highlight_index = index

        if index < 0:
            self._highlight.hidden = True
            return

        col = index % self._cols
        row = index // self._cols
        self._highlight.x = col * self._zone_width
        self._highlight.y = row * self._zone_height
        self._highlight.hidden = False

    def get_button_from_screen(self, screen_x, screen_y):
        """Map screen coordinates to a button grid index.

        Returns:
            Button index (row * cols + col), 0-based.
        """
        col = min(screen_x // self._zone_width, self._cols - 1)
        row = min(screen_y // self._zone_height, self._rows - 1)
        return row * self._cols + col

    def set_backlight(self, on):
        """Turn the display backlight on or off."""
        if self._backlight:
            self._backlight.value = on

    @property
    def display(self):
        """The underlying displayio display object."""
        return self._display

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @property
    def zone_width(self):
        return self._zone_width

    @property
    def zone_height(self):
        return self._zone_height

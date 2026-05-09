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
    """Manages ILI9341 display, background image, and button grid geometry."""

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

        # Defaults; only the SPI display path populates these
        self._spi = None
        self._display_bus = None
        self._backlight = None

        displayio.release_displays()

        display_type = config.get("display_type", "ILI9341")
        if display_type == "FRUITJAM_DVI":
            self._init_fruitjam_dvi(config)
        else:
            self._init_spi_display(config, spi)

        # Display group — background loaded later by menu system or fallback
        self._splash = displayio.Group()
        self._display.root_group = self._splash
        bg = config.get("background_image")
        if bg:
            try:
                self._load_background(bg)
            except Exception as e:
                print("Initial background skipped:", e)

        # Selection highlight overlay
        self._highlight = None
        self._highlight_index = -1

    def _init_fruitjam_dvi(self, config):
        """Bring up the Fruit Jam onboard DVI/HDMI output.

        request_display_config() validates against the firmware's allowed
        sizes ({320,240}, {360,200}, {640,480}, {720,400}) and populates
        supervisor.runtime.display — board.DISPLAY does NOT exist on this
        firmware.
        """
        import supervisor
        from adafruit_fruitjam.peripherals import request_display_config
        request_display_config(self._width, self._height)
        self._display = supervisor.runtime.display
        scale = config.get("framebuffer_pixel_scale", 1)
        print("DVI ready: {}x{} fb -> {}x{} hdmi".format(
            self._width, self._height,
            self._width * scale, self._height * scale,
        ))

    def _init_spi_display(self, config, spi):
        """Bring up an SPI-attached panel (ILI9341 / ST7735R)."""
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
        bl_pin = _pin(config.get("lcd_backlight"))
        if bl_pin:
            import digitalio
            self._backlight = digitalio.DigitalInOut(bl_pin)
            self._backlight.direction = digitalio.Direction.OUTPUT
            self._backlight.value = True

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
        """Swap the background image (used when navigating between menus)."""
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

        Args:
            index: Grid cell index (0-based), or -1 to hide.
        """
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

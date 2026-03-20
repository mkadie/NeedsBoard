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

    def __init__(self, config):
        """Initialize display hardware from config dict.

        Args:
            config: Hardware config dictionary.
        """
        self._config = config
        self._width = config["screen_width"]
        self._height = config["screen_height"]
        self._cols = config["button_cols"]
        self._rows = config["button_rows"]
        self._zone_width = self._width // self._cols
        self._zone_height = self._height // self._rows

        displayio.release_displays()

        # SPI bus
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
        self._display_bus = fourwire.FourWire(self._spi, **fw_kwargs)

        # ILI9341 display
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

        # Display group and background image
        self._splash = displayio.Group()
        self._display.root_group = self._splash
        self._load_background(config["background_image"])

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
        print("Background loaded")

    def set_background(self, image_path):
        """Swap the background image (used when navigating between menus)."""
        self._load_background(image_path)

    def get_button_from_screen(self, screen_x, screen_y):
        """Map screen coordinates to a button grid index.

        Returns:
            Button index (row * cols + col), 0-based.
        """
        col = min(screen_x // self._zone_width, self._cols - 1)
        row = min(screen_y // self._zone_height, self._rows - 1)
        return row * self._cols + col

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

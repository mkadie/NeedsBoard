"""Display management for AAC device.

Handles display initialization, background image loading,
and screen-coordinate-to-button-grid mapping.
"""

import time
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
        elif display_type == "FRUITJAM_DVI":
            self._init_fruitjam_dvi(config)
        elif display_type == "BLINKA_PYGAME":
            self._init_blinka_pygame(config)
        else:
            self._init_spi_display(config, spi)

        # Display group
        self._splash = displayio.Group()
        self._display.root_group = self._splash

        # Built on first sleep — a full-screen black fill used to blank the
        # panel without touching the controller's sleep mode.
        self._blank_group = None

        # Selection highlight overlay
        self._highlight = None
        self._highlight_index = -1

        if self._text_mode:
            self._init_text_display()
        else:
            bg = config.get("background_image")
            if bg:
                try:
                    self._load_background(bg)
                except Exception as e:
                    print("Initial background skipped:", e)

    def _init_ssd1306(self, config):
        """Initialize SSD1306 OLED via I2C."""
        from i2cdisplaybus import I2CDisplayBus
        import adafruit_displayio_ssd1306

        i2c = busio.I2C(_pin(config["i2c_scl"]), _pin(config["i2c_sda"]))
        self._display_bus = I2CDisplayBus(i2c, device_address=0x3C)
        self._display = adafruit_displayio_ssd1306.SSD1306(
            self._display_bus,
            width=self._width,
            height=self._height,
            rotation=config.get("display_rotation", 0),
        )

    def _init_fruitjam_dvi(self, config):
        """Bring up the Fruit Jam onboard DVI/HDMI output.

        request_display_config() validates against the firmware's allowed
        sizes ({320,240}, {360,200}, {640,480}, {720,400}) and populates
        supervisor.runtime.display — board.DISPLAY does NOT exist on this
        firmware. Verified on Fruit Jam CP 10.0.3.
        """
        import supervisor
        from adafruit_fruitjam.peripherals import request_display_config
        request_display_config(self._width, self._height)
        self._spi = None
        self._display_bus = None
        self._backlight = None
        self._display = supervisor.runtime.display
        scale = config.get("framebuffer_pixel_scale", 1)
        print("DVI ready: %dx%d fb -> %dx%d hdmi" % (
            self._width, self._height,
            self._width * scale, self._height * scale))

    def _init_blinka_pygame(self, config):
        """Bring up an HDMI displayio surface on a Raspberry Pi via Blinka.

        Uses pi_blinka/display_backend.make_display(), which returns a
        LogicalDisplay: the app keeps drawing at logical screen_width x
        screen_height while the backend scales/pillarboxes to the physical HDMI
        mode (auto-detected per board). Only runs under Blinka (CPython3); the
        import is local so the CircuitPython targets never touch it.

        The caller (machine.py) must call display_backend.service() once per main
        loop to pump events + refresh — PyGame can't refresh from a thread.
        """
        import sys
        import os
        sys.path.insert(0, os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "pi_blinka"))
        from display_backend import make_display
        self._spi = None
        self._display_bus = None
        self._backlight = None
        self._display = make_display(config)

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
        """Update the 3-line text display, single-line, or hint overlay."""
        if self._text_lines:
            self._text_lines[0].text = prev_text
            self._text_lines[1].text = current_text
            self._text_lines[2].text = next_text
        else:
            # Delegate to set_text which handles lazy overlay creation
            self.set_text(current_text)

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
        gc.collect()
        odb = displayio.OnDiskBitmap(image_path)
        face = displayio.TileGrid(odb, pixel_shader=odb.pixel_shader)
        # Success — now clear and swap
        while len(self._splash):
            self._splash.pop()
        self._splash.append(face)
        # Re-add highlight overlay if it existed
        if self._highlight is not None:
            self._splash.append(self._highlight)
        # Re-add text overlay if it existed
        if self._text_area is not None:
            self._splash.append(self._text_area)
        # Store as the menu background for restore_background()
        self._menu_bg_face = face
        self._menu_bg_odb = odb  # Keep reference so GC doesn't free it
        print("Background loaded")

    def set_background(self, image_path):
        """Swap the background image. No-op for text-mode displays."""
        if self._text_mode:
            return
        self._load_background(image_path)

    def show_image(self, image_path):
        """Show a temporary full-screen image (zoom view).

        Call restore_background() to return to the menu background.
        """
        if self._text_mode:
            return
        import gc
        gc.collect()
        try:
            odb = displayio.OnDiskBitmap(image_path)
            face = displayio.TileGrid(odb, pixel_shader=odb.pixel_shader)
            while len(self._splash):
                self._splash.pop()
            self._splash.append(face)
            self._temp_odb = odb  # Keep reference
        except Exception as e:
            print("show_image error:", e)

    def restore_background(self):
        """Restore the menu background after a temporary image."""
        if self._text_mode:
            return
        if not hasattr(self, '_menu_bg_face') or self._menu_bg_face is None:
            return
        while len(self._splash):
            self._splash.pop()
        self._splash.append(self._menu_bg_face)
        if self._highlight is not None:
            self._splash.append(self._highlight)
        if self._text_area is not None:
            self._splash.append(self._text_area)
        # Free temp image
        self._temp_odb = None
        import gc
        gc.collect()

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

    def sleep_display(self):
        """Put display into low-power mode.

        SSD1306: DISPLAYOFF (0xAE) — drops to ~10uA
        ILI9341/ST7735R: DISPOFF (0x28) then SLPIN (0x10) — ~0.1mA

        The panel is blanked before sleeping it: SLPIN alone stops the
        booster while the driver still thinks it is displaying, which on
        the ST7735R leaves a fading ghost of the last frame.
        """
        if self._text_mode:
            if hasattr(self, '_display_bus'):
                try:
                    self._display_bus.send(0xAE, b"")  # SSD1306 DISPLAYOFF
                except:
                    pass
        else:
            # Colour panels blank through displayio, not SLPIN. Panel sleep
            # saves about 0.1 mA and costs a screen that does not come back:
            # SLPOUT is not guaranteed to preserve the controller's RAM, and
            # displayio then has no dirty region, so it sends nothing and the
            # panel stays black. Swapping the root group is pure displayio --
            # it always repaints -- and on boards with a real backlight pin
            # the saving comes from the backlight anyway.
            self._show_blank()
        self.set_backlight(False)

    def wake_display(self):
        """Wake display from low-power mode and put an image back on it.

        SSD1306: DISPLAYON (0xAF)
        ILI9341/ST7735R: SLPOUT (0x11) + 120ms settle + DISPON (0x29)

        Sleep-out is not enough on its own. The panel needs DISPON to
        re-enable output, its RAM is not guaranteed to survive the sleep,
        and displayio only pushes pixels it believes have changed — so
        without a forced redraw the screen comes back blank. The backlight
        is switched on last, so the panel is never lit while empty.
        """
        if self._text_mode:
            if hasattr(self, '_display_bus'):
                try:
                    self._display_bus.send(0xAF, b"")  # SSD1306 DISPLAYON
                except:
                    pass
        else:
            self.refresh()
        self.set_backlight(True)

    def rebuild(self):
        """Re-initialise the panel after it has lost power.

        Sleep can cut the rail that feeds the display, which leaves the
        controller unconfigured -- its registers and RAM are gone, and
        re-sending pixels to it achieves nothing. Building a fresh driver
        and re-attaching the existing groups brings the screen back without
        rebooting the board, which is what the old wake path resorted to.

        No-op on text-mode displays, which are not on a switched rail.
        """
        if self._text_mode or self._display is None:
            return False
        try:
            displayio.release_displays()
            time.sleep(0.1)
            # Hand back the existing SPI bus: it survives the rail cut (the
            # MCU pins never lost power), and re-claiming SCK/MOSI/MISO
            # would collide with the bus this object already holds.
            self._init_spi_display(self._config, self._spi)
            self._display.root_group = self._splash
            print("Display: rebuilt after power loss")
            return True
        except Exception as e:
            print("Display: rebuild failed:", type(e).__name__, e)
            return False

    def _show_blank(self):
        """Put a full-screen black bitmap up, so the panel reads as off."""
        if self._display is None:
            return
        if getattr(self, "_blank_group", None) is None:
            bmp = displayio.Bitmap(self._width, self._height, 1)
            pal = displayio.Palette(1)
            pal[0] = 0x000000
            self._blank_group = displayio.Group()
            self._blank_group.append(
                displayio.TileGrid(bmp, pixel_shader=pal))
        try:
            self._display.root_group = self._blank_group
        except Exception as e:
            print("Display: blank failed:", e)

    def refresh(self):
        """Put the real screen contents back and force a repaint.

        Re-attaching the root group is what marks the whole frame dirty;
        displayio otherwise believes nothing changed and sends nothing.
        """
        if self._display is None or self._splash is None:
            return
        try:
            self._display.root_group = self._splash
        except Exception as e:
            print("Display: refresh failed:", e)

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

"""Input management for AAC device.

Unified polling interface for touch screen, physical buttons,
rotary encoder, and wake button.
"""

import time
import digitalio
import board


def _pin(name):
    """Resolve pin name string to board pin. Returns None if name is None."""
    if name is None:
        return None
    return getattr(board, name)


class InputManager:
    """Polls all configured input sources and returns button presses."""

    def __init__(self, config, display_manager, i2c=None):
        """Initialize input hardware from config dict.

        Args:
            config: Hardware config dictionary.
            display_manager: DisplayManager instance (for touch-to-button mapping).
            i2c: Shared I2C bus (required for touch controller).
        """
        self._config = config
        self._display = display_manager
        self._debounce_time = config.get("debounce_time", 0.5)
        self._touch_time = time.monotonic()
        self._debug = True

        # Touch screen
        self._touch = None
        if config.get("touch_screen", False):
            self._init_touch(config, i2c)

        # Physical button decoder
        self._button_int = None
        self._button_data = []
        self._button_latch = None
        if config.get("max_buttons", 0) > 0:
            self._init_buttons(config)

        # Rotary encoder
        self._encoder = None
        self._encoder_button = None
        self._encoder_button_index = config.get("encoder_button_index", 8)
        self._last_encoder_button = True
        if config.get("rotary_encoder", False):
            self._init_encoder(config)

        # Wake button
        self._wake_button = None
        self._wake_button_index = config.get("wake_button_index", 8)
        self._last_wake = True
        if config.get("wake_button_pin"):
            pin = _pin(config["wake_button_pin"])
            self._wake_button = digitalio.DigitalInOut(pin)
            self._wake_button.direction = digitalio.Direction.INPUT
            self._wake_button.pull = digitalio.Pull.UP
            self._last_wake = self._wake_button.value

    def _init_touch(self, config, i2c):
        """Initialize capacitive touch controller."""
        # Reset touch controller
        rst_pin = _pin(config.get("touch_rst"))
        if rst_pin:
            rst = digitalio.DigitalInOut(rst_pin)
            rst.direction = digitalio.Direction.OUTPUT
            rst.value = False
            time.sleep(0.01)
            rst.value = True
            time.sleep(0.3)
            self._touch_rst = rst  # Keep reference to prevent GC

        import adafruit_focaltouch
        self._touch = adafruit_focaltouch.Adafruit_FocalTouch(i2c)

        # Touch coordinate remapping settings
        self._touch_swap_xy = config.get("touch_swap_xy", False)
        self._touch_flip_x = config.get("touch_flip_x", False)
        self._touch_flip_y = config.get("touch_flip_y", False)
        print("Touch controller ready")

    def _init_buttons(self, config):
        """Initialize hardware button decoder (3-bit binary + interrupt + latch)."""
        # Data pins (bit 0, 1, 2)
        for pin_name in config.get("button_data_pins", []):
            pin = digitalio.DigitalInOut(_pin(pin_name))
            pin.direction = digitalio.Direction.INPUT
            pin.pull = digitalio.Pull.DOWN
            self._button_data.append(pin)

        # Interrupt pin
        int_pin = _pin(config.get("button_int_pin"))
        if int_pin:
            self._button_int = digitalio.DigitalInOut(int_pin)
            self._button_int.direction = digitalio.Direction.INPUT
            self._button_int.pull = digitalio.Pull.DOWN

        # Latch reset pin
        latch_pin = _pin(config.get("button_latch_reset_pin"))
        if latch_pin:
            self._button_latch = digitalio.DigitalInOut(latch_pin)
            self._button_latch.direction = digitalio.Direction.OUTPUT
            self._button_latch.value = False

    def _init_encoder(self, config):
        """Initialize rotary encoder and its push button."""
        import rotaryio
        self._encoder = rotaryio.IncrementalEncoder(
            _pin(config["encoder_pin_a"]),
            _pin(config["encoder_pin_b"]),
        )
        btn_pin = _pin(config.get("encoder_button_pin"))
        if btn_pin:
            self._encoder_button = digitalio.DigitalInOut(btn_pin)
            self._encoder_button.direction = digitalio.Direction.INPUT
            self._encoder_button.pull = digitalio.Pull.UP
            self._last_encoder_button = self._encoder_button.value

    def poll(self):
        """Check all input sources for a button press.

        Returns:
            Button index (int) if pressed, or None.
        """
        # Wake button (checked every iteration, no debounce)
        result = self._check_wake()
        if result is not None:
            return result

        # Encoder button
        result = self._check_encoder()
        if result is not None:
            return result

        # Hardware button decoder
        result = self._check_buttons()
        if result is not None:
            return result

        # Touch screen (debounced)
        now = time.monotonic()
        if now - self._touch_time >= self._debounce_time:
            result = self._check_touch()
            if result is not None:
                self._touch_time = time.monotonic()
                return result

        return None

    def _check_touch(self):
        """Poll touch screen. Returns button index or None."""
        if self._touch is None:
            return None

        touches = self._touch.touches
        if not touches:
            return None

        point = touches[0]
        raw_x = point["x"]
        raw_y = point["y"]
        screen_x, screen_y = self._map_touch(raw_x, raw_y)
        button = self._display.get_button_from_screen(screen_x, screen_y)

        if self._debug:
            print(
                "Touch raw=({},{}) screen=({},{}) -> button {}".format(
                    raw_x, raw_y, screen_x, screen_y, button
                )
            )
        return button

    def _map_touch(self, raw_x, raw_y):
        """Remap touch coordinates to screen coordinates."""
        if self._touch_swap_xy:
            sx, sy = raw_y, raw_x
        else:
            sx, sy = raw_x, raw_y

        if self._touch_flip_x:
            sx = self._display.width - 1 - sx
        if self._touch_flip_y:
            sy = self._display.height - 1 - sy

        return sx, sy

    def _check_buttons(self):
        """Poll hardware button decoder. Returns button index or None."""
        if self._button_int is None:
            return None
        if not self._button_int.value:
            return None

        # Read binary-encoded button number
        button_number = 0
        for i, pin in enumerate(self._button_data):
            if pin.value:
                button_number |= 1 << i

        print("Button decoder:", button_number)

        # Reset latch
        if self._button_latch:
            self._button_latch.value = True
            time.sleep(0.1)
            self._button_latch.value = False

        return button_number

    def _check_encoder(self):
        """Poll rotary encoder button. Returns button index or None."""
        if self._encoder_button is None:
            return None

        current = self._encoder_button.value
        if current != self._last_encoder_button:
            self._last_encoder_button = current
            if not current:  # Active low
                return self._encoder_button_index
        return None

    def _check_wake(self):
        """Poll wake button. Returns button index or None."""
        if self._wake_button is None:
            return None

        current = self._wake_button.value
        if current != self._last_wake:
            self._last_wake = current
            if not current:  # Active low
                print("WAKE_UP_BUTTON pressed -> button", self._wake_button_index)
                return self._wake_button_index
        return None

    def deinit_for_sleep(self):
        """Release GPIO pins so alarm module can use them for wake."""
        if self._wake_button:
            self._wake_button.deinit()
            self._wake_button = None

    def reinit_after_sleep(self):
        """Reclaim GPIO pins after waking from light sleep."""
        config = self._config
        if config.get("wake_button_pin"):
            pin = _pin(config["wake_button_pin"])
            self._wake_button = digitalio.DigitalInOut(pin)
            self._wake_button.direction = digitalio.Direction.INPUT
            self._wake_button.pull = digitalio.Pull.UP
            self._last_wake = self._wake_button.value

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, value):
        self._debug = value

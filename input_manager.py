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
        self._i2c = i2c
        self._debounce_time = config.get("debounce_time", 0.5)
        self._last_press_time = 0  # Global debounce for ALL inputs
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

        # Direct GPIO buttons (individual pins, no decoder)
        self._direct_buttons = []
        self._direct_last = []
        if config.get("direct_button_pins"):
            self._init_direct_buttons(config)

        # Rotary encoder
        self._encoder = None
        self._encoder_button = None
        self._encoder_button_index = config.get("encoder_button_index", 8)
        self._last_encoder_button = True
        self._last_encoder_pos = 0
        # Encoder navigation: rotate to select, press to activate
        self._encoder_nav = config.get("encoder_navigation", False)
        self._encoder_flip = -1 if config.get("encoder_direction_flip", False) else 1
        self._play_on_release = config.get("play_on_release", False)
        self._selected_index = 0
        max_grid = config.get("button_cols", 4) * config.get("button_rows", 2)
        self._max_index = max_grid
        if config.get("rotary_encoder", False):
            self._init_encoder(config)

        # USB HID keyboard (Fruit Jam DVI variant)
        self._kb_device = None
        if config.get("input_type") == "USB_HID_KEYBOARD":
            self._init_keyboard(config)

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
        """Initialize hardware buttons (binary decoder or I2C expander)."""
        button_type = config.get("button_type", "decoder")

        if button_type == "i2c_expander":
            self._init_i2c_expander_buttons(config)
            return

        # Binary decoder: data pins + interrupt + latch
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

    def _init_i2c_expander_buttons(self, config):
        """Initialize buttons via PCA9555 I2C expanders."""
        from i2c_expanders.PCA9555 import PCA9555

        i2c = self._i2c if self._i2c else board.I2C()
        addresses = config.get("i2c_expander_addresses", [])
        pin_nums = config.get("i2c_expander_pins", [4, 5, 6, 7])

        self._expander_pins = []
        for addr in addresses:
            try:
                dev = PCA9555(i2c, address=addr)
                for p in pin_nums:
                    pin = dev.get_pin(p)
                    pin.switch_to_input(invert_polarity=True)
                    self._expander_pins.append(pin)
            except Exception as e:
                print("I2C expander 0x{:02x} error: {}".format(addr, e))

        # Interrupt pin (active low)
        int_pin = _pin(config.get("button_int_pin"))
        if int_pin:
            self._button_int = digitalio.DigitalInOut(int_pin)
            self._button_int.direction = digitalio.Direction.INPUT
            self._button_int.pull = digitalio.Pull.UP

        # Latch reset pin
        latch_pin = _pin(config.get("button_latch_reset_pin"))
        if latch_pin:
            self._button_latch = digitalio.DigitalInOut(latch_pin)
            self._button_latch.direction = digitalio.Direction.OUTPUT
            self._button_latch.value = True

        self._button_type = "i2c_expander"
        print("I2C expander buttons: {} pins".format(len(self._expander_pins)))

    def _init_direct_buttons(self, config):
        """Initialize individual GPIO buttons (active low with pull-up)."""
        active_low = config.get("direct_buttons_active_low", True)
        for pin_name in config["direct_button_pins"]:
            pin = digitalio.DigitalInOut(_pin(pin_name))
            pin.direction = digitalio.Direction.INPUT
            pin.pull = digitalio.Pull.UP if active_low else digitalio.Pull.DOWN
            self._direct_buttons.append(pin)
            self._direct_last.append(pin.value)
        self._direct_active_low = active_low
        print("Direct buttons ready:", len(self._direct_buttons), "pins")

    def _init_encoder(self, config):
        """Initialize rotary encoder and its push button.

        Three input decode modes, selected by config:

        - **pulse** (``encoder_pulse_mode = True``): A and B are read as
          independent active-low pulse inputs. Each falling edge on A bumps
          position +1; each falling edge on B bumps position -1. Used for
          devices that emit a single short pulse per step (e.g. sip-n-puff
          adapters) instead of a quadrature waveform.
        - **hardware**: rotaryio.IncrementalEncoder. Default when available.
        - **software**: bit-banged quadrature decode. Fallback when rotaryio
          can't claim the PIO state machine.
        """

        # Drive GND pin low if configured (uses GPIO as ground for encoder)
        gnd_pin_name = config.get("encoder_gnd_pin")
        if gnd_pin_name:
            self._encoder_gnd = digitalio.DigitalInOut(_pin(gnd_pin_name))
            self._encoder_gnd.direction = digitalio.Direction.OUTPUT
            self._encoder_gnd.value = False

        self._software_encoder = False
        self._pulse_encoder = bool(config.get("encoder_pulse_mode", False))

        if self._pulse_encoder:
            # Pulse mode — independent active-low edge inputs on A and B.
            self._enc_a = digitalio.DigitalInOut(_pin(config["encoder_pin_a"]))
            self._enc_a.direction = digitalio.Direction.INPUT
            self._enc_a.pull = digitalio.Pull.UP
            self._enc_b = digitalio.DigitalInOut(_pin(config["encoder_pin_b"]))
            self._enc_b.direction = digitalio.Direction.INPUT
            self._enc_b.pull = digitalio.Pull.UP
            self._enc_last_a = self._enc_a.value
            self._enc_last_b = self._enc_b.value
            class PulseEncoder:
                def __init__(self):
                    self.position = 0
            self._encoder = PulseEncoder()
        else:
            # Try hardware rotaryio first, fall back to software polling
            try:
                import rotaryio
                self._encoder = rotaryio.IncrementalEncoder(
                    _pin(config["encoder_pin_a"]),
                    _pin(config["encoder_pin_b"]),
                )
                # Test if it works with a quick read
                _ = self._encoder.position
            except Exception:
                self._encoder = None

            # If rotaryio didn't work or no pull-ups, use software polling
            if self._encoder is None or gnd_pin_name:
                # Software encoder needs pull-ups — rotaryio may not set them
                if self._encoder:
                    self._encoder.deinit()
                self._software_encoder = True
                self._enc_a = digitalio.DigitalInOut(_pin(config["encoder_pin_a"]))
                self._enc_a.direction = digitalio.Direction.INPUT
                self._enc_a.pull = digitalio.Pull.UP
                self._enc_b = digitalio.DigitalInOut(_pin(config["encoder_pin_b"]))
                self._enc_b.direction = digitalio.Direction.INPUT
                self._enc_b.pull = digitalio.Pull.UP
                self._enc_last_a = self._enc_a.value
                self._enc_last_b = self._enc_b.value
                # Create a simple position tracker
                class SoftEncoder:
                    def __init__(self):
                        self.position = 0
                self._encoder = SoftEncoder()

        self._last_encoder_pos = self._encoder.position
        btn_pin = _pin(config.get("encoder_button_pin"))
        if btn_pin:
            self._encoder_button = digitalio.DigitalInOut(btn_pin)
            self._encoder_button.direction = digitalio.Direction.INPUT
            self._encoder_button.pull = digitalio.Pull.UP
            self._last_encoder_button = self._encoder_button.value
        if self._pulse_encoder:
            mode = "pulse"
        elif self._software_encoder:
            mode = "software"
        else:
            mode = "hardware"
        print("Encoder ready: nav={} pos={} max={} mode={}".format(
            self._encoder_nav, self._last_encoder_pos, self._max_index, mode))

    # ---- USB HID boot keyboard (Fruit Jam DVI variant) -----------------
    # Uses adafruit_usb_host_descriptors.find_boot_keyboard_endpoint() which
    # returns a (interface_num, ep_addr) tuple — pick the IN endpoint
    # (bit 0x80 set). Requires /boot.py with usb_host.Port() to enable the
    # PIO-USB host port. Don't call is_kernel_driver_active/detach_kernel_driver
    # on CircuitPython USB host — those raise TypeError.

    def _init_keyboard(self, config):
        """Set up a USB HID boot keyboard. Lazy-attaches if absent at boot."""
        pwr_name = config.get("usb_host_5v_power")
        self._kb_5v = None
        if pwr_name:
            try:
                self._kb_5v = digitalio.DigitalInOut(_pin(pwr_name))
                self._kb_5v.direction = digitalio.Direction.OUTPUT
                self._kb_5v.value = True
            except Exception as e:
                if self._debug:
                    print("USB host 5V enable skipped:", e)
        self._kb_device = None
        self._kb_in_endpoint = 0x81
        self._kb_report = bytearray(8)
        self._kb_prev_keys = set()
        self._kb_next_attempt = 0.0
        self._kb_retry_period = 1.0
        self._try_attach_keyboard()
        print("USB keyboard input ready (attached={})".format(
            self._kb_device is not None))

    def _try_attach_keyboard(self):
        try:
            import usb.core
            import adafruit_usb_host_descriptors as _usbhd
        except ImportError as e:
            if self._debug:
                print("USB host libs missing:", e)
            return
        try:
            devs = list(usb.core.find(find_all=True))
        except Exception as e:
            if self._debug:
                print("usb.core.find failed:", type(e).__name__, repr(e))
            return
        for dev in devs:
            try:
                info = _usbhd.find_boot_keyboard_endpoint(dev)
            except Exception as e:
                if self._debug:
                    print("kb descriptor parse failed:", type(e).__name__, repr(e))
                continue
            if info is None:
                continue
            if isinstance(info, tuple):
                ep_addr = None
                for x in info:
                    if isinstance(x, int) and (x & 0x80):
                        ep_addr = x
                        break
                if ep_addr is None:
                    continue
            else:
                ep_addr = info
            try:
                dev.set_configuration()
            except Exception as cfg_e:
                if self._debug:
                    print("set_configuration note:", type(cfg_e).__name__, cfg_e)
            self._kb_device = dev
            self._kb_in_endpoint = ep_addr
            print("USB keyboard attached VID:%04x PID:%04x  ep=0x%02x" % (
                dev.idVendor, dev.idProduct, ep_addr))
            return

    def _check_keyboard(self):
        """Poll the USB keyboard. Returns button index or None."""
        if self._kb_device is None:
            now = time.monotonic()
            if now < self._kb_next_attempt:
                return None
            self._kb_next_attempt = now + self._kb_retry_period
            self._try_attach_keyboard()
            if self._kb_device is None:
                return None
        try:
            self._kb_device.read(
                self._kb_in_endpoint, self._kb_report, timeout=2,
            )
        except Exception as e:
            name = type(e).__name__
            msg = str(e).lower()
            if "timeout" in msg or name == "USBTimeoutError":
                return None
            if self._debug:
                print("kb read err, dropping:", name, repr(e))
            self._kb_device = None
            self._kb_prev_keys = set()
            return None
        keys_now = set(b for b in self._kb_report[2:8] if b)
        new_keys = keys_now - self._kb_prev_keys
        self._kb_prev_keys = keys_now
        for code in new_keys:
            result = self._handle_key(code)
            if result is not None:
                return result
        return None

    # HID usage codes
    _KEY_RIGHT = 0x4F
    _KEY_LEFT  = 0x50
    _KEY_DOWN  = 0x51
    _KEY_UP    = 0x52
    _KEY_ENTER = 0x28
    _KEY_SPACE = 0x2C
    _KEY_1     = 0x1E   # 0x1E..0x26 -> 1..9
    _KEY_9     = 0x26
    _KEY_0     = 0x27

    def _handle_key(self, code):
        """Map an HID key code to a press event.

        Arrow keys move the selected_index (matches encoder navigation).
        Enter/Space activates the selected cell.
        Number keys 1..9, 0 directly activate cells 0..9 (clamped to grid).
        """
        cols = self._config.get("button_cols", 4)
        if code == self._KEY_UP:
            self._move_selection(-cols)
        elif code == self._KEY_DOWN:
            self._move_selection(cols)
        elif code == self._KEY_LEFT:
            self._move_selection(-1)
        elif code == self._KEY_RIGHT:
            self._move_selection(1)
        elif code in (self._KEY_ENTER, self._KEY_SPACE):
            if self._debug:
                print("Keyboard: activate", self._selected_index)
            return self._selected_index
        elif self._KEY_1 <= code <= self._KEY_9:
            idx = code - self._KEY_1
            if idx < self._max_index:
                if self._debug:
                    print("Keyboard: number", idx + 1, "->", idx)
                return idx
        elif code == self._KEY_0:
            if 9 < self._max_index:
                return 9
        return None

    def _move_selection(self, delta):
        old = self._selected_index
        self._selected_index = (self._selected_index + delta) % self._max_index
        if self._debug:
            print("Keyboard: select", self._selected_index,
                  "(was", old, "delta", delta, ")")

    def poll(self):
        """Check all input sources for a button press.

        All inputs share a global debounce timer to prevent double-fires.

        Returns:
            Button index (int) if pressed, or None.
        """
        now = time.monotonic()
        if now - self._last_press_time < self._debounce_time:
            return None

        # Wake button
        result = self._check_wake()
        if result is not None:
            self._last_press_time = now
            return result

        # Encoder button
        result = self._check_encoder()
        if result is not None:
            self._last_press_time = now
            return result

        # USB HID keyboard (FRUITJAM_DVI_KBD variant)
        result = self._check_keyboard()
        if result is not None:
            self._last_press_time = now
            return result

        # Hardware button decoder
        result = self._check_buttons()
        if result is not None:
            self._last_press_time = now
            return result

        # Direct GPIO buttons
        result = self._check_direct_buttons()
        if result is not None:
            self._last_press_time = now
            return result

        # Touch screen
        result = self._check_touch()
        if result is not None:
            self._last_press_time = now
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
        """Poll hardware buttons (decoder or I2C expander)."""
        if hasattr(self, '_button_type') and self._button_type == "i2c_expander":
            return self._check_i2c_expander_buttons()

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

    def _check_i2c_expander_buttons(self):
        """Poll PCA9555 I2C expander pins. Returns button index or None.

        Edge-detects on press (False→True transition after invert).
        Only fires once per press, must release before firing again.
        """
        if not hasattr(self, '_expander_pins'):
            return None

        if not hasattr(self, '_expander_last'):
            self._expander_last = [True] * len(self._expander_pins)

        for i, pin in enumerate(self._expander_pins):
            current = pin.value  # True = idle, False = pressed
            was = self._expander_last[i]
            self._expander_last[i] = current
            if not current and was:  # Falling edge = new press
                print("I2C button:", i)
                return i
        return None

    def reset_button_latch(self):
        """Reset the button latch after handling a press.

        Call this after the action (sound playback) finishes,
        matching V1's pattern of resetting after playback completes.
        """
        if self._button_latch:
            self._button_latch.value = False
            time.sleep(0.1)
            self._button_latch.value = True

    def _check_direct_buttons(self):
        """Poll direct GPIO buttons. Returns button index or None."""
        if not self._direct_buttons:
            return None

        for i, pin in enumerate(self._direct_buttons):
            current = pin.value
            if current != self._direct_last[i]:
                self._direct_last[i] = current
                # Detect press: active low means pressed=False
                pressed = not current if self._direct_active_low else current
                if pressed:
                    if self._debug:
                        print("Direct button", i, "pressed")
                    return i
        return None

    def _check_encoder(self):
        """Poll rotary encoder rotation and button.

        In navigation mode: rotation moves selection, button activates.
        In legacy mode: button returns fixed index.
        """
        if self._encoder is None:
            return None

        # Pulse mode — independent active-low edge inputs on A and B.
        # Each falling edge on A bumps position +1; on B bumps -1.
        if self._pulse_encoder:
            a = self._enc_a.value
            b = self._enc_b.value
            if a != self._enc_last_a:
                if not a:                       # falling edge
                    self._encoder.position += 1
                self._enc_last_a = a
            if b != self._enc_last_b:
                if not b:                       # falling edge
                    self._encoder.position -= 1
                self._enc_last_b = b

        # Update software encoder — lookup table approach
        # Tracks all 4 state transitions, only counts valid sequences
        if self._software_encoder:
            a = self._enc_a.value
            b = self._enc_b.value
            state = (a << 1) | b
            last_state = (self._enc_last_a << 1) | self._enc_last_b
            if state != last_state:
                # Lookup table: [last_state][state] -> direction
                # 0=invalid/bounce, 1=CW, -1=CCW
                if not hasattr(self, '_enc_table'):
                    self._enc_table = {
                        (0,1): 1, (1,3): 1, (3,2): 1, (2,0): 1,   # CW
                        (0,2):-1, (2,3):-1, (3,1):-1, (1,0):-1,   # CCW
                    }
                    self._enc_count = 0
                direction = self._enc_table.get((last_state, state), 0)
                if direction != 0:
                    self._enc_count += direction
                    # Only commit after 2 valid steps in same direction
                    # (full detent = 2 or 4 edges depending on encoder)
                    if abs(self._enc_count) >= 2:
                        self._encoder.position += 1 if self._enc_count > 0 else -1
                        self._enc_count = 0
                else:
                    self._enc_count = 0  # Invalid transition = bounce, reset
                self._enc_last_a = a
                self._enc_last_b = b

        # Check rotation
        if self._encoder_nav:
            pos = self._encoder.position
            delta = pos - self._last_encoder_pos
            if delta != 0:
                self._last_encoder_pos = pos
                old = self._selected_index
                # Apply direction (flip via config)
                self._selected_index = (self._selected_index - delta * self._encoder_flip) % self._max_index
                if self._debug:
                    print("Encoder: select", self._selected_index,
                          "(was", old, "delta", delta, ")")
                return None  # Rotation doesn't trigger a press

        # Check button press or release
        if self._encoder_button is None:
            return None
        current = self._encoder_button.value
        if current != self._last_encoder_button:
            self._last_encoder_button = current
            # Active low: not current = pressed, current = released
            if self._play_on_release:
                trigger = current  # Trigger on release (rising edge)
            else:
                trigger = not current  # Trigger on press (falling edge)
            if trigger:
                if self._encoder_nav:
                    if self._debug:
                        print("Encoder: activate", self._selected_index)
                    return self._selected_index
                return self._encoder_button_index
        return None

    @property
    def selected_index(self):
        """Current encoder-selected grid index."""
        return self._selected_index

    @property
    def encoder_button_held(self):
        """True if the encoder button is currently pressed (active low)."""
        if self._encoder_button is None:
            return False
        return not self._encoder_button.value

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

    def _reinit_encoder_button(self):
        """Reclaim encoder button pin after software idle wake."""
        config = self._config
        btn_pin = _pin(config.get("encoder_button_pin"))
        if btn_pin and self._encoder_button is None:
            self._encoder_button = digitalio.DigitalInOut(btn_pin)
            self._encoder_button.direction = digitalio.Direction.INPUT
            self._encoder_button.pull = digitalio.Pull.UP
            self._last_encoder_button = self._encoder_button.value

    @property
    def debug(self):
        return self._debug

    @debug.setter
    def debug(self, value):
        self._debug = value

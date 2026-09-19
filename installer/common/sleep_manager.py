"""Sleep and power management for AAC device.

Handles inactivity timeout, peripheral shutdown, and sleep/wake.

Supports three sleep modes:
    - light: alarm-based, program resumes after wake, fast (~100ms)
    - deep:  alarm-based, full restart on wake, lowest power (~70uA)
    - software_idle: no alarm module needed — powers down peripherals
      and polls encoder in a slow loop until activity detected.
      Used on RP2350/Fruit Jam where alarm module is unavailable.
"""

import time
import board

try:
    import alarm
    import alarm.pin
    _HAS_ALARM = True
except ImportError:
    _HAS_ALARM = False

try:
    import supervisor
    _HAS_SUPERVISOR = True
except ImportError:
    _HAS_SUPERVISOR = False


def _pin(name):
    """Resolve pin name string to board pin. Returns None if name is None."""
    if name is None:
        return None
    return getattr(board, name)


class SleepManager:
    """Manages inactivity timeout and sleep/wake transitions."""

    def __init__(self, config):
        """Initialize sleep manager from hardware config.

        Args:
            config: Hardware config dict with sleep_* keys.
        """
        self._enabled = config.get("sleep_enabled", False)
        self._timeout = config.get("sleep_timeout", 120)
        self._mode = config.get("sleep_mode", "light")
        # Resolved once so the alarm path, the software-idle poll and the
        # startup banner all report the same list. Variants that declare
        # nothing fall back to whatever button they already have.
        self._wake_pin_names = list(config.get("sleep_wake_pins") or [])
        if not self._wake_pin_names:
            fallback = (config.get("emergency_push_pin")
                        or config.get("encoder_button_pin"))
            if fallback:
                self._wake_pin_names = [fallback]
        self._config = config

        # Track last activity
        self._last_activity = time.monotonic()

        # References to hardware subsystems (set by Machine)
        self._pixel = None
        self._input = None
        self._display = None
        self._backlight_pin_name = config.get("lcd_backlight")
        self._amp_en_pin_name = config.get("amp_en_pin")
        self._amp_active_low = config.get("amp_en_active_low", True)
        self._touch_rst_pin_name = config.get("touch_rst")

        # References for software_idle mode (set by Machine)
        self._peripherals = None
        self._full_power = None
        self._full_power_active_low = config.get("full_power_active_low", True)
        # When True, disable the rail by RELEASING the pin to high-Z (an
        # external pull-up holds the load switch off) instead of driving it to
        # the inactive level. Used by boards whose enable net must float off.
        self._full_power_off_release = config.get("full_power_off_release", False)
        self._full_power_settle_ms = config.get("full_power_settle_ms", 500)
        self._periph_reset_pin_name = config.get("periph_reset_pin")
        self._periph_reset = None  # DigitalInOut, claimed during idle

        # If alarm module not available, fall back to software_idle
        if self._enabled and not _HAS_ALARM:
            if self._mode != "software_idle":
                print("Sleep: no alarm module — falling back to software_idle")
                self._mode = "software_idle"

        if self._enabled:
            print("Sleep: enabled, timeout={}s, mode={}".format(
                self._timeout, self._mode))
            print("Sleep: wake pins:", self._wake_pin_names)
            if _HAS_SUPERVISOR and supervisor.runtime.usb_connected:
                if self._config.get("sleep_on_usb", False):
                    print("Sleep: USB connected — sleeping anyway (sleep_on_usb)")
                else:
                    print("Sleep: USB connected — sleep suspended until unplugged")
        else:
            print("Sleep: disabled")

    def set_pixel(self, pixel):
        """Set the NeoPixel reference for shutdown before sleep."""
        self._pixel = pixel

    def set_input(self, input_manager):
        """Set InputManager reference so we can release pins for sleep."""
        self._input = input_manager

    def set_display(self, display_manager):
        """Set DisplayManager reference for backlight control."""
        self._display = display_manager

    def set_peripherals(self, peripherals):
        """Set Fruit Jam Peripherals reference for software_idle shutdown."""
        self._peripherals = peripherals

    def set_full_power(self, full_power):
        """Set FULL_POWER DigitalInOut reference for software_idle."""
        self._full_power = full_power

    def activity(self):
        """Call this on any user interaction to reset the inactivity timer."""
        self._last_activity = time.monotonic()

    def check(self):
        """Check if inactivity timeout has elapsed. Call in the main loop.

        Returns:
            True if the device went to sleep and woke back up (light sleep).
            False if no sleep occurred.
            For deep sleep, this never returns — code.py restarts.
        """
        if not self._enabled:
            return False

        # USB means external power, and on a board with a battery it means
        # charging. There is nothing to save, and a device that blanks itself
        # on the charger just looks broken. Software idle used to be exempted
        # here because it does not drop the USB link the way light sleep
        # does -- but "can" is not "should".
        #
        # sleep_on_usb re-enables it, which bench work needs: sleeping on the
        # cable is the only way to watch a sleep cycle over serial.
        if _HAS_SUPERVISOR and supervisor.runtime.usb_connected:
            if not self._config.get("sleep_on_usb", False):
                return False

        elapsed = time.monotonic() - self._last_activity
        if elapsed < self._timeout:
            return False

        print("Sleep: timeout after {}s inactivity".format(int(elapsed)))
        return self._enter_sleep()

    @property
    def time_until_sleep(self):
        """Seconds remaining until sleep. -1 if sleep is disabled."""
        if not self._enabled:
            return -1
        remaining = self._timeout - (time.monotonic() - self._last_activity)
        return max(0, remaining)

    def _enter_sleep(self):
        """Power down peripherals and enter sleep mode."""
        if self._mode == "software_idle":
            return self._enter_software_idle()

        self._power_down()

        # Release GPIO pins that the alarm module needs
        if self._input:
            self._input.deinit_for_sleep()

        # Build wake alarms from configured pins
        alarms = []
        for pin_name in self._wake_pin_names:
            pin = _pin(pin_name)
            if pin:
                # All wake pins are active LOW (touch INT, boot button)
                a = alarm.pin.PinAlarm(pin=pin, value=False, pull=True)
                alarms.append(a)

        if not alarms:
            print("Sleep: no wake pins configured, cannot sleep")
            if self._input:
                self._input.reinit_after_sleep()
            self._power_up()
            return False

        if self._mode == "deep":
            print("Sleep: entering deep sleep (will restart on wake)...")
            alarm.exit_and_deep_sleep_until_alarms(*alarms)
            # Never reaches here — device restarts

        else:  # light sleep
            print("Sleep: entering light sleep...")
            triggered = alarm.light_sleep_until_alarms(*alarms)
            print("Sleep: woke up from light sleep")
            if triggered:
                print("Sleep: wake source:", triggered)
            if self._input:
                self._input.reinit_after_sleep()
            self._power_up()
            self._last_activity = time.monotonic()
            return True

    def _enter_software_idle(self):
        """Software idle mode: power down peripherals, poll for wake.

        Used on RP2350 devices where the alarm module is not available.
        Two paths:
          - Heavy (Fruit Jam): deinit Peripherals, cut FULL_POWER, reset on wake
          - Light (OLED badge): DISPLAYOFF, poll button, DISPLAYON on wake
        """
        import digitalio

        print("Sleep: entering software idle...")

        # Whether the FULL_POWER rail may be dropped. Cutting it is what
        # actually darkens a screen whose backlight has no pin of its own --
        # blanking pixels leaves the backlight burning.
        #
        # Derived from board facts rather than declared as a verb, because
        # the failure it guards is invisible in a variant file: a rail that
        # feeds the wake inputs takes the wake path down with it, and a rail
        # that feeds a panel with its own backlight pin need not be cut at
        # all. The policy lives here so a user enabling sleep from config.txt
        # cannot arm it by hand.
        #
        # Waking no longer resets the board. That was the old "heavy" path,
        # and repeated resets are how a board ended up sitting in the RP2350
        # bootloader. The display is rebuilt in place instead -- bench-tested:
        # the button still registers with the rail down, and the panel
        # re-initialises after losing power.
        cut_rail = self._full_power is not None
        if cut_rail:
            if self._config.get("full_power_feeds_inputs", False):
                print("Sleep: FULL_POWER feeds the wake inputs — staying powered")
                cut_rail = False
            elif self._config.get("full_power_feeds_display", False):
                print("Sleep: FULL_POWER feeds the panel — staying powered")
                cut_rail = False
        heavy_sleep = False          # the reset-on-wake path is retired

        if heavy_sleep:
            # Heavy path: Fruit Jam — deinit hardware, reset on wake
            if self._peripherals:
                self._peripherals.deinit()
                print("Sleep: Peripherals deinited")

            if self._periph_reset_pin_name:
                pin = _pin(self._periph_reset_pin_name)
                self._periph_reset = digitalio.DigitalInOut(pin)
                self._periph_reset.direction = digitalio.Direction.OUTPUT
                self._periph_reset.value = False
                print("Sleep: PERIPH_RESET held LOW")

            if self._full_power:
                if self._full_power_off_release:
                    self._full_power.switch_to_input()
                else:
                    self._full_power.value = self._full_power_active_low
                print("Sleep: FULL_POWER OFF")
        else:
            # Blank the panel and turn off whatever has its own pin
            # (backlight, amplifier, NeoPixel) on variants that wire them.
            self._power_down()
            if self._display:
                self._display.sleep_display()
                print("Sleep: display off")

            # Then drop the rail, where the board allows it. This is the
            # only way to darken a backlight that has no pin of its own.
            if cut_rail:
                if self._full_power_off_release:
                    self._full_power.switch_to_input()
                else:
                    self._full_power.value = self._full_power_active_low
                print("Sleep: FULL_POWER OFF (rail down)")

        # Poll for wake — declared wake pins, plus encoder rotation.
        print("Sleep: idle, polling for wake...")

        # InputManager holds the encoder button; hand it back unconditionally
        # so the pin is free to claim below. Testing whether it is "one of the
        # wake pins" by name would miss a variant spelling the same physical
        # pin under another board alias (BUTTON1 and GPIO0 are one pin here),
        # and the light path reclaims it on wake anyway.
        if self._input and getattr(self._input, "_encoder_button", None):
            self._input._encoder_button.deinit()
            self._input._encoder_button = None

        wake_btns = []
        for name in self._wake_pin_names:
            try:
                btn = digitalio.DigitalInOut(_pin(name))
                btn.direction = digitalio.Direction.INPUT
                btn.pull = digitalio.Pull.UP
                wake_btns.append((name, btn))
            except Exception as e:
                print("Sleep: wake pin {} unavailable: {}".format(name, e))

        encoder = None
        last_pos = 0
        if self._input and hasattr(self._input, '_encoder'):
            encoder = self._input._encoder
            if encoder:
                last_pos = encoder.position

        # I2C expander buttons are just more active-low inputs; folding them
        # into one list keeps the poll a single shape instead of three.
        expander_pins = getattr(self._input, "_expander_pins", None) or []
        wake_inputs = wake_btns + [("expander", p) for p in expander_pins]

        # Refuse to sleep with nothing able to wake us — that is how a device
        # goes quiet for good. The alarm path already takes this stance.
        if not wake_inputs and encoder is None:
            print("Sleep: no wake source available — staying awake")
            if not heavy_sleep:
                if self._display:
                    self._display.wake_display()
                self._power_up()
            if self._input and hasattr(self._input, '_reinit_encoder_button'):
                self._input._reinit_encoder_button()
            self._last_activity = time.monotonic()
            return False

        print("Sleep: wake sources:",
              ", ".join([n for n, _ in wake_inputs] +
                        (["encoder rotation"] if encoder else [])))

        while True:
            woke_on = None
            for name, pin in wake_inputs:
                if not pin.value:          # active low
                    woke_on = name
                    break
            if woke_on:
                print("Sleep: wake from", woke_on)
                break
            if encoder and encoder.position != last_pos:
                print("Sleep: encoder wake (pos {} -> {})".format(
                    last_pos, encoder.position))
                break
            time.sleep(0.1)

        for _name, btn in wake_btns:
            btn.deinit()   # expander pins belong to InputManager; leave them

        # Reset button latch to stop vibration motors
        if self._input and hasattr(self._input, 'reset_button_latch'):
            self._input.reset_button_latch()

        if heavy_sleep:
            # Heavy wake: full device reset
            self._wake_from_idle()
        else:
            # Wake in place. Rail first: the panel has no power until it is
            # back, and the controller lost its configuration with it, so the
            # display is rebuilt rather than merely repainted.
            if cut_rail and self._full_power:
                self._full_power.switch_to_output(
                    value=not self._full_power_active_low)
                time.sleep(self._full_power_settle_ms / 1000.0)
                print("Sleep: FULL_POWER ON (rail up)")
                if self._display:
                    self._display.rebuild()
            if self._display:
                self._display.wake_display()
                print("Sleep: display on")
            self._power_up()
            if self._input and hasattr(self._input, '_reinit_encoder_button'):
                self._input._reinit_encoder_button()

        self._last_activity = time.monotonic()
        return True

    def _wake_from_idle(self):
        """Restart the device after software idle wake.

        Reinitializing Peripherals, display SPI, and audio after power-down
        is fragile. A clean reset is fast (~2s) and reliable.
        """
        import microcontroller
        print("Sleep: waking — resetting device...")
        microcontroller.reset()

    def _power_down(self):
        """Turn off peripherals to minimize power draw during sleep."""
        # Turn off NeoPixel
        if self._pixel:
            self._pixel[0] = (0, 0, 0)

        # Turn off display backlight via DisplayManager
        if self._display:
            self._display.set_backlight(False)

        # Disable amplifier (save power)
        amp_pin = _pin(self._amp_en_pin_name)
        if amp_pin:
            try:
                import digitalio
                amp = digitalio.DigitalInOut(amp_pin)
                amp.switch_to_output(value=self._amp_active_low)
                amp.deinit()
            except ValueError:
                pass

        # Keep touch controller active (do NOT reset it) so it can
        # generate the INT signal that wakes us up

        print("Sleep: peripherals powered down")

    def _power_up(self):
        """Restore peripherals after light sleep wake."""
        # Restore display backlight via DisplayManager
        if self._display:
            self._display.set_backlight(True)

        # Re-enable amplifier
        amp_pin = _pin(self._amp_en_pin_name)
        if amp_pin:
            try:
                import digitalio
                amp = digitalio.DigitalInOut(amp_pin)
                amp.switch_to_output(value=not self._amp_active_low)
                amp.deinit()
            except ValueError:
                pass

        # Restore NeoPixel status
        if self._pixel:
            self._pixel[0] = (0, 0, 255)  # Blue = ready

        print("Sleep: peripherals restored")

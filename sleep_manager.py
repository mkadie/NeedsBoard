"""Sleep and power management for AAC device.

Handles inactivity timeout, peripheral shutdown, and sleep/wake
using the CircuitPython alarm module.

Supports two sleep modes:
    - light: program resumes after wake, fast (~100ms)
    - deep:  full restart on wake, lowest power (~70uA)
"""

import time
import board
import alarm
import alarm.pin
import supervisor


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
        self._wake_pin_names = config.get("sleep_wake_pins", [])
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

        if self._enabled:
            print("Sleep: enabled, timeout={}s, mode={}".format(
                self._timeout, self._mode))
            print("Sleep: wake pins:", self._wake_pin_names)
            if supervisor.runtime.usb_connected:
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

        # Don't sleep while connected to USB — light sleep causes
        # USB disconnect which triggers auto-reload (looks like a reboot).
        # On battery (the target use case) this check is False.
        if supervisor.runtime.usb_connected:
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

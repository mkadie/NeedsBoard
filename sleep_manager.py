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

        # References for software_idle mode (set by Machine)
        self._peripherals = None
        self._full_power = None
        self._full_power_active_low = config.get("full_power_active_low", True)
        self._full_power_settle_ms = config.get("full_power_settle_ms", 500)
        self._periph_reset_pin_name = config.get("periph_reset_pin")
        self._periph_reset = None  # DigitalInOut, claimed during idle

        # Disable if alarm module is not available and mode requires it
        if self._enabled and not _HAS_ALARM and self._mode != "software_idle":
            print("Sleep: alarm module not available — disabled")
            self._enabled = False

        if self._enabled:
            print("Sleep: enabled, timeout={}s, mode={}".format(
                self._timeout, self._mode))
            print("Sleep: wake pins:", self._wake_pin_names)
            if _HAS_SUPERVISOR and supervisor.runtime.usb_connected:
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

        # Don't sleep while connected to USB — light sleep causes
        # USB disconnect which triggers auto-reload (looks like a reboot).
        # Software idle is safe over USB (no USB disconnect), so allow it.
        if _HAS_SUPERVISOR and supervisor.runtime.usb_connected:
            if self._mode != "software_idle":
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
        """Software idle mode: power down peripherals, poll encoder for wake.

        Used on RP2350/Fruit Jam where the alarm module is not available.
        Powers down: display (via FULL_POWER), DAC/ESP32 (via PERIPH_RESET).
        Polls the rotary encoder in a slow loop for wake activity.
        """
        import digitalio

        print("Sleep: entering software idle...")

        # Turn off NeoPixel
        if self._pixel:
            self._pixel[0] = (0, 0, 0)

        # Deinit Peripherals (releases DAC, MCLK, audio)
        if self._peripherals:
            self._peripherals.deinit()
            print("Sleep: Peripherals deinited")

        # Drive PERIPH_RESET low to cut power to DAC and ESP32
        if self._periph_reset_pin_name:
            pin = _pin(self._periph_reset_pin_name)
            self._periph_reset = digitalio.DigitalInOut(pin)
            self._periph_reset.direction = digitalio.Direction.OUTPUT
            self._periph_reset.value = False
            print("Sleep: PERIPH_RESET held LOW")

        # Cut display power via FULL_POWER (TPS22917)
        if self._full_power:
            active_low = self._full_power_active_low
            self._full_power.value = active_low  # Disable: HIGH if active_low
            print("Sleep: FULL_POWER OFF")

        # Poll for wake — check encoder rotation and emergency/button pins
        print("Sleep: idle, polling for wake...")
        emergency_pin = None
        emergency_pin_name = self._config.get("emergency_push_pin")
        if emergency_pin_name and self._config.get("emergency_push_enabled"):
            pin = _pin(emergency_pin_name)
            emergency_pin = digitalio.DigitalInOut(pin)
            emergency_pin.direction = digitalio.Direction.INPUT
            emergency_pin.pull = digitalio.Pull.UP

        encoder = None
        last_pos = 0
        if self._input and hasattr(self._input, '_encoder'):
            encoder = self._input._encoder
            if encoder:
                last_pos = encoder.position

        while True:
            # Check emergency/button pin (active low)
            if emergency_pin and not emergency_pin.value:
                print("Sleep: button wake!")
                break
            # Check encoder rotation
            if encoder:
                pos = encoder.position
                if pos != last_pos:
                    print("Sleep: encoder wake (pos {} -> {})".format(
                        last_pos, pos))
                    break
            time.sleep(0.1)

        if emergency_pin:
            emergency_pin.deinit()

        # Wake: restore everything
        self._wake_from_idle()
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

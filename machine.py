"""Machine — top-level AAC device orchestrator.

Initializes all hardware subsystems from a named variant config
and runs the main application loop.
"""

import time
import busio
import board
import button_config
from hardware_config import VARIANTS, DEFAULT_VARIANT
from display_manager import DisplayManager
from audio_player import AudioPlayer
from input_manager import InputManager


def _pin(name):
    """Resolve pin name string to board pin. Returns None if name is None."""
    if name is None:
        return None
    return getattr(board, name)


class Machine:
    """AAC communication device: reads config, inits hardware, runs loop."""

    def __init__(self, variant_name=None):
        """Build the machine from a named variant config.

        Args:
            variant_name: Key into VARIANTS dict. Uses DEFAULT_VARIANT if None.
        """
        if variant_name is None:
            variant_name = DEFAULT_VARIANT

        if variant_name not in VARIANTS:
            raise ValueError("Unknown variant: " + variant_name)

        self._config = VARIANTS[variant_name]
        print("AAC Device — variant:", self._config["name"])

        # Status LED (optional)
        self._pixel = None
        neo_pin = _pin(self._config.get("neopixel_pin"))
        if neo_pin:
            import neopixel
            self._pixel = neopixel.NeoPixel(neo_pin, 1, brightness=0.05, auto_write=True)
        self.set_status("init")

        # Shared I2C bus (touch + codec may share it)
        self._i2c = None
        scl = _pin(self._config.get("i2c_scl"))
        sda = _pin(self._config.get("i2c_sda"))
        if scl and sda:
            self._i2c = busio.I2C(scl, sda, frequency=self._config.get("i2c_freq", 400_000))

        # Subsystems
        self.display = DisplayManager(self._config)
        print("Display ready")

        self.audio = AudioPlayer(self._config, i2c=self._i2c)
        print("Audio ready")

        self.input = InputManager(self._config, self.display, i2c=self._i2c)
        print("Input ready")

    def run(self):
        """Main application loop. Polls inputs and plays sounds."""
        cfg = self._config
        print("AAC Device ready")
        print("Grid:", cfg["button_cols"], "x", cfg["button_rows"])
        print("Sounds:", len(button_config.button_sound), "configured")
        self.set_status("ready")

        while True:
            button = self.input.poll()
            if button is not None:
                self._play_button(button)
            time.sleep(0.01)

    def _play_button(self, button_index):
        """Play the sound for a button index with status LED feedback."""
        if button_index < 0 or button_index >= len(button_config.button_sound):
            print("Invalid button:", button_index)
            return

        sound_file = button_config.button_sound[button_index]
        print("Playing:", sound_file)
        self.set_status("playing")

        try:
            self.audio.play(sound_file)
        except Exception as e:
            print("Error:", e)
            self.set_status("error")
            time.sleep(0.5)

        self.set_status("ready")

    def set_status(self, state):
        """Update NeoPixel status LED. No-op if no LED configured."""
        if self._pixel is None:
            return
        colors = {
            "init": (255, 255, 0),    # Yellow
            "ready": (0, 0, 255),     # Blue
            "playing": (0, 255, 0),   # Green
            "error": (255, 0, 0),     # Red
        }
        self._pixel[0] = colors.get(state, (255, 255, 255))

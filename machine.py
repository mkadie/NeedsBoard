"""Machine — top-level AAC device orchestrator.

Initializes all hardware subsystems from a named variant config,
loads the menu system, and runs the main application loop.
"""

import time
import board
from hardware_config import VARIANTS, DEFAULT_VARIANT


def _pin(name):
    """Resolve pin name string to board pin. Returns None if name is None."""
    if name is None:
        return None
    return getattr(board, name)


class Machine:
    """AAC communication device: reads config, inits hardware, runs loop."""

    def __init__(self, variant_name=None, menus_dir="/menus",
                 start_menu=None):
        """Build the machine from a named variant config.

        Args:
            variant_name: Key into VARIANTS dict. Uses DEFAULT_VARIANT if None.
            menus_dir: Directory containing .menu files.
            start_menu: Filename of the starting menu.
        """
        if variant_name is None:
            variant_name = DEFAULT_VARIANT

        if variant_name not in VARIANTS:
            raise ValueError("Unknown variant: " + variant_name)

        self._config = VARIANTS[variant_name]
        self._menus_dir = menus_dir
        if start_menu is None:
            start_menu = self._config.get("start_menu", "base.menu")
        self._start_menu = start_menu
        print("AAC Device — variant:", self._config["name"])

        # FULL_POWER — enable first so rail settles during other init
        self._full_power = None
        if self._config.get("full_power_pin"):
            self._init_full_power()

        # Emergency push fast path: check button BEFORE heavy init
        self._emergency_playing = False
        emergency_held = self._check_emergency_pin()

        # Fruit Jam Peripherals (must init before anything else on FruitJam)
        self._peripherals = None
        if self._config["sound_system"] == "FRUITJAM_DAC":
            self._init_fruitjam_peripherals()

        # If emergency button held, start playing sound NOW before display/menus
        if emergency_held:
            self._start_emergency_sound()

        # Deferred imports — these run while emergency sound plays
        import busio
        from storage_manager import StorageManager
        from display_manager import DisplayManager
        from audio_player import AudioPlayer
        from input_manager import InputManager
        from menu_parser import MenuStack
        from action import Action
        from sleep_manager import SleepManager

        # Status LED (optional)
        self._pixel = None
        neo_pin = _pin(self._config.get("neopixel_pin"))
        if neo_pin:
            import neopixel
            self._pixel = neopixel.NeoPixel(neo_pin, 1, brightness=0.05, auto_write=True)
        self.set_status("init")

        # Storage manager — mounts SD card, creates shared SPI bus
        # Must be initialized BEFORE display (SD card needs SPI first)
        self.storage = StorageManager(self._config)

        # Sync flash content to SD card if SD is available and new
        if self.storage.sd_available:
            self.storage.sync_flash_to_sd()

        # Shared I2C bus (touch + codec may share it)
        # Skip if Peripherals already owns the I2C bus
        self._i2c = None
        if self._peripherals is None:
            scl = _pin(self._config.get("i2c_scl"))
            sda = _pin(self._config.get("i2c_sda"))
            if scl and sda:
                self._i2c = busio.I2C(scl, sda, frequency=self._config.get("i2c_freq", 400_000))

        # Display — pass shared SPI bus if SD card shares it
        spi = self.storage.spi if self._config.get("sd_shares_display_spi") else None
        self.display = DisplayManager(self._config, spi=spi)
        print("Display ready")

        # Full audio init (reuses Peripherals audio if emergency already started)
        self.audio = AudioPlayer(self._config, i2c=self._i2c,
                                 storage=self.storage,
                                 peripherals=self._peripherals)
        print("Audio ready")

        self.input = InputManager(self._config, self.display, i2c=self._i2c)
        print("Input ready")

        # Action executor — uses storage for SD-first path resolution
        self.action = Action(
            audio=self.audio,
            display=self.display,
            pixel=self._pixel,
            menus_dir=menus_dir,
            storage=self.storage,
        )

        # Sleep / power management
        self.sleep = SleepManager(self._config)
        self.sleep.set_pixel(self._pixel)
        self.sleep.set_input(self.input)
        self.sleep.set_display(self.display)
        if self._peripherals:
            self.sleep.set_peripherals(self._peripherals)
        if self._full_power:
            self.sleep.set_full_power(self._full_power)

        # Menu system — try to load from .menu files, fall back to button_config
        self._menu_stack = None
        self._grid = None
        self._use_legacy = False
        try:
            self._menu_stack = MenuStack(menus_dir, self._start_menu,
                                         storage=self.storage)
            self._build_grid()
            self._update_display()
            print("Menu loaded:", self._menu_stack.name)
        except Exception as e:
            print("Menu load failed ({}), falling back to button_config".format(e))
            self._use_legacy = True
            import button_config
            self._legacy_sounds = button_config.button_sound

    def _check_emergency_pin(self):
        """Check if emergency button is held at boot. Returns True if pressed.

        Pin defaults to encoder_button_pin if emergency_push_pin not set.
        """
        cfg = self._config
        if not cfg.get("emergency_push_enabled", False):
            return False

        pin_name = cfg.get("emergency_push_pin",
                           cfg.get("encoder_button_pin"))
        if not pin_name:
            return False

        import digitalio
        pin = digitalio.DigitalInOut(_pin(pin_name))
        pin.direction = digitalio.Direction.INPUT
        pin.pull = digitalio.Pull.UP
        time.sleep(0.01)  # Let pull-up settle
        pressed = not pin.value  # Active low (pulled up, pressed = low)
        pin.deinit()

        if pressed:
            print("EMERGENCY: button held at boot!")
        return pressed

    def _start_emergency_sound(self):
        """Play emergency sound ASAP using minimal audio init."""
        cfg = self._config
        sound_file = cfg.get("emergency_push_sound")
        if not sound_file or not self._peripherals:
            return

        try:
            import audiomp3
            # Configure DAC with minimal setup
            self._peripherals.audio_output = "speaker"
            self._peripherals.dac.dac_volume = cfg.get("dac_volume", -10)
            self._peripherals.dac.speaker_volume = cfg.get("speaker_volume", 0)
            self._peripherals.dac.speaker_gain = cfg.get("speaker_gain", 24)

            f = open(sound_file, "rb")
            mp3 = audiomp3.MP3Decoder(f)
            self._peripherals.audio.play(mp3)
            self._emergency_playing = True
            self._emergency_file = f
            print("EMERGENCY: playing", sound_file)
        except Exception as e:
            print("EMERGENCY: sound error:", e)

    def _init_fruitjam_peripherals(self):
        """Initialize Fruit Jam Peripherals (DAC, MCLK, PERIPH_RESET).

        Peripherals claims D8/D9/D10 as buttons, but we need them for
        the rotary encoder. Release the button pins after init so
        InputManager can claim them for encoder use.
        """
        import displayio
        displayio.release_displays()
        from adafruit_fruitjam.peripherals import Peripherals
        self._peripherals = Peripherals()
        # Release D8/D9/D10 so encoder can use them
        if hasattr(self._peripherals, '_buttons'):
            for btn in self._peripherals._buttons:
                btn.deinit()
            self._peripherals._buttons = []
            print("Fruit Jam Peripherals ready (encoder pins released)")

    def _init_full_power(self):
        """Enable FULL_POWER pin — no blocking settle, overlaps with other init."""
        import digitalio
        cfg = self._config
        pin = _pin(cfg["full_power_pin"])
        self._full_power = digitalio.DigitalInOut(pin)
        self._full_power.direction = digitalio.Direction.OUTPUT
        active_low = cfg.get("full_power_active_low", True)
        self._full_power.value = not active_low  # Enable: LOW if active_low
        print("FULL_POWER enabled")

    def _build_grid(self):
        """Build the press grid from the current menu."""
        from menu_parser import get_grid_items, get_sorted_items
        header = self._menu_stack.header
        menu_type = self._menu_stack.menu_type

        if menu_type == "grid":
            cols = header.get("columns", self._config["button_cols"])
            rows = header.get("rows", self._config["button_rows"])
            self._grid = get_grid_items(self._menu_stack.items, cols, rows)
        elif menu_type == "list":
            sort_by = header.get("sort", "alpha")
            self._grid = get_sorted_items(self._menu_stack.items, sort_by)
        else:
            self._grid = self._menu_stack.items

    def run(self):
        """Main application loop. Polls inputs and executes actions."""
        cfg = self._config

        # Wait for emergency sound to finish if it was triggered at boot
        if self._emergency_playing:
            print("EMERGENCY: waiting for sound to finish...")
            while self._peripherals.audio.playing:
                time.sleep(0.01)
            self._emergency_file.close()
            self._emergency_playing = False
            print("EMERGENCY: done")

        print("AAC Device ready")
        print("Grid:", cfg["button_cols"], "x", cfg["button_rows"])
        if self.storage.sd_available:
            print("Storage: SD card active")
        if self._use_legacy:
            print("Mode: legacy (button_config.py)")
            print("Sounds:", len(self._legacy_sounds), "configured")
        else:
            print("Mode: menu system")
            print("Menu:", self._menu_stack.name)
            print("Items:", len(self._menu_stack.items))
        self.set_status("ready")

        # Show initial highlight if encoder navigation is active
        self._has_encoder_nav = self._config.get("encoder_navigation", False)
        if self._has_encoder_nav:
            self.display.set_highlight(self.input.selected_index)

        while True:
            button = self.input.poll()
            if button is not None:
                self.sleep.activity()
                self._handle_press(button)
            else:
                self.sleep.check()
            # Update highlight position from encoder
            if self._has_encoder_nav:
                self.display.set_highlight(self.input.selected_index)
            time.sleep(0.01)

    def _handle_press(self, button_index):
        """Handle a button press — dispatch to menu or legacy mode."""
        if self._use_legacy:
            self._play_legacy(button_index)
        else:
            self._execute_menu_press(button_index)

    def _execute_menu_press(self, button_index):
        """Look up the press item and execute its actions."""
        if button_index < 0 or button_index >= len(self._grid):
            print("Invalid button:", button_index)
            return

        item = self._grid[button_index]
        if item is None:
            return  # Empty grid slot

        print("Press:", item.get("label", item.get("id", "?")))
        self.set_status("playing")

        try:
            nav = self.action.execute(item)
        except Exception as e:
            print("Action error:", e)
            self.set_status("error")
            time.sleep(0.5)
            self.set_status("ready")
            return

        self.set_status("ready")

        # Handle navigation
        if nav is None:
            return
        if nav == "back":
            if self._menu_stack.back():
                self._build_grid()
                self._update_display()
                print("Back to:", self._menu_stack.name)
            else:
                print("Already at root menu")
        elif nav.startswith("submenu:") or nav.startswith("list:"):
            menu_file = nav.split(":", 1)[1]
            try:
                self._menu_stack.navigate(menu_file)
                self._build_grid()
                self._update_display()
                print("Navigated to:", self._menu_stack.name)
            except Exception as e:
                print("Navigation error:", e)

    def _resolve_path(self, path):
        """Resolve a menu-relative path to an absolute device path.

        Paths starting with / are already absolute.
        Other paths are relative to the menus directory.
        Then checks SD card via storage manager.
        """
        if not path:
            return path
        if not path.startswith("/"):
            path = self._menus_dir + "/" + path
        if self.storage:
            return self.storage.resolve_path(path)
        return path

    def _update_display(self):
        """Update the display background for the current menu."""
        bg = self._menu_stack.header.get("background")
        if bg:
            try:
                self.display.set_background(self._resolve_path(bg))
            except Exception as e:
                print("Background load error:", e)

    def _play_legacy(self, button_index):
        """Legacy mode: play sound by index from button_config."""
        if button_index < 0 or button_index >= len(self._legacy_sounds):
            print("Invalid button:", button_index)
            return

        sound_file = self._legacy_sounds[button_index]
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

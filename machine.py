"""Machine — top-level AAC device orchestrator.

Initializes all hardware subsystems from a named variant config,
loads the menu system, and runs the main application loop.
"""

import time
import busio
import board
from hardware_config import VARIANTS, DEFAULT_VARIANT
from display_manager import DisplayManager
from audio_player import AudioPlayer
from input_manager import InputManager
from menu_parser import MenuStack, get_grid_items, get_sorted_items
from action import Action
from sleep_manager import SleepManager


def _pin(name):
    """Resolve pin name string to board pin. Returns None if name is None."""
    if name is None:
        return None
    return getattr(board, name)


class Machine:
    """AAC communication device: reads config, inits hardware, runs loop."""

    def __init__(self, variant_name=None, menus_dir="/menus",
                 start_menu="base.menu"):
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

        # Hardware subsystems
        self.display = DisplayManager(self._config)
        print("Display ready")

        self.audio = AudioPlayer(self._config, i2c=self._i2c)
        print("Audio ready")

        self.input = InputManager(self._config, self.display, i2c=self._i2c)
        print("Input ready")

        # Action executor
        self.action = Action(
            audio=self.audio,
            display=self.display,
            pixel=self._pixel,
            menus_dir=menus_dir,
        )

        # Sleep / power management
        self.sleep = SleepManager(self._config)
        self.sleep.set_pixel(self._pixel)
        self.sleep.set_input(self.input)

        # Menu system — try to load from .menu files, fall back to button_config
        self._menu_stack = None
        self._grid = None
        self._use_legacy = False
        try:
            self._menu_stack = MenuStack(menus_dir, start_menu)
            self._build_grid()
            self._update_display()
            print("Menu loaded:", self._menu_stack.name)
        except Exception as e:
            print("Menu load failed ({}), falling back to button_config".format(e))
            self._use_legacy = True
            import button_config
            self._legacy_sounds = button_config.button_sound

    def _build_grid(self):
        """Build the press grid from the current menu."""
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
        print("AAC Device ready")
        print("Grid:", cfg["button_cols"], "x", cfg["button_rows"])
        if self._use_legacy:
            print("Mode: legacy (button_config.py)")
            print("Sounds:", len(self._legacy_sounds), "configured")
        else:
            print("Mode: menu system")
            print("Menu:", self._menu_stack.name)
            print("Items:", len(self._menu_stack.items))
        self.set_status("ready")

        while True:
            button = self.input.poll()
            if button is not None:
                self.sleep.activity()
                self._handle_press(button)
            else:
                self.sleep.check()
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
        """
        if not path or path.startswith("/"):
            return path
        return self._menus_dir + "/" + path

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

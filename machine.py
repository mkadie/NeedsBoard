# ---------------------------------------------------------------------------
# Modified file — originally from T-Rex Talker (https://github.com/mkadie).
#
# Upstream license: MIT.
#     Copyright (c) T-Rex Talker contributors. All rights reserved under MIT.
#     Permission is hereby granted, free of charge, to any person obtaining
#     a copy of the upstream software and associated documentation files,
#     to deal in the Software without restriction, subject to the conditions
#     in the upstream LICENSE file. See ../NOTICE for the full MIT text.
#
# Modifications in this file were added as part of T-Rex Talker Interactive
# and are licensed under the PolyForm Noncommercial License 1.0.0.
# See ../LICENSE for terms and ../upstream_patches/README.md for what changed.
# ---------------------------------------------------------------------------
"""Machine — top-level AAC device orchestrator.

Initializes all hardware subsystems from a named variant config,
loads the menu system, and runs the main application loop.
"""

import time
import board
from hardware_config import VARIANTS, DEFAULT_VARIANT
from config_reader import load_config, apply_config


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

        self._config = dict(VARIANTS[variant_name])  # Copy so overlay is safe
        self._menus_dir = menus_dir

        # Load user config and overlay onto hardware defaults
        user_config = load_config("/config.txt")
        if user_config:
            apply_config(self._config, user_config)
            print("User config loaded ({} settings)".format(len(user_config)))

        if start_menu is None:
            start_menu = self._config.get("start_menu", "base.menu")
        self._start_menu = start_menu
        print("AAC Device — variant:", self._config["name"])

        # FULL_POWER — enable first so rail settles during other init
        self._full_power = None
        if self._config.get("full_power_pin"):
            self._init_full_power()

        # Emergency push fast path: minimal DAC init, skip Peripherals
        emergency_held = self._check_emergency_pin()
        self._emergency_audio = None  # Holds I2S if emergency played

        if emergency_held and self._config["sound_system"] == "FRUITJAM_DAC":
            self._play_emergency_sound()

        # Fruit Jam Peripherals (full init for normal operation)
        self._peripherals = None
        if self._config["sound_system"] == "FRUITJAM_DAC":
            self._init_fruitjam_peripherals()

        # Deferred imports — after emergency sound finishes (if any)
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

        # Display — pass shared SPI bus if SD card shares it
        spi = self.storage.spi if self._config.get("sd_shares_display_spi") else None
        self.display = DisplayManager(self._config, spi=spi)

        # Shared I2C bus (touch + codec may share it)
        # Skip if Peripherals owns it or display is I2C (SSD1306)
        self._i2c = None
        if self._peripherals is None and self._config.get("display_type") != "SSD1306":
            scl = _pin(self._config.get("i2c_scl"))
            sda = _pin(self._config.get("i2c_sda"))
            if scl and sda:
                self._i2c = busio.I2C(scl, sda, frequency=self._config.get("i2c_freq", 400_000))
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
            config=self._config,
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

    def _play_emergency_sound(self):
        """Play emergency sound via minimal direct DAC init (~0.2s).

        Bypasses the full Peripherals import (1.3s) by directly
        configuring MCLK, TLV320 DAC, and I2S. Blocks until done.
        """
        cfg = self._config
        sound_file = cfg.get("emergency_push_sound")
        if not sound_file:
            return

        try:
            import pwmio
            import busio
            import audiobusio
            import audiomp3
            import adafruit_tlv320

            # MCLK — 15 MHz master clock for DAC PLL
            mclk = pwmio.PWMOut(board.I2S_MCLK,
                                frequency=15_000_000, duty_cycle=2**15)

            # DAC — minimal I2C config
            i2c = board.I2C()
            dac = adafruit_tlv320.TLV320DAC3100(i2c)
            sample_rate = cfg.get("codec_sample_rate", 22050)
            dac.configure_clocks(sample_rate=sample_rate,
                                 bit_depth=16, mclk_freq=15_000_000)
            dac.speaker_output = True
            dac.dac_volume = cfg.get("dac_volume", -10)
            dac.speaker_volume = cfg.get("speaker_volume", 0)
            dac.speaker_gain = cfg.get("speaker_gain", 24)

            # I2S output
            audio = audiobusio.I2SOut(board.I2S_BCLK,
                                      board.I2S_WS, board.I2S_DIN)

            # Play
            f = open(sound_file, "rb")
            mp3 = audiomp3.MP3Decoder(f)
            audio.play(mp3)
            print("EMERGENCY: playing", sound_file)
            while audio.playing:
                time.sleep(0.01)
            f.close()
            print("EMERGENCY: done")

            # Clean up so Peripherals can claim these pins
            audio.deinit()
            mclk.deinit()
            i2c.deinit()
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

        # Encoder is repurposed as a language switcher on touch-input
        # variants (CYD_PLUS). Skip menu-highlight wiring entirely so
        # encoder rotation only drives the language overlay, not menu nav.
        self._has_encoder_nav = False
        self._last_shown_index = -1
        self._emergency_hold_enabled = self._config.get("emergency_hold_enabled", True)
        self._emergency_hold_time = self._config.get("emergency_hold_seconds", 3)
        self._hold_start = 0
        self._hold_triggered = False

        # Language switcher overlay — encoder rotation enters; encoder
        # click commits; 10s no-activity reverts to whatever menu was
        # active before the rotation started.
        self._lang_active = False
        self._lang_index = 0
        self._lang_timeout = 0
        self._lang_revert_menu = None
        try:
            from stim_games.multi_lingual import LANGUAGES as _L
            self._LANGUAGES = _L
        except Exception as e:
            print("Lang switcher: multi_lingual import failed:", e)
            self._LANGUAGES = ()
        enc = getattr(self.input, "_encoder", None)
        self._lang_last_pos = enc.position if enc is not None else 0
        self._lang_flip = getattr(self.input, "_encoder_flip", 1)

        # Config-driven subprogram mode: `mode = stim_games/foo.py` in
        # config.txt causes the device to boot into that subprogram
        # after hardware/menu init finishes. When the subprogram exits,
        # control drops through to the menu loop (start_menu).
        mode = self._config.get("mode")
        if mode and isinstance(mode, str) and mode.endswith(".py"):
            print("Config mode: launching subprogram", mode)
            self._launch_subprogram(mode)
            # After subprogram exit, repaint the menu before looping
            try:
                self.display.restore_background()
                self._update_display()
                self._last_shown_index = -1
            except Exception as e:
                print("Post-subprogram redraw error:", e)
            # Resync encoder position so the picker doesn't fire on stale delta
            enc = getattr(self.input, "_encoder", None)
            if enc is not None:
                self._lang_last_pos = enc.position

        wake_grace = self._config.get("wake_ignore_seconds", 1.0)
        wake_until = 0

        while True:
            # Sample encoder-button state BEFORE poll() consumes it, so
            # we can attribute the upcoming press to encoder vs. touch.
            enc_btn_down = bool(getattr(self.input, "encoder_button_held", False))

            button = self.input.poll()
            if button is not None:
                self.sleep.activity()
                if time.monotonic() >= wake_until:
                    if self._lang_active and enc_btn_down:
                        # Picker overlay is up and the press came from the
                        # encoder button → commit the highlighted language.
                        self._lang_commit(self._lang_index)
                        self._lang_active = False
                    elif enc_btn_down:
                        # No overlay active → cycle directly to the next
                        # language. Lets a single encoder/BUTTON3 tap rotate
                        # languages even when encoder rotation isn't wired.
                        self._lang_cycle_next()
                    else:
                        self._handle_press(button)
            else:
                woke = self.sleep.check()
                if woke:
                    wake_until = time.monotonic() + wake_grace
                    print("Wake grace: ignoring input for {}s".format(wake_grace))
            if self._emergency_hold_enabled:
                self._check_emergency_hold()
            self._check_lang_encoder()
            time.sleep(0.01)

    def _check_lang_encoder(self):
        """Encoder rotation enters/cycles the language picker overlay.

        After 10s of no rotation/press the overlay reverts and the
        previous menu is restored.
        """
        if not self._LANGUAGES:
            return
        enc = getattr(self.input, "_encoder", None)
        if enc is None:
            return
        now = time.monotonic()
        pos = enc.position
        delta = pos - self._lang_last_pos
        if delta != 0:
            self._lang_last_pos = pos
            if not self._lang_active:
                # Entering: remember menu to revert to, seed index from it.
                curr = None
                if self._menu_stack is not None:
                    stack = getattr(self._menu_stack, "_stack", None)
                    if stack:
                        curr = stack[-1]
                self._lang_revert_menu = curr
                self._lang_index = 0
                for i, lang in enumerate(self._LANGUAGES):
                    if lang[3] == curr:
                        self._lang_index = i
                        break
                self._lang_active = True
            self._lang_index = (self._lang_index - delta * self._lang_flip) % len(self._LANGUAGES)
            self._lang_show()
            self._lang_timeout = now + 10.0
            self.sleep.activity()
        elif self._lang_active and now >= self._lang_timeout:
            self._lang_active = False
            self.display.restore_background()
            print("Lang switcher: timeout — reverted")

    def _lang_show(self):
        _code, en_name, native_name, _menu = self._LANGUAGES[self._lang_index]
        path = "/lang_images/lang_{}.bmp".format(_code)
        if self.storage is not None:
            path = self.storage.resolve_path(path)
        try:
            self.display.show_image(path)
        except Exception as e:
            print("Lang switcher: image error ({}):".format(e), path)
            try:
                self.display.set_text("{} / {}".format(en_name, native_name))
            except Exception:
                pass
        print("Lang switcher: highlight", en_name)

    def _lang_cycle_next(self):
        """Advance directly to the next language. Used when the user taps
        the encoder click (BUTTON3) without first turning the encoder."""
        n = len(self._LANGUAGES)
        if n == 0:
            return
        curr_menu = None
        if self._menu_stack is not None:
            stack = getattr(self._menu_stack, "_stack", None)
            if stack:
                curr_menu = stack[-1]
        curr = 0
        for i, lang in enumerate(self._LANGUAGES):
            if lang[3] == curr_menu:
                curr = i
                break
        nxt = (curr + 1) % n
        en_name = self._LANGUAGES[nxt][1]
        print("Lang switcher: cycle ->", en_name)
        self._lang_commit(nxt)

    def _lang_commit(self, index):
        _code, en_name, _native, menu_file = self._LANGUAGES[index]
        print("Lang switcher: commit", en_name, "->", menu_file)
        self.display.restore_background()
        from menu_parser import MenuStack
        for attempt in range(3):
            try:
                self._menu_stack = MenuStack(
                    self._menus_dir, menu_file, storage=self.storage)
                self._build_grid()
                self._update_display()
                if hasattr(self, "_reset_selection"):
                    self._reset_selection()
                print("Lang switcher: loaded", menu_file)
                return
            except Exception as e:
                print("Lang switcher: load attempt {} failed: {}".format(
                    attempt + 1, e))
                time.sleep(0.1)
        print("Lang switcher: gave up loading", menu_file)

    def _check_emergency_hold(self):
        """Check if encoder button is held for emergency_hold_seconds.

        Plays the emergency sound if held long enough. Resets when released.
        """
        held = self.input.encoder_button_held
        if held:
            if self._hold_start == 0:
                self._hold_start = time.monotonic()
            elif not self._hold_triggered:
                elapsed = time.monotonic() - self._hold_start
                if elapsed >= self._emergency_hold_time:
                    self._hold_triggered = True
                    print("EMERGENCY: hold triggered ({:.0f}s)".format(elapsed))
                    sound = self._config.get("emergency_push_sound")
                    if sound:
                        self.display.set_text("EMERGENCY")
                        self.set_status("playing")
                        self.audio.play(sound)
                        self.set_status("ready")
        else:
            self._hold_start = 0
            self._hold_triggered = False

    def _get_item_text(self, index):
        """Get text_description for a grid item by index, with wrapping."""
        if not self._grid:
            return ""
        idx = index % len(self._grid)
        item = self._grid[idx]
        if item:
            return item.get("text_description", item.get("label", ""))
        return ""

    def _update_text_for_index(self, index):
        """Update display text with prev/current/next items."""
        if index == self._last_shown_index:
            return
        self._last_shown_index = index
        if not self._grid:
            return
        n = len(self._grid)
        prev_text = self._get_item_text((index - 1) % n)
        curr_text = self._get_item_text(index)
        next_text = self._get_item_text((index + 1) % n)

        if hasattr(self.display, 'set_text_lines'):
            self.display.set_text_lines(prev_text, curr_text, next_text)
        else:
            self.display.set_text(curr_text)

    def _reset_selection(self):
        """Reset encoder selection to first item and update text."""
        if self._has_encoder_nav:
            self.input._selected_index = 0
            if hasattr(self.input, '_encoder') and self.input._encoder:
                self.input._encoder.position = 0
                self.input._last_encoder_pos = 0
        self._last_shown_index = -1  # Force text refresh
        # Force full text update for new menu
        self._last_shown_index = -1
        self._update_text_for_index(0)
        self._last_shown_index = 0
        # Force display refresh
        try:
            self.display.display.refresh()
        except:
            pass

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
        # Show the pressed item's text on screen
        text = item.get("text_description", item.get("label", ""))
        self.display.set_text(text)
        # Hide highlight during image/sound playback
        self.display.set_highlight(-1)
        self.set_status("playing")

        press_start = time.monotonic()
        try:
            nav = self.action.execute(item)
        except Exception as e:
            print("Action error:", e)
            self.set_status("error")
            time.sleep(0.5)
            self.set_status("ready")
            self._update_display()
            return

        # Keep zoom image visible for at least 3 seconds (only if zoom shown)
        has_nav = "submenu" in item or "list" in item or "back" in item
        if not has_nav and item.get("image") and self.action._zoom_enabled:
            elapsed = time.monotonic() - press_start
            if elapsed < 3:
                time.sleep(3 - elapsed)

        self.set_status("ready")

        # Reset button latch after playback (V1 pattern)
        if hasattr(self.input, 'reset_button_latch'):
            self.input.reset_button_latch()

        # Handle navigation
        if nav is None:
            # Restore menu background after zoom image
            self.display.restore_background()
            # Restore highlight
            if self._has_encoder_nav:
                self.display.set_highlight(self.input.selected_index)
            return
        if nav == "back":
            if self._menu_stack.back():
                self._build_grid()
                self.display.restore_background()
                self._update_display()
                self._reset_selection()
                if self._has_encoder_nav:
                    self.display.set_highlight(self.input.selected_index)
                print("Back to:", self._menu_stack.name)
            else:
                print("Already at root menu")
        elif nav.startswith("submenu:") or nav.startswith("list:"):
            menu_file = nav.split(":", 1)[1]
            try:
                self._menu_stack.navigate(menu_file)
                self._build_grid()
                self.display.restore_background()
                self._update_display()
                self._reset_selection()
                if self._has_encoder_nav:
                    self.display.set_highlight(self.input.selected_index)
                print("Navigated to:", self._menu_stack.name)
            except Exception as e:
                print("Navigation error:", e)
        elif nav.startswith("subprogram:"):
            # Launch a Python subprogram (stim game, helper, etc.)
            # Menu stack is NOT touched — on return we redraw the
            # current menu so the user lands back where they launched.
            target = nav.split(":", 1)[1]
            self._launch_subprogram(target)
            try:
                self.display.restore_background()
                self._update_display()
                self._last_shown_index = -1
                if self._has_encoder_nav:
                    self.display.set_highlight(self.input.selected_index)
                    self._update_text_for_index(self.input.selected_index)
            except Exception as e:
                print("Menu redraw error:", e)

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
        """Update the display background for the current menu.

        Stores the last working background path so it can be restored
        after zoom images without re-parsing the menu header.
        """
        bg = self._menu_stack.header.get("background")
        if bg:
            resolved = self._resolve_path(bg)
            try:
                self.display.set_background(resolved)
                self._current_bg = resolved  # Remember working path
            except Exception as e:
                print("Background load error:", e)
                # Try the stored fallback
                if hasattr(self, '_current_bg') and self._current_bg:
                    try:
                        self.display.set_background(self._current_bg)
                    except:
                        pass

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

    def _launch_subprogram(self, target):
        """Load and run a Python subprogram (e.g. a stim game).

        `target` is a path-like reference: "stim_games/bubble_pop.py",
        "stim_games.bubble_pop", or any module importable from /lib.

        An optional sidecar config file with the same stem and a .cfg
        extension is loaded and passed to the subprogram. For example,
        `stim_games/aac_trainer.py` will look for
        `stim_games/aac_trainer.cfg`.

        Hardware (display, audio, input, pixel, storage) stays initialized
        — the subprogram receives `self` as its `machine` reference and
        is expected to leave the device in a usable state on exit.
        """
        from stim_games.subprogram import launch_subprogram
        from stim_games.game_config import load as load_game_cfg

        cfg = None
        # Locate sidecar .cfg next to the .py file
        cfg_path = None
        if target.endswith(".py"):
            cfg_path = target[:-3] + ".cfg"
            # Allow "stim_games.foo" dotted form too
            cfg_path = cfg_path.replace(".", "/") if "/" not in cfg_path else cfg_path
        if cfg_path:
            resolved = self._resolve_path(cfg_path)
            try:
                header, sections = load_game_cfg(resolved)
                if header or sections:
                    cfg = {"header": header, "sections": sections}
                    print("Loaded subprogram config:", resolved)
            except Exception as e:  # noqa: BLE001
                print("Subprogram config load skipped:", e)

        self.set_status("playing")
        try:
            launch_subprogram(self, target, config=cfg)
        finally:
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
        self._status = state

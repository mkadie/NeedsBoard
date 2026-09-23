"""Audio playback abstraction for AAC device.

Supports ES8311 codec, direct I2S output, and Fruit Jam TLV320DAC3100.
"""

import time
import audiomp3
import board


def _pin(name):
    """Resolve pin name string to board pin. Returns None if name is None."""
    if name is None:
        return None
    return getattr(board, name)


class AudioPlayer:
    """Plays MP3 files through ES8311, direct I2S, or Fruit Jam DAC."""

    def __init__(self, config, i2c=None, storage=None, peripherals=None):
        """Initialize audio hardware from config dict.

        Args:
            config: Hardware config dictionary.
            i2c: Shared I2C bus (required for ES8311 sound system).
            storage: StorageManager for SD-first path resolution.
            peripherals: Fruit Jam Peripherals object (for FRUITJAM_DAC).
        """
        self._config = config
        self._codec = None
        self._amp_en = None
        self._storage = storage
        self._peripherals = peripherals
        self._current_rate = config["codec_sample_rate"]
        self._volume = config["volume"]
        self._sound_system = config["sound_system"]
        self._playback_speed = config.get("playback_speed", 100)

        # Amplifier / peripheral reset. Held HIGH the chip runs; pulled LOW
        # it is held in reset, which is what stops the speaker hiss and the
        # idle current it draws. Claimed here rather than in SleepManager so
        # one object owns the pin -- sleep, idle timeout and playback all
        # have to agree about it.
        self._periph_reset_pin_name = config.get("periph_reset_pin")
        self._periph_reset = None
        self._periph_idle_timeout = config.get("periph_idle_timeout", 15)
        self._periph_idle = False
        self._last_play_end = time.monotonic()

        if self._sound_system == "NONE":
            # Silent build: board has no reachable codec (e.g. a bring-up board
            # whose I2C pull-ups aren't fitted yet). Everything else — display,
            # menus, encoder — still runs; play() becomes a no-op.
            self._audio = None
            print("Audio: DISABLED (sound_system = NONE) — device will be silent")
        elif self._sound_system == "FRUITJAM_DAC":
            self._init_fruitjam_dac(config, peripherals)
        else:
            self._init_i2s(config, i2c)

    def _init_fruitjam_dac(self, config, peripherals):
        """Initialize Fruit Jam TLV320DAC3100 audio via Peripherals.

        Reads volume/gain settings for both speaker and headphone paths from
        config (with sane loud-but-safe defaults), then routes to the chosen
        starting output. Optional headset jack detection auto-routes between
        speaker and headphone on plug/unplug.

        Important quirk: setting `peripherals.audio_output` runs the
        underlying TLV320DAC3100 driver's "quickstart" presets, which
        overwrite dac_volume / speaker_volume / speaker_gain /
        headphone_volume / headphone_left/right_gain. We re-apply our values
        after every route change. See `set_audio_route()` and
        `_apply_fruitjam_levels()`.
        """
        if peripherals is None:
            raise ValueError("FRUITJAM_DAC requires Peripherals object")

        # Cached level config — applied after every audio_output change.
        self._dac_volume = config.get("dac_volume", -10)
        self._speaker_volume = config.get("speaker_volume", 0)
        self._speaker_gain = config.get("speaker_gain", 24)
        self._headphone_volume = config.get("headphone_volume", 0)
        self._headphone_left_gain = config.get("headphone_left_gain", 9)
        self._headphone_right_gain = config.get("headphone_right_gain", 9)

        # Optional headset jack auto-detect (TLV320DAC3100 hardware feature)
        self._headset_detect_enabled = config.get(
            "headset_detect_enabled", False)
        self._hp_poll_interval = config.get("headset_poll_interval", 0.5)
        self._hp_debounce = config.get("headset_debounce", 1.0)
        self._last_hp_poll = 0.0
        self._hp_pending_status = 0
        self._hp_pending_since = 0.0
        self._last_hp_status = 0

        if self._headset_detect_enabled:
            try:
                self._last_hp_status = self._arm_headset_detect(peripherals.dac)
                self._hp_pending_status = self._last_hp_status
            except Exception as e:
                print("headset detect init err:", type(e).__name__, e)

        # Initial route. When jack detection is on, what the codec actually
        # reports wins: audio_output_default is a starting guess, and
        # honouring it over a live reading meant booting with an empty jack
        # routed to the headphone amp -- silent, with no plug event coming
        # to correct it, because the poll only ever reacts to a *change*.
        if self._headset_detect_enabled:
            default_route = self._wanted_route_from(self._last_hp_status)
        else:
            default_route = config.get("audio_output_default", "speaker")
        self.audio_route = None  # set_audio_route fills it in
        self.set_audio_route(default_route)
        self._audio = peripherals.audio
        print(
            "Fruit Jam DAC ready: route=%s, dac=%+d, spk_vol=%+d, "
            "spk_gain=%+d, hp_vol=%+d, hp_gain=%d/%d, hp_status=%d" % (
                self.audio_route,
                self._dac_volume, self._speaker_volume, self._speaker_gain,
                self._headphone_volume, self._headphone_left_gain,
                self._headphone_right_gain, self._last_hp_status))

    def _claim_periph_reset(self):
        """Claim the peripheral-reset pin, driven to its active (HIGH) level."""
        if self._periph_reset is not None or not self._periph_reset_pin_name:
            return
        import digitalio

        try:
            self._periph_reset = digitalio.DigitalInOut(
                _pin(self._periph_reset_pin_name))
            self._periph_reset.switch_to_output(value=True)
        except Exception as e:
            print("Audio: PERIPH_RESET unavailable:", type(e).__name__, e)
            self._periph_reset = None

    def amp_idle(self):
        """Hold the audio peripheral in reset.

        This is what actually silences the speaker between sounds. Leaving
        it running hisses continuously and draws current for nothing, which
        matters most in sleep -- where the whole point is to stop drawing.
        """
        self._claim_periph_reset()
        if self._periph_reset is None or self._periph_idle:
            return False
        self._periph_reset.value = False
        self._periph_idle = True
        print("Audio: amp held in reset (idle)")
        return True

    def amp_wake(self):
        """Release the peripheral from reset and reprogram it.

        Coming out of reset the codec is at power-on defaults, so the route
        and levels have to be re-applied or the next sound plays to the
        wrong place -- or nowhere.
        """
        self._claim_periph_reset()
        if self._periph_reset is None or not self._periph_idle:
            return False
        self._periph_reset.value = True
        time.sleep(0.05)              # let the part come out of reset
        self._periph_idle = False
        print("Audio: amp released from reset")
        if self._sound_system == "FRUITJAM_DAC":
            self.reinit_after_wake()
        return True

    def poll_amp_idle(self):
        """Drop the amp into reset once it has been quiet long enough.

        Called from the main loop. Does nothing while audio is playing, or
        if the board has no reset pin wired.
        """
        if self._periph_idle or not self._periph_reset_pin_name:
            return False
        if self._periph_idle_timeout <= 0:
            return False
        if self._audio is not None and self._audio.playing:
            self._last_play_end = time.monotonic()
            return False
        if time.monotonic() - self._last_play_end < self._periph_idle_timeout:
            return False
        return self.amp_idle()

    def prepare_for_sleep(self):
        """Called before the device sleeps: silence the amp."""
        return self.amp_idle()

    def _apply_fruitjam_levels(self):
        """Restore our cached level settings on the TLV320DAC3100.

        The Adafruit Peripherals.audio_output setter runs "quickstart"
        presets that clobber: dac_volume, speaker_volume, speaker_gain,
        headphone_volume, headphone_left/right_gain. Call this after every
        audio_output write so our intended levels actually stick.
        """
        if self._sound_system != "FRUITJAM_DAC":
            return
        d = self._peripherals.dac
        d.dac_volume = self._dac_volume
        d.speaker_volume = self._speaker_volume
        d.speaker_gain = self._speaker_gain
        d.headphone_volume = self._headphone_volume
        d.headphone_left_gain = self._headphone_left_gain
        d.headphone_right_gain = self._headphone_right_gain

    def set_audio_route(self, route):
        """Switch audio output between 'speaker' and 'headphone' and
        re-apply our level settings (the audio_output setter clobbers them).
        No-op on non-Fruit-Jam variants."""
        if self._sound_system != "FRUITJAM_DAC":
            return
        if route not in ("speaker", "headphone"):
            raise ValueError("audio route must be 'speaker' or 'headphone'")
        self._peripherals.audio_output = route
        self._apply_fruitjam_levels()
        self.audio_route = route

    @staticmethod
    def _wanted_route_from(status):
        """Map TLV320DAC3100 headset_status to a route.

        0 = no headset detected -> speaker.
        1 = headphone-no-mic, 3 = headset+mic -> headphone.
        """
        return "speaker" if status == 0 else "headphone"

    def _arm_headset_detect(self, dac):
        """Enable jack detection on the codec and return a settled reading."""
        # detect_debounce=4 -> 256 ms hardware debounce
        dac.set_headset_detect(True, detect_debounce=4, button_debounce=2)
        time.sleep(0.2)
        return self._settle_headset_status(dac)

    def reinit_after_wake(self):
        """Reprogram the codec after a sleep, and re-pick the route.

        Sleep can cut the rail the codec sits on, and on battery that rail
        is its only supply -- so it comes back at power-on defaults with
        every register lost. Software still believed it was on the speaker,
        and because set_audio_route() only reprograms the chip when its own
        value CHANGES, nothing was ever re-applied. The device woke wired to
        whatever the defaults were and ignored the socket from then on.

        So this re-applies everything unconditionally rather than trusting
        the cached state: clocks, jack detection, route and levels. It is
        cheap and idempotent, and it is correct whether or not the codec
        actually lost power -- which differs between USB and battery, and is
        not worth trying to detect.
        """
        if self._sound_system != "FRUITJAM_DAC":
            return False
        # Writes go nowhere while the part is held in reset.
        if self._periph_reset is not None and self._periph_idle:
            self._periph_reset.value = True
            time.sleep(0.05)
            self._periph_idle = False
        dac = self._peripherals.dac

        try:
            dac.configure_clocks(sample_rate=self._current_rate, bit_depth=16)
        except Exception as e:
            print("Audio: clock reconfigure failed:", type(e).__name__, e)

        status = 0
        if self._headset_detect_enabled:
            try:
                status = self._arm_headset_detect(dac)
            except Exception as e:
                print("Audio: jack re-arm failed:", type(e).__name__, e)
            self._last_hp_status = status
            self._hp_pending_status = status
            self._hp_pending_since = time.monotonic()
            self._last_hp_poll = 0.0
            wanted = self._wanted_route_from(status)
        else:
            wanted = self.audio_route or self._config.get(
                "audio_output_default", "speaker")

        # Drop the cached value so set_audio_route always reaches the chip.
        # Skipping this is what left the codec unprogrammed after a wake.
        self.audio_route = None
        try:
            self.set_audio_route(wanted)
            print("Audio: codec reprogrammed after wake — status=%d route=%s"
                  % (status, wanted))
        except Exception as e:
            print("Audio: route restore failed:", type(e).__name__, e)
            return False
        return True

    def resync_headset_detect(self):
        """Re-arm jack detection and re-pick the route after waking.

        set_headset_detect() was only ever called once, at startup, and the
        codec's detect configuration does not survive a sleep cycle on every
        board. Waking could leave the detector stuck on whatever it last
        reported: the route then settled on that value and the socket stopped
        having any effect at all -- plugging in, playing, and unplugging
        changed nothing.

        Re-arming costs a fraction of a second on wake and makes the jack
        behave the same before and after sleep.
        """
        if not self._headset_detect_enabled:
            return False
        if self._sound_system != "FRUITJAM_DAC":
            return False
        try:
            status = self._arm_headset_detect(self._peripherals.dac)
        except Exception as e:
            print("Audio: jack re-arm failed:", type(e).__name__, e)
            return False

        # Reset the debounce state too, so the poll judges the fresh reading
        # rather than comparing it against whatever was pending before sleep.
        self._last_hp_status = status
        self._hp_pending_status = status
        self._hp_pending_since = time.monotonic()
        self._last_hp_poll = 0.0

        wanted = self._wanted_route_from(status)
        if wanted != self.audio_route:
            self.set_audio_route(wanted)
            print("Audio: jack re-armed after wake — status=%d -> %s"
                  % (status, wanted))
        else:
            print("Audio: jack re-armed after wake — status=%d, route %s"
                  % (status, self.audio_route))
        return True

    def _settle_headset_status(self, dac, timeout=1.5, need=5):
        """Read the jack until the value holds still, or report empty.

        A single reading taken just after enabling detection is not
        trustworthy: the detector can briefly report a plug that is not
        there, and the device then boots routed to a headphone amp with
        nothing in the socket -- silent, and it stays that way until a real
        plug event happens to correct it.

        Requiring the reading to repeat costs a fraction of a second at
        startup. If it will not settle, report 0 (empty): erring towards the
        onboard speaker is audible in the room, while erring towards the
        jack is silence.
        """
        stable = 0
        value = 0
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            reading = dac.headset_status
            if reading == value:
                stable += 1
                if stable >= need:
                    return value
            else:
                value = reading
                stable = 1
            time.sleep(0.08)
        print("Audio: jack reading unsettled — assuming nothing plugged in")
        return 0

    def poll_headset_detect(self):
        """Poll the 3.5 mm jack and auto-route on a stable plug change.

        Called from the main loop. Debounces the codec's report so the
        oscillation seen during plug insertion (status flipping 0/3) doesn't
        trigger spurious route changes. Returns True if the route changed
        this call. No-op when headset detection is disabled or while audio
        is currently playing (a route swap can't safely glitch a
        live stream).
        """
        if not self._headset_detect_enabled:
            return False
        if self._sound_system != "FRUITJAM_DAC":
            return False
        # Nothing to read while the part is held in reset -- the I2C access
        # just errors ("No such device") once per poll. Detection resumes
        # when the amp wakes, and reinit_after_wake() re-reads the jack
        # before the next sound plays, so the route is still right.
        if self._periph_idle:
            return False
        now = time.monotonic()
        if now - self._last_hp_poll < self._hp_poll_interval:
            return False
        self._last_hp_poll = now
        try:
            hps = self._peripherals.dac.headset_status
        except Exception as e:
            print("headset_status read err:", type(e).__name__, e)
            return False
        # Settle the reading first — the codec chatters between 0 and 3
        # while a plug is going in.
        if hps != self._hp_pending_status:
            self._hp_pending_status = hps
            self._hp_pending_since = now
            return False
        if (now - self._hp_pending_since) < self._hp_debounce:
            return False
        self._last_hp_status = self._hp_pending_status

        # Reconcile the route against the settled status on every poll, not
        # only on a transition. Acting on transitions alone lost the change
        # for good whenever it landed while a sound was playing: the status
        # was marked as seen, the route swap was skipped, and no further
        # event was coming to retry it. Comparing state instead of edges
        # makes this self-healing — any disagreement gets corrected as soon
        # as the codec is idle.
        wanted = self._wanted_route_from(self._last_hp_status)
        if wanted != self.audio_route and not self._audio.playing:
            self.set_audio_route(wanted)
            print("auto route: status=%d -> %s" %
                  (self._last_hp_status, wanted))
            return True
        return False

    def _init_i2s(self, config, i2c):
        """Initialize ES8311 codec or direct I2S output."""
        import audiobusio

        # Amplifier enable pin
        if config.get("amp_en_pin"):
            import digitalio
            self._amp_en = digitalio.DigitalInOut(_pin(config["amp_en_pin"]))
            self._amp_en.direction = digitalio.Direction.OUTPUT
            self._amp_en.value = not config.get("amp_en_active_low", True)

        # ES8311 codec initialization
        if config["sound_system"] == "ES8311":
            from es8311 import ES8311
            self._codec = ES8311(i2c)
            self._codec.init(sample_rate=self._current_rate, bits=16)
            self._codec.set_volume(self._volume)
            self._codec.mute(False)

        # I2S audio output
        mclk = _pin(config.get("i2s_mclk"))
        kwargs = {}
        if mclk is not None:
            kwargs["main_clock"] = mclk

        self._audio = audiobusio.I2SOut(
            _pin(config["i2s_bclk"]),
            _pin(config["i2s_ws"]),
            _pin(config["i2s_dout"]),
            **kwargs,
        )

    def play(self, sound_file):
        """Play an MP3 or WAV file. Blocks until playback finishes.

        Checks SD card first via StorageManager, falls back to flash.

        Args:
            sound_file: Path to the sound file (.mp3 or .wav).
        """
        if self._audio is None:                  # sound_system = NONE
            print("Audio: (silent) would play", sound_file)
            return

        # Resolve path: SD card first, then flash
        if self._storage:
            sound_file = self._storage.resolve_path(sound_file)

        print("Audio: playing", sound_file)
        # The amp may be sitting in reset from the idle timeout or a sleep.
        self.amp_wake()
        f = None
        try:
            f = open(sound_file, "rb")

            if sound_file.lower().endswith(".wav"):
                import audiocore
                source = audiocore.WaveFile(f)
                native_rate = source.sample_rate
            else:
                source = audiomp3.MP3Decoder(f)
                native_rate = source.sample_rate

            # Adjust sample rate for playback speed
            target_rate = int(native_rate * self._playback_speed / 100)
            if target_rate != native_rate:
                source.sample_rate = target_rate
                print("Audio: rate={} -> {} ({}%)".format(
                    native_rate, target_rate, self._playback_speed))
            else:
                print("Audio: rate=", native_rate)

            # Switch codec sample rate if needed
            if self._codec:
                if target_rate != self._current_rate:
                    print("Switching codec to", target_rate, "Hz")
                    self._audio.stop()
                    self._codec.init(sample_rate=target_rate, bits=16)
                    self._codec.set_volume(self._volume)
                    self._codec.mute(False)
                    self._current_rate = target_rate

            time.sleep(0.1)  # Dead time before play (some DACs need settling)
            self._audio.play(source)
            while self._audio.playing:
                time.sleep(0.01)
            time.sleep(0.05)  # Let last buffer drain
            self._audio.stop()
            self._last_play_end = time.monotonic()
            print("Audio: done")
        except Exception as e:
            print("Audio: ERROR:", e)
        finally:
            if f:
                f.close()

    @property
    def playing(self):
        """True if audio is currently playing."""
        if self._audio is None:                  # sound_system = NONE
            return False
        return self._audio.playing

    def stop(self):
        """Stop current playback."""
        if self._audio is None:                  # sound_system = NONE
            return
        self._audio.stop()

    def set_playback_speed(self, speed):
        """Set playback speed as percentage (50=half speed, 100=normal, 150=fast)."""
        self._playback_speed = max(25, min(200, speed))

    def set_volume(self, volume):
        """Set volume (0-100). Only effective with ES8311 codec."""
        self._volume = max(0, min(100, volume))
        if self._codec:
            self._codec.set_volume(self._volume)

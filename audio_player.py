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

        if self._sound_system == "FRUITJAM_DAC":
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
                # detect_debounce=4 -> 256 ms hardware debounce
                peripherals.dac.set_headset_detect(
                    True, detect_debounce=4, button_debounce=2)
                time.sleep(0.5)
                self._last_hp_status = peripherals.dac.headset_status
                self._hp_pending_status = self._last_hp_status
            except Exception as e:
                print("headset detect init err:", type(e).__name__, e)

        # Initial route: explicit config, otherwise auto from plug detection.
        default_route = config.get(
            "audio_output_default",
            self._wanted_route_from(self._last_hp_status)
            if self._headset_detect_enabled else "speaker",
        )
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
        now = time.monotonic()
        if now - self._last_hp_poll < self._hp_poll_interval:
            return False
        self._last_hp_poll = now
        try:
            hps = self._peripherals.dac.headset_status
        except Exception as e:
            print("headset_status read err:", type(e).__name__, e)
            return False
        if hps != self._hp_pending_status:
            self._hp_pending_status = hps
            self._hp_pending_since = now
            return False
        if (self._hp_pending_status != self._last_hp_status
                and (now - self._hp_pending_since) >= self._hp_debounce):
            self._last_hp_status = self._hp_pending_status
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
        # Resolve path: SD card first, then flash
        if self._storage:
            sound_file = self._storage.resolve_path(sound_file)

        print("Audio: playing", sound_file)
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
            print("Audio: done")
        except Exception as e:
            print("Audio: ERROR:", e)
        finally:
            if f:
                f.close()

    @property
    def playing(self):
        """True if audio is currently playing."""
        return self._audio.playing

    def stop(self):
        """Stop current playback."""
        self._audio.stop()

    def set_playback_speed(self, speed):
        """Set playback speed as percentage (50=half speed, 100=normal, 150=fast)."""
        self._playback_speed = max(25, min(200, speed))

    def set_volume(self, volume):
        """Set volume (0-100). Only effective with ES8311 codec."""
        self._volume = max(0, min(100, volume))
        if self._codec:
            self._codec.set_volume(self._volume)

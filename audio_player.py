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
        """Initialize Fruit Jam TLV320DAC3100 audio via Peripherals."""
        if peripherals is None:
            raise ValueError("FRUITJAM_DAC requires Peripherals object")

        peripherals.audio_output = "speaker"
        peripherals.dac.dac_volume = config.get("dac_volume", -10)
        peripherals.dac.speaker_volume = config.get("speaker_volume", 0)
        peripherals.dac.speaker_gain = config.get("speaker_gain", 24)
        self._audio = peripherals.audio
        print("Fruit Jam DAC ready (dac={} spk={} gain={})".format(
            config.get("dac_volume", -10),
            config.get("speaker_volume", 0),
            config.get("speaker_gain", 24)))

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

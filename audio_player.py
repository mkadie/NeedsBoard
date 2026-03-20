"""Audio playback abstraction for AAC device.

Supports ES8311 codec and direct I2S output.
"""

import time
import audiomp3
import audiobusio
import board


def _pin(name):
    """Resolve pin name string to board pin. Returns None if name is None."""
    if name is None:
        return None
    return getattr(board, name)


class AudioPlayer:
    """Plays MP3 files through either an ES8311 codec or direct I2S."""

    def __init__(self, config, i2c=None):
        """Initialize audio hardware from config dict.

        Args:
            config: Hardware config dictionary.
            i2c: Shared I2C bus (required for ES8311 sound system).
        """
        self._config = config
        self._codec = None
        self._amp_en = None
        self._current_rate = config["codec_sample_rate"]
        self._volume = config["volume"]

        # Amplifier enable pin
        if config.get("amp_en_pin"):
            import digitalio
            self._amp_en = digitalio.DigitalInOut(_pin(config["amp_en_pin"]))
            self._amp_en.direction = digitalio.Direction.OUTPUT
            # Enable amplifier
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
        """Play an MP3 file. Blocks until playback finishes.

        Args:
            sound_file: Path to the MP3 file.
        """
        f = None
        try:
            f = open(sound_file, "rb")
            mp3 = audiomp3.MP3Decoder(f)

            # Switch codec sample rate if needed
            if self._codec:
                mp3_rate = mp3.sample_rate
                if mp3_rate != self._current_rate:
                    print("Switching codec to", mp3_rate, "Hz")
                    self._audio.stop()
                    self._codec.init(sample_rate=mp3_rate, bits=16)
                    self._codec.set_volume(self._volume)
                    self._codec.mute(False)
                    self._current_rate = mp3_rate

            self._audio.play(mp3)
            while self._audio.playing:
                time.sleep(0.01)
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

    def set_volume(self, volume):
        """Set volume (0-100). Only effective with ES8311 codec."""
        self._volume = max(0, min(100, volume))
        if self._codec:
            self._codec.set_volume(self._volume)

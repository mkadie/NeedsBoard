"""ES8311 audio codec driver for CircuitPython.

Ported from the Espressif ESP-IDF ES8311 driver (Apache 2.0).
"""

import time

# Register addresses
_RESET_REG00 = 0x00
_CLK_MANAGER_REG01 = 0x01
_CLK_MANAGER_REG02 = 0x02
_CLK_MANAGER_REG03 = 0x03
_CLK_MANAGER_REG04 = 0x04
_CLK_MANAGER_REG05 = 0x05
_CLK_MANAGER_REG06 = 0x06
_CLK_MANAGER_REG07 = 0x07
_CLK_MANAGER_REG08 = 0x08
_SDPIN_REG09 = 0x09   # DAC serial digital port (data IN to codec)
_SDPOUT_REG0A = 0x0A  # ADC serial digital port (data OUT from codec)
_SYSTEM_REG0B = 0x0B
_SYSTEM_REG0C = 0x0C
_SYSTEM_REG0D = 0x0D
_SYSTEM_REG0E = 0x0E
_SYSTEM_REG10 = 0x10
_SYSTEM_REG11 = 0x11
_SYSTEM_REG12 = 0x12
_SYSTEM_REG13 = 0x13
_SYSTEM_REG14 = 0x14
_ADC_REG15 = 0x15
_ADC_REG17 = 0x17
_ADC_REG1C = 0x1C
_DAC_REG31 = 0x31
_DAC_REG32 = 0x32
_DAC_REG37 = 0x37
_GPIO_REG44 = 0x44
_GP_REG45 = 0x45

# Clock coefficient table: (mclk, rate) -> register values
# Fields: pre_div, pre_multi, adc_div, dac_div, fs_mode, lrck_h, lrck_l, bclk_div, adc_osr, dac_osr
_COEFF_TABLE = {
    (12288000, 8000):  (0x06, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    (16384000, 8000):  (0x08, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    (8192000, 8000):   (0x04, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    (6144000, 8000):   (0x03, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    (4096000, 8000):   (0x02, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    (3072000, 8000):   (0x01, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    (2048000, 8000):   (0x01, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    (1536000, 8000):   (0x03, 0x02, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    (1024000, 8000):   (0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),

    (11289600, 11025): (0x04, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    (5644800, 11025):  (0x02, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    (2822400, 11025):  (0x01, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    (1411200, 11025):  (0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),

    (12288000, 16000): (0x03, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    (16384000, 16000): (0x04, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    (8192000, 16000):  (0x02, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    (6144000, 16000):  (0x03, 0x01, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    (4096000, 16000):  (0x01, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    (3072000, 16000):  (0x03, 0x02, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    (2048000, 16000):  (0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    (1024000, 16000):  (0x01, 0x02, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),

    (11289600, 22050): (0x02, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    (5644800, 22050):  (0x01, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    (2822400, 22050):  (0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    (1411200, 22050):  (0x01, 0x02, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),

    (12288000, 32000): (0x03, 0x01, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    (16384000, 32000): (0x02, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    (8192000, 32000):  (0x01, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    (4096000, 32000):  (0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    (2048000, 32000):  (0x01, 0x02, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),

    (11289600, 44100): (0x01, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    (5644800, 44100):  (0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    (2822400, 44100):  (0x01, 0x02, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),

    (12288000, 48000): (0x01, 0x00, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    (6144000, 48000):  (0x01, 0x01, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
    (3072000, 48000):  (0x01, 0x02, 0x01, 0x01, 0x00, 0x00, 0xFF, 0x04, 0x10, 0x10),
}

_ADDR = 0x18


class ES8311:
    def __init__(self, i2c, address=_ADDR):
        self._i2c = i2c
        self._addr = address

    def _write_reg(self, reg, val):
        while not self._i2c.try_lock():
            pass
        try:
            self._i2c.writeto(self._addr, bytes([reg, val]))
        finally:
            self._i2c.unlock()

    def _read_reg(self, reg):
        while not self._i2c.try_lock():
            pass
        try:
            buf = bytearray(1)
            self._i2c.writeto_then_readfrom(self._addr, bytes([reg]), buf)
            return buf[0]
        finally:
            self._i2c.unlock()

    def _update_reg(self, reg, mask, val):
        old = self._read_reg(reg)
        self._write_reg(reg, (old & ~mask) | (val & mask))

    def init(self, sample_rate=16000, mclk_frequency=None, bits=16):
        """Initialize the codec for DAC playback.

        Args:
            sample_rate: Audio sample rate in Hz.
            mclk_frequency: MCLK frequency in Hz. If None, assumes 256 * sample_rate.
            bits: Audio resolution (16, 24, or 32).
        """
        if mclk_frequency is None:
            mclk_frequency = 256 * sample_rate

        # Reset
        self._write_reg(_RESET_REG00, 0x1F)
        time.sleep(0.02)
        self._write_reg(_RESET_REG00, 0x00)
        self._write_reg(_RESET_REG00, 0x80)  # Power-on

        # Clock config: enable all clocks, MCLK from MCLK pin
        self._write_reg(_CLK_MANAGER_REG01, 0x3F)

        # Look up clock coefficients
        key = (mclk_frequency, sample_rate)
        if key not in _COEFF_TABLE:
            raise ValueError(
                "No clock coefficients for MCLK={}Hz, rate={}Hz".format(
                    mclk_frequency, sample_rate))

        pre_div, pre_multi, adc_div, dac_div, fs_mode, lrck_h, lrck_l, bclk_div, adc_osr, dac_osr = _COEFF_TABLE[key]

        # reg02: pre_div and pre_multi
        reg02 = self._read_reg(_CLK_MANAGER_REG02)
        reg02 &= 0x07
        reg02 |= (pre_div - 1) << 5
        reg02 |= pre_multi << 3
        self._write_reg(_CLK_MANAGER_REG02, reg02)

        # reg03: fs_mode + adc_osr
        self._write_reg(_CLK_MANAGER_REG03, (fs_mode << 6) | adc_osr)

        # reg04: dac_osr
        self._write_reg(_CLK_MANAGER_REG04, dac_osr)

        # reg05: adc_div + dac_div
        self._write_reg(_CLK_MANAGER_REG05, ((adc_div - 1) << 4) | (dac_div - 1))

        # reg06: bclk_div (keep sclk_inv bit)
        reg06 = self._read_reg(_CLK_MANAGER_REG06)
        reg06 &= 0xE0
        if bclk_div < 19:
            reg06 |= (bclk_div - 1)
        else:
            reg06 |= bclk_div
        self._write_reg(_CLK_MANAGER_REG06, reg06)

        # reg07: lrck_h
        reg07 = self._read_reg(_CLK_MANAGER_REG07)
        reg07 &= 0xC0
        reg07 |= lrck_h
        self._write_reg(_CLK_MANAGER_REG07, reg07)

        # reg08: lrck_l
        self._write_reg(_CLK_MANAGER_REG08, lrck_l)

        # Slave mode, I2S format
        reg00 = self._read_reg(_RESET_REG00)
        reg00 &= 0xBF  # Clear bit 6 = slave mode
        self._write_reg(_RESET_REG00, reg00)

        # SDP format: I2S with correct word length
        wl_bits = {16: 3, 18: 2, 20: 1, 24: 0, 32: 4}
        if bits not in wl_bits:
            raise ValueError("Unsupported bit depth: {}".format(bits))
        sdp_val = wl_bits[bits] << 2  # I2S format (bits[1:0]=0) + word length
        self._write_reg(_SDPIN_REG09, sdp_val)   # DAC input format
        self._write_reg(_SDPOUT_REG0A, sdp_val)  # ADC output format

        # Power up analog circuitry
        self._write_reg(_SYSTEM_REG0D, 0x01)
        # Enable analog PGA + ADC modulator
        self._write_reg(_SYSTEM_REG0E, 0x02)
        # Power up DAC
        self._write_reg(_SYSTEM_REG12, 0x00)
        # Enable output to HP drive
        self._write_reg(_SYSTEM_REG13, 0x10)
        # ADC EQ bypass, cancel DC offset
        self._write_reg(_ADC_REG1C, 0x6A)
        # Bypass DAC equalizer
        self._write_reg(_DAC_REG37, 0x08)

        time.sleep(0.05)

    def set_volume(self, volume):
        """Set DAC output volume (0-100)."""
        volume = max(0, min(100, volume))
        if volume == 0:
            reg32 = 0
        else:
            reg32 = (volume * 256 // 100) - 1
        self._write_reg(_DAC_REG32, reg32)

    def mute(self, enable=True):
        """Mute or unmute DAC output."""
        reg31 = self._read_reg(_DAC_REG31)
        if enable:
            reg31 |= 0x60  # Set bits 6 and 5
        else:
            reg31 &= ~0x60
        self._write_reg(_DAC_REG31, reg31)

    def configure_mic(self, gain_db=24, digital_mic=False):
        """Configure the microphone input.

        Args:
            gain_db: Microphone gain in dB (0, 6, 12, 18, 24, 30, 36, 42).
            digital_mic: True for digital DMIC, False for analog mic.
        """
        reg14 = 0x1A  # Enable analog MIC, max PGA gain
        if digital_mic:
            reg14 |= 0x40  # BIT(6)
        self._write_reg(_SYSTEM_REG14, reg14)

        # ADC volume
        self._write_reg(_ADC_REG17, 0xC8)

        # ADC gain scale (reg16): 0=0dB, 1=6dB, 2=12dB, ... 7=42dB
        gain_val = max(0, min(7, gain_db // 6))
        self._write_reg(0x16, gain_val)

    def dump_registers(self):
        """Print all registers for debugging."""
        print("ES8311 Register Dump:")
        for reg in range(0x4A):
            val = self._read_reg(reg)
            print("  REG 0x{:02X} = 0x{:02X}".format(reg, val))

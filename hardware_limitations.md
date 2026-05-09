# Hardware Limitations

## FEATHER_RP2350_V1 — MP3 Playback Distortion

**Processor:** Adafruit Feather RP2350 (RP2350A, dual ARM Cortex-M33)
**CircuitPython:** 9.2.6
**Audio output:** Direct I2S via `audiobusio.I2SOut(board.A1, board.A2, board.A3)` — no dedicated codec/DAC chip
**DAC:** None — the I2S output goes directly to an external amplifier. The RP2350 generates the I2S bitstream in software via CircuitPython's `audiomp3.MP3Decoder`.

### Problem
MP3 files of any sample rate or bitrate play with heavy distortion, clipping, and excessive volume through the direct I2S output on the RP2350. The same MP3 files play cleanly on:
- Computer speakers
- ESP32-S3 (CYD_PLUS) with ES8311 codec
- Fruit Jam (RP2350B) with TLV320DAC3100

### Tested MP3 configurations (all distorted on Feather RP2350)
| Sample Rate | Bitrate | Encoding | Result |
|-------------|---------|----------|--------|
| 44100 Hz | 64 kbps | CBR | Distorted |
| 24000 Hz | 64 kbps | CBR | Distorted |
| 24000 Hz | 32 kbps | VBR | Distorted |
| 16000 Hz | 64 kbps | CBR | Distorted |

### Working format
WAV PCM signed 16-bit little-endian, 16000 Hz, mono plays perfectly.
The WAV header must be minimal (RIFF/fmt/data only — no LIST/INFO metadata chunks).

### Root cause (suspected)
The RP2350's `audiomp3.MP3Decoder` in CircuitPython 9.2.6 may have a bug in the I2S output path when there is no hardware codec managing clocking. The MP3 decoder's output samples may overflow the I2S buffer or the sample rate negotiation between the decoder and I2S output may be incorrect. The Fruit Jam (also RP2350) works because it uses the TLV320DAC3100 codec which handles I2S clocking independently via MCLK/PLL.

### Workaround
Use WAV files (PCM 16-bit, 16000 Hz, mono) for all audio on Feather RP2350 direct I2S configurations. File size is ~3x larger than MP3 but plays reliably.

### GitHub Issue
https://github.com/mkadie/NeedsBoard/issues/27

### Future investigation
- Test with CircuitPython 10.x on Feather RP2350
- Test with an external I2S DAC board (e.g., UDA1334, PCM5102)
- Test with Fruit Jam's TLV320 to confirm codec-managed I2S works
- File upstream CircuitPython bug if confirmed as a platform issue

---

## Device Audio Format Summary

| Device | Processor | Audio Path | MP3 | WAV | Recommended |
|--------|-----------|------------|-----|-----|-------------|
| CYD_PLUS | ESP32-S3 | ES8311 codec via I2C + I2S | ✅ | ✅ | MP3 (saves space) |
| FRUITJAM_V2 | RP2350B | TLV320DAC3100 via I2C + I2S + MCLK | ✅ | ✅ | MP3 (saves space) |
| RP2350_OLED_BADGE_V3 | RP2350A | Direct I2S | ❓ Untested | ✅ | WAV (safe) |
| FEATHER_RP2350_V1 | RP2350A | Direct I2S | ❌ Distorted | ✅ | WAV only |

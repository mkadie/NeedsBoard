# CircuitPython Audio Playback Notes

## Working Formats

### WAV (audiocore.WaveFile)
- **Thai files (working perfectly)**: PCM signed 16-bit LE, 16000 Hz, mono
- This is the most reliable format on CircuitPython
- No decoder overhead — raw PCM samples

### MP3 (audiomp3.MP3Decoder)
- **emergency.mp3 (working)**: 24000 Hz, 64kbps, mono
- gTTS default output: 24000 Hz, ~32-48kbps, mono
- CircuitPython MP3 decoder has known issues with:
  - Very low bitrates (< 48kbps can cause artifacts)
  - Certain encoding modes (VBR can be problematic)
  - Some sample rates

## Recommendation
For maximum compatibility on CircuitPython, convert all audio to:
- **WAV**: 16000 Hz, 16-bit, mono PCM (matches Thai files)
- **OR MP3**: 44100 Hz, 128kbps CBR, mono (standard, most compatible)

## gTTS to WAV Pipeline
```bash
# Generate MP3 with gTTS, then convert to WAV
gtts-cli "word" --lang xx --output temp.mp3
ffmpeg -i temp.mp3 -ar 16000 -ac 1 -acodec pcm_s16le output.wav
```

## File Size Comparison (per word, ~1 second)
- WAV 16kHz mono: ~32 KB
- MP3 64kbps: ~8 KB
- MP3 32kbps: ~4 KB

## CircuitPython Constraints
- audiomp3.MP3Decoder on RP2350: works but sensitive to encoding
- audiocore.WaveFile: always works, larger files
- I2S output handles both, sample rate auto-detected

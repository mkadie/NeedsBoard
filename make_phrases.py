"""Generate the spoken English phrases for a menu with gTTS.

The project's English voice is gTTS (see Credits.md); the Thai set was made
separately with poppop.ai. This regenerates every phrase a menu references
so the whole board speaks in one voice instead of a mix of recordings at
different sample rates.

The text spoken is each item's `text_description` -- the same words the
screen shows -- read straight out of the .menu file, so the audio cannot
drift from the display. An item with no `sound` key (a submenu or a back
button) is skipped: it navigates rather than speaks.

Output is 44.1 kHz mono MP3. That rate is not cosmetic: the TLV320DAC3100
only accepts 8000/11025/22050/44100/48000 as a BCLK rate, and the older
16 kHz recordings in this tree sit outside that set.

Needs network (gTTS calls Google) and ffmpeg.

Usage:
    python3 make_phrases.py              # all menus listed in MENUS
    python3 make_phrases.py --dry-run    # print what it would say, call nothing
"""

import os
import re
import subprocess
import sys

MENUS = ["menus/base_fruitjam.menu", "menus/food_fruitjam.menu"]
LANG = "en"
TLD = "com"          # accent: .com = US English
SAMPLE_RATE = 44100


def parse_items(path):
    """[(section, {key: value})] for a .menu file, in file order."""
    items = []
    current = None
    for raw in open(path):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        if line.startswith("[") and line.endswith("]"):
            current = (line[1:-1], {})
            items.append(current)
        elif "=" in line and current is not None:
            key, _, val = line.partition("=")
            current[1][key.strip()] = val.strip()
    return items


def phrases_for(path):
    """[(sound_path, text)] for every item in `path` that actually speaks."""
    out = []
    for name, keys in parse_items(path):
        if name == "menu":
            continue
        sound = keys.get("sound")
        if not sound:
            continue          # submenu / back: navigates, says nothing
        text = keys.get("text_description") or keys.get("label") or name
        out.append((sound, text))
    return out


def local_path(sound):
    """Menu sound reference -> path in the repo, as action.py resolves it."""
    return sound.lstrip("/") if sound.startswith("/") else "menus/" + sound


def synth(text, dest):
    """Speak `text` to `dest` as 44.1 kHz mono MP3."""
    from gtts import gTTS

    tmp = dest + ".raw.mp3"
    gTTS(text=text, lang=LANG, tld=TLD).save(tmp)
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-i", tmp,
         "-ac", "1", "-ar", str(SAMPLE_RATE), "-b:a", "64k", dest],
        check=True)
    os.remove(tmp)


def main(argv):
    dry = "--dry-run" in argv
    total = 0
    for menu in MENUS:
        print("\n{}:".format(menu))
        for sound, text in phrases_for(menu):
            dest = local_path(sound)
            print('  {:34s} "{}"'.format(dest, text))
            if not dry:
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                synth(text, dest)
            total += 1
    print("\n{} phrase(s){}".format(total, " (dry run)" if dry else " written"))


if __name__ == "__main__":
    main(sys.argv)

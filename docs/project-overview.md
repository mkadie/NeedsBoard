# Project Overview

> **Updated 2026-05-30:** This document was the original design brief from early 2025, written while the first prototype was being built for a special-needs child in Thailand. The project has since shipped as **T-Rex Talk v3.0** (released March 28, 2026) with four supported hardware variants, a menu file system, and an SD-card auto-installer. See *Status today* below for the current state; the original brief is preserved at the bottom of this file as a snapshot of where the project started.

---

## Status today

The project that began as "Moana's associative device" has shipped as **T-Rex Talk** — an open-source AAC (Augmentative and Alternative Communication) device that helps people communicate by pressing pictures on a screen. When a picture is pressed, the device speaks a word or phrase out loud.

**No programming knowledge needed.** Teachers and parents customize the device by editing simple text files — see [`GUIDE_FOR_TEACHERS.md`](../GUIDE_FOR_TEACHERS.md).

### What's working now

- **Picture-based communication** — touch or press to speak
- **Menu system** — vocabulary organized into topic boards via `.menu` files
- **Emergency button** — instant help message on hold (~1.2 seconds)
- **Configurable** — volume, speed, sleep timing, encoder direction via `config.txt`
- **Multi-language** — bilingual support, tested with Thai/English
- **Playback speed control** — slow down speech for pre-verbal learners
- **Sleep/wake** — battery-friendly power management
- **SD card installer** — auto-detects board and configures device

### Supported hardware variants

| Device             | Screen                       | Input                         | Best for               |
| ------------------ | ---------------------------- | ----------------------------- | ---------------------- |
| **CYD_PLUS**       | 320×240 color touch          | Touch screen                  | Primary AAC device     |
| **Fruit Jam**      | 160×128 color LCD            | Rotary encoder                | Compact, low-power     |
| **OLED Badge**     | 128×32 mono OLED             | Rotary encoder                | Wearable, text-only    |
| **Feather RP2350** | 320×240 color LCD            | 8 physical buttons + encoder  | Physical button access |

### Devices deployed

5 AAC devices currently in field use. Goal: 50-unit production prototype run.

### Related repositories

- [`mkadie/NeedsBoard`](https://github.com/mkadie/NeedsBoard) — this repo (T-Rex Talker)
- [`mkadie/SipNPuff`](https://github.com/mkadie/SipNPuff) — breath-controlled switch (working alpha/beta)
- [`mkadie/MSPM0_Seesaw`](https://github.com/mkadie/MSPM0_Seesaw) — I²C peripheral firmware for TI MSPM0G3507

### Branding

The active brand for the public-facing project is **R.O.A.R. — Rex's Open Assistive Resources**, at [tssfaa.com](https://tssfaa.com).

---

## Original document (early 2025)

> The text below is the original "Moana associative device" design brief, preserved as written. Footnote: the original spelling of Moana's name was uncertain — the author chose "Moana" because it made him smile.

### Moana associative device

Have buttons numbered by I/O pin for simplicity of low-powered processor. Have a look-up table in main software that is easily configured, maybe by QR code when keys are plugged in, or a manual with photos and corresponding configuration. Have configuration in named files. Files would be named like NES, 4-column 2-row, rotary encoder.

Menu types finite and list.

**Status at time of writing — Working Prototype.** Startup is slow as it exercises all the systems and I don't have all the graphics, but all the words are encoded and it speaks when a button is pressed, with the button vibrating and lights flashing around the pressed button. *Was: Function Complete — I have written code that exercises all the functional parts required for the final device and made changes where needed.*

*Later update added to the original doc — "Now working and on way to special needs child."*

### Initial Needs icons

(See [`needs-word-list.md`](./needs-word-list.md) — the initial vocabulary list for Moana, six basic needs she did not currently communicate.)

### Introduction

This project / paper covers the building of an assistive device for a special needs girl I met in Thailand. It borrows some of what I learned from the assistive speech boards I built in college and many years of electronic and software engineering that I have done in the meantime. The intent is to build it in such a way that it is easily reused and adapted for other projects, be they special needs or otherwise.

Moana has six needs that she does not currently communicate. The one that brings me the most joy is the trampoline — she apparently loves playing on it. Using dog buttons available online might help her express these needs, but it's uncertain. The key is to build associations between her needs and a form of communication that her caregivers and family can understand. My plan is to start with bright, colorful, and durable buttons, each labeled with a picture representing one of her needs. Pushing the buttons will:

1. Activate a stagnant set of 4 single-color LEDs that will stay lit for a period of time, surrounding the button
2. Activate a sequence of 4-color NEOPixel LEDs that will attempt to be visually stimulating. These are offset at 90 degrees.
3. Play a recorded or synthesized voice stating the need from a wave file.
4. It would be good to add a vibration feature, but not in the first iteration. I just had the idea as I was typing.

Current test article. Synthesized voice file sounds pretty good. Built from closest existing hardware I had lying around.

Recording from phone of trampoline from test article: [Google Drive link](https://drive.google.com/file/d/1qb92j4w4Nms7PUfHk4EWQCyRjlVYXBTG/view?usp=sharing).

Original speech boards from the early 1990s (referenced in HISTORY.md).

### Design constraints

- **Portable**
  - Currently 290mm × 290mm
  - Next version target for 225 × 225 to 250 × 225 so that they will be printable on more printers
- **Tough**
- **Weather resistant**
- **Long battery life**
- **Convenient** for both the user and the caregiver
- **Easily modified software**
- **Very engaging**
- **Easily configurable** either remotely or ideally by the caregiver
  - Assistive configuration

### Current design choice

- **CircuitPython**
  - No need to recompile, can just plug into USB and edit files
  - Great libraries
  - Great community
  - Fast development cycle
  - Will introduce some delays at power-on time
  - May add some latency between button push and NeoPixel sequencing / voice playback — not a lot
- **Medium-sized screen** to reinforce or add to the experience. Could just be a future upgrade or covered and reserved for later. This is great for diagnosing what is happening, so even if the user doesn't benefit from it, it is still worthwhile.
- *Open questions:*
  - How long should the screen be on before it times out and turns off?
  - How long should the system be on before it times out and goes into deep-sleep mode?
- **Separation of inputs from core system**
  - This will allow easy changing of inputs without much development cost
  - Current design has the buttons connected to an I²C communication bus that talks to the embedded processor
  - Want to develop a standard for assistive communications that is protocol-agnostic, but not for the first version
    - e.g. a powered wheelchair might have forward, backward, rotate right, rotate left, and speed. If we can encode that to a standard message format over (say) CANBUS, then we can plug whatever human interface the user needs into a standard chair and save a lot of integration and customization.
  - Consider moving to a cable interconnect system. Use standard, readily available, premade cables. Special needs switches use stereo / stereo + mic headphone 3.5mm plugs, so do that.
    - RJ45
    - USB
    - MIDI
    - DIN
    - Ribbon
- **More important to get it done soon** than to get it done perfect on the first try. We won't know everything until after it is in their hands, and as long as we deliver a functional good-ish first article we can adapt after we learn more. We hope to adapt for others after we finish as well.

### Sub-documents

- Button Board → see [`button-board-v1.md`](./button-board-v1.md)
- Processor Board
- Assistive Configuration

### Progress notes (original)

- Battery power — start with battery bank
- Boards sent to fab (Button Board, Processor Board)

### Parts (original)

- Latch — [PCA9555 datasheet](https://www.nxp.com/docs/en/data-sheet/PCA9555.pdf)
- Headphone jacks — [JLCPCB audio connectors](https://jlcpcb.com/parts/2nd/Connectors/Audio_Connectors_3080)
- Built-in I²S amplifier — [MAX98357A on JLCPCB](https://jlcpcb.com/partdetail/978950-MAX98357AETET/C910544), [datasheet (PDF)](https://www.analog.com/media/en/technical-documentation/data-sheets/max98357a-max98357b.pdf)
- RP2350 chip — [JLCPCB search](https://jlcpcb.com/parts/componentSearch?searchTxt=RP2350)

### Working notes / things found out (original)

- Waking from deep sleep causes soft reset. The delay between pushing a button and playing "Trampoline" wav file is acceptable.
- Use magnets to keep button pushed up and away from switch.
- The vibration motors are magnetic so they will stick to the magnets on the switches, so they can attach to the PCB without separate mounting.
- **Plastics**
  - ASA for temp, chem, UV resistance with good strength
  - Colors: Black + White + Grey + Blue + Green + Red + Orange + Purple + Yellow + Teal + Pink

---

*Captured / possibly obsolete notes from the original were filed under "Working Notes Assistive Project."*

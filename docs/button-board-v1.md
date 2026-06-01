# Button Board — V1 Historical Design Notes

> **Updated 2026-05-30:** This document describes the original button board design from March 2025, which used dedicated hardware (PCA9555 I²C expander + latch circuit) for low-power button input. The project has since moved to a more flexible input architecture that supports four different hardware variants. See *Status today* below for the current state; the original V1.0 design is preserved at the bottom.

---

## Status today

The button board's role is now filled by [`input_manager.py`](../input_manager.py), which abstracts inputs and supports four front-end variants:

| Variant            | Input style                                  |
| ------------------ | -------------------------------------------- |
| **CYD_PLUS**       | Touch screen (320×240)                       |
| **Fruit Jam**      | Rotary encoder (compact, low-power)          |
| **OLED Badge**     | Rotary encoder (wearable, text-only)         |
| **Feather RP2350** | 8 physical buttons + encoder                 |

Plus the original I²C-connected button-array architecture is still supported by the firmware.

Configuration is now via [`config.txt`](../config.txt) and `.menu` files, **not** custom PCB rework. The "open assistive communication standard" vision from the V1 design notes below is closer to reality — the same firmware now drives four different hardware front-ends.

### What V1 contributed to today's design

- The "near-immediate feedback" idea (LEDs and vibration that fire the instant a switch closes) made it into V3 as the emergency-button hold (~1.2 seconds) and the picture-button visual feedback.
- The "input boards are interchangeable, configured via files, not code" idea is the spine of the current architecture.
- The cable-connector standardization (3.5mm TRRS, like off-the-shelf AT switches) is preserved.
- The vision section ("open source communication standard for assistive communications, protocol-agnostic") is still the long-term goal — not implemented as a formal standard yet, but the current code architecture leaves room for it.

### What V1 chose that didn't survive

- **PCA9555-only input pathway.** The board still works via I²C, but the canonical paths now are touch and encoder for most users.
- **Dedicated latch IC.** The 1.2-second emergency-button feedback is now firmware-side. The Class 0 ultra-low-power "screen off + speaker off + processor deep sleep, button board powered" mode wasn't needed once the battery life from the modern variants proved adequate.
- **"V1.0" branding.** The release branding is now T-Rex Talk v3.0, and the per-board V1.0 naming is retired.

---

## Original document (March 2025)

> Original title: **Button Board for associative device.** Preserved as written.

Have buttons numbered by I/O pin for simplicity of low-powered processor. Have a look-up table in main software that is easily configured, maybe by QR code when keys are plugged in, or a manual with photos and corresponding configuration. Have configuration in named files. Files would be named like NES, 4-column 2-row, rotary encoder.

Button Board should have near-immediate feedback, so I have put in a circuit that latches the moment the switch is closed and turns on a boring set of lights and pager motor until `clear_interrupt` is sent. This allows a very low-power mode — screen off, speaker off, processor in deep-sleep mode, button board powered.

The time between pressing a button and the processor waking and taking action is noticeable by me, but only while paying attention. For an associative device I think any delayed response might lessen the impact, so I have this circuit in place.

### Vision

- **Open-source communication standard for assistive communications that is protocol-agnostic.**
  - e.g. a powered wheelchair might have forward, backward, rotate right, rotate left, and speed. If we can encode that to a standard message format over (say) CANBUS, then we can plug whatever human–machine interface the user needs into a standard chair and save a lot of integration and customization.

### Button Board V1.0 — design notes

- It is more important that we build a working system and help the first child than we develop a standard that may or may not reach fruition. So: focus on a working system and helping the child first, then as we learn we can generalize for others and build/expand an open-source assistive standard.
- I²C for communication layer.
- I/O connector input board with I²C, interrupt, clear_interrupt, and NeoPixel controls — maybe a standardized "cheap hardware" connection.
- The buttons are mapped over I²C.
- There is an interrupt when any button is pressed.

### Button Board V1.0 — implementation (boards ordered 2025-03-20)

- Each board is a 1 × 4 array of button objects.
- Each button object consists of:
  - One large plastic button that is colorful, easily pressed, 3D printed, easily assembled. Has a magnet in the middle, 4 alignment pins. Will have a picture / sticker / symbol / text placed on top.
  - 4 parallel tactile switches. With the idea that 4 should provide the spring-back we want without adding springs.
  - 4 simple LEDs that immediately light when the button is pressed.
  - 1 cell-phone vibration motor that is magnetically attached to the large button. Immediately triggered when button is pressed.
  - 4 RGB LEDs that will entertain. These are controlled by the processor board, and there is a slight delay between when the button is pressed and when these lights start.
- Board has a lot of extra resistors and configuration capabilities, with the understanding that if any mistakes are made — or any parts don't work as expected — it will be much easier to "bodge" a working prototype out of the first article boards.

### Future (as written in original)

- Replace dedicated hardware chips with embedded processor.
  - Cost saving by replacing both the I²C expander and the latch with an embedded processor such as TI MSP430 at low power / low speed.
  - The power draw of this chip is low enough not to impact battery life.
  - The reason this is not included in the first version is time to prototype — removing coding and debugging gets the first version out sooner.
  - It would be good to have a helper processor to work on standardization for this (e.g. communication protocol), but maybe that should be done one level up?
  - Maybe it should be 2 D-pads to be more like game controllers and interchangeable with them.
    - Cons:
      - harder for LCD programming to look correct
      - quite a bit bigger
  - Think about adding EEPROM for auto-identification on every board in system.
  - Should be a query command that returns a list of inputs that will be provided, class of device, and human-readable description of device.

### Classes / types of inputs

- DPad layout, like game controllers
- Matrix (referred to in array notation `[x,y]` or underscore notation `x_y`)
- Rotary encoders
- Touchscreens
- Buttons over screen (Stream Deck-style) — [reference](https://github.com/SuperMakeSomething/diy-stream-deck)
- Joysticks
- Rotary potentiometers
- Slider / linear potentiometers
- Mouse / trackball
- Keyboard (special case of matrix)
- "Transmission / shifter"
- Breath (in / out / neutral) — easily simulated with 2 buttons and process monitoring "being pressed"

### Working pictures / notes (original)

- Button Board (board photo placeholders in original)
- Parts:
  - Latch
  - I²C expander — [PCA9555 datasheet](https://www.nxp.com/docs/en/data-sheet/PCA9555.pdf)
- Latch not working — investigating MSP430 alternatives:
  - MSP430FR2433IRGER — 16 KB FRAM, 4 KB SRAM, 10-bit ADC, UART/SPI/I²C, timer
  - MSP430G2553IPW28R — 16 KB Flash, 512 B SRAM, comparator, UART/SPI/I²C, timer
- Schematic — `Assistive4x1ButtonArray.pdf`
- Dimensions — 12.6172 mm × 81 mm, 15 mm separation

### Libraries

- [CircuitPython_I2C_Expanders v1.0.0](https://github.com/ilikecake/CircuitPython_I2C_Expanders/tree/1.0.0) — for PCA9555 I²C expander

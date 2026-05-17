# Custom RP2350 Board for `T-Rex_talker`

A stripped, low-power derivative of the Adafruit Fruit Jam designed as the production hardware for the talker. The Fruit Jam remains the development and reference platform; this custom board is the production target.

> **Status:** preliminary design notes, but grounded in working alpha hardware. See [Development status](#development-status) below. Specific component selection that is still **TBD** (exact flash size, MSPM0 part number, display interface details and panel choices, speaker driver, daughterboard connector pinout) is tracked in the open questions at the bottom of this document.

## Development status

The custom board's design is not pure speculation — it is being driven by a working alpha **Fruit Jam daughterboard** that the project has been actively testing. Concretely:

- The Fruit Jam daughterboard is **working alpha with bodge wires**. It is being used to validate component choices and feature decisions before committing to a custom-board PCB layout.
- The daughterboard currently carries:
  - **MSPM0** (on an [Adafruit Seesaw Tiny 1616](https://www.adafruit.com/product/5743)-footprint PCB, so the same module footprint as Adafruit's ATtiny1616 Seesaw board)
  - **Battery input + charging circuit**
  - **Audio passthrough** input from the Fruit Jam's audio output, routed onward to the main board
- The MSPM0 on the Seesaw-Tiny-1616-footprint module **still needs to be programmed and tested** end-to-end to verify it behaves as expected as wake controller / interrupt handler / I/O expander.
- The daughterboard's header pinout is **compatible with the V2 AAC hardware**, so the same daughterboard can be plugged into it for testing without rework.

This staging — alpha-on-Fruit-Jam-daughterboard first, then custom board — is intentional: it lets every component on the custom-board BOM be exercised in real hardware before being committed to a custom PCB.

## Design philosophy

If a feature is expensive enough — in power draw, BOM cost, or board area — that having it would erase the difference between this board and a stock Fruit Jam, that feature does not belong on this board. The custom board exists to give us:

- Lower idle and active power draw than the Fruit Jam
- A smaller, cheaper BOM
- A smaller physical footprint
- More headroom (flash budget, GPIO, mechanical layout, power budget) for AAC-specific peripherals
- Battery operation as a first-class deployment mode

Anything that doesn't serve those goals comes off the board.

A corollary: **the custom board is not "Fruit Jam minus DVI."** It's a different point in the design space. Use cases that need DVI output to an external monitor should just use a Fruit Jam — the production custom board is for self-contained, battery-powered, lower-power deployments.

### Target use case: minimum portable AAC device

The primary design target is a **minimum-size portable AAC device** for users with selective mutism, involuntary non-verbal conditions, and similar communication needs. "Minimum-size" drives several decisions:

- MSPM0 is integrated **on the main board** rather than on a daughterboard (the Fruit Jam dev setup uses an MSPM0 daughterboard for compatibility, but on the custom board the same chip is on the main PCB to save space).
- USB host is on an *optional* daughterboard — a deployment that uses only MSPM0-mediated input doesn't carry the USB host hardware.
- All user-facing connectors are placed on a single edge so cases can treat the board as a "plug-in processor module."

## Compatibility principle

The custom board is **wire-compatible** with the Fruit Jam for everything the talker firmware touches. In particular, the MSPM0 I/O expander (see below) is wired identically on both boards, so the same talker code runs on both without changes. Where peripherals are absent on the custom board (DVI, NeoPixels, ESP32-C6, IR), the talker firmware must guard their use behind feature flags or hardware-abstraction shims so the absence is graceful.

## Specification

### Retained from Fruit Jam

| Component | Notes |
|---|---|
| **RP2350B** (dual Cortex-M33 @ 150 MHz) | Same MCU as Fruit Jam |
| **PSRAM** | 8 MB |
| **Flash** | 8 MB or 16 MB (TBD — depends on final code + asset budget) |
| **microSD slot** | QSPI interface |
| **I2S audio** | Speaker output **integrated through the main board-edge connector** (no separate on-PCB speaker connector) |
| **Headphone jack** | Retained, placed on the same edge as all other user-facing connectors |
| **USB-C device port** | Retained on the main board for power, programming, and bootloader access |
| **MSPM0 wiring** | Same pinout as the Fruit Jam dev setup, so firmware ports cleanly. MSPM0 lives on a **daughterboard** for Fruit Jam dev, **integrated on the main PCB** on the custom board. |

### Removed

| Component | Reason |
|---|---|
| **DVI / HSTX video output** | Power-hungry. Deployments that can afford DVI's power budget can afford a Fruit Jam. The custom board uses LCD and OLED display connectors instead — see [Display](#display) below. |
| **NeoPixels** | Idle power draw is unacceptable for an always-on battery-powered appliance. |
| **IR receiver** | Not used by the talker. |
| **ESP32-C6** | Not used in the default build. Retained only on a future eye-tracking variant SKU. |
| **Other** | Additional parts removed for cost / BOM reduction (specifics TBD) |

### Moved

| Component | Where it goes |
|---|---|
| **USB host port** | Moved off the main board onto an **optional daughterboard**. Deployments that need USB HID input (head-mouse, switch interface that emulates HID, future external gaze-to-HID bridge) attach the daughterboard. Deployments that drive the talker entirely through the MSPM0's I/O don't pay the power and BOM cost of the USB host hardware. |

### Added

**MSPM0 ultra-low-power MCU** — TI's Cortex-M0+ family, configured as an always-on companion to the RP2350 with three combined roles:

1. **Wake-up controller.** The RP2350 can sleep deeply between user actions. The MSPM0 stays awake on a tiny power budget and wakes the RP2350 when a user input event occurs.
2. **Interrupt handler.** Slow, sporadic, or jitter-sensitive I/O lines terminate on the MSPM0 rather than the RP2350, so the main MCU isn't woken or interrupted for every edge.
3. **I/O expander.** Adds usable GPIO beyond what the RP2350 provides directly.

The MSPM0 is **integrated onto the main PCB** on the custom board (to keep the minimum-portable-device footprint small). On the Fruit Jam dev setup the same MSPM0 lives on the **Fruit Jam daughterboard**, mounted on a PCB that uses the [**Adafruit Seesaw Tiny 1616**](https://www.adafruit.com/product/5743) footprint — the same physical module footprint as Adafruit's ATtiny1616-based Seesaw. The daughterboard header pinout is also **compatible with the V2 AAC hardware**, so the same module drops into that test rig without rework.

Wiring between the MSPM0 and the host RP2350 is **identical on both boards**, so firmware that drives talker buttons, switch inputs, sip-and-puff lines, etc. through the MSPM0 on Fruit Jam works unchanged on the custom board.

**Host bus: I²C, speaking the Adafruit Seesaw protocol.** The MSPM0 firmware exposes itself on I²C as a Seesaw-compatible device, matching both the physical footprint and the wire protocol of the Adafruit Seesaw line. The practical implication is that the host-side talker code can use the existing [`adafruit_seesaw`](https://github.com/adafruit/Adafruit_CircuitPython_seesaw) CircuitPython library directly to read GPIO, ADC, encoder, and similar peripherals from the MSPM0 — no custom host-side driver is needed for the common register set, only for any MSPM0-specific extensions beyond what Seesaw defines.

Specific MSPM0 part number is TBD; the module still needs to be programmed and bench-verified against the Seesaw register layout.

**Battery input with charging circuit** — the board accepts a **standard lithium-ion battery (3.7 V nominal)** and includes onboard charging. USB-C provides charge current as well as data. This is what makes the device viable as a truly portable AAC device rather than a wall-tethered appliance.

On the Fruit Jam dev setup, the same battery + charging circuit lives on the **Fruit Jam daughterboard** so the entire portable power story can be exercised end-to-end on Fruit Jam before the custom-board PCB is committed.

**Multiple display and input connectors** — the board exposes several connectors on its single user-facing edge:

- Multiple **display connectors** supporting both LCD and OLED panels (specific interfaces, count, and pinout TBD — see [Display](#display) below).
- Multiple **input connectors** for AAC-side I/O (talker buttons, switch interfaces, sip-and-puff trigger lines, future modality-specific peripherals). These route through the MSPM0 rather than directly to the RP2350.

## Display

DVI is removed. The custom board exposes **multiple display connectors supporting LCD and OLED panels**. This matches how existing AAC devices typically present information to the user — small embedded panels rather than external monitors. Supporting multiple display connectors on one PCB means:

- A single board can be paired with whichever panel best fits a given enclosure or use case (small OLED for a wrist/lapel device, larger LCD for a desktop tablet-style device, etc.).
- The talker firmware sees the display through an abstraction; the physical panel can be swapped without changes to AAC UI code.

The framebuffer story (PSRAM allocation, partial-redraw vs. full-redraw, color depth) depends on the specific panels chosen and is tracked as an open question.

The talker rendering code should be written against a display abstraction so the backend can be selected at build/config time:

- **DVI backend** for Fruit Jam dev work
- **LCD/OLED backend(s)** for custom-board production

Specific connector pinouts, supported panel sizes/resolutions, and the LCD vs. OLED interface choices (SPI, parallel via PIO, MIPI?) are TBD.

## Speaker / audio

- I2S audio retained.
- Speaker output **integrated through the main board-edge connector** rather than a dedicated on-PCB speaker connector. The enclosure cable carries audio along with whatever else terminates on the main connector. This eliminates a separate connector and assumes an enclosure-mounted speaker.
- **Headphone jack retained**, placed on the same edge as all other user-facing connectors (see [Connector layout](#connector-layout)).

On the Fruit Jam dev setup, audio leaves the Fruit Jam's normal audio output and is **routed through the Fruit Jam daughterboard** to the main board. This lets the daughterboard be the single point of contact for the AAC enclosure cable (audio + power + I/O all merging through one board), matching the topology the custom-board production design assumes.

## USB

- **Device-mode USB-C** for power, programming, and bootloader: **retained** on the main board. Also serves as the charge input for the battery (see [Power and battery](#power-and-battery)).
- **USB host port** (the one used to accept HID input from external head-mice, switch interfaces, etc.): moved to the optional daughterboard. Without the daughterboard, the talker has no USB host capability and must drive all input through the MSPM0.

## Power and battery

The board adds a **battery input with onboard charging circuit**, making the device portable rather than wall-tethered. USB-C provides charge current.

- **Battery chemistry:** standard **lithium-ion, 3.7 V nominal** (single cell).
- **Battery capacity:** TBD.
- **Charging IC:** TBD.
- **Power path:** the board should support running while charging.

The same battery + charging circuit is also present on the Fruit Jam daughterboard so the full portable-power path is being exercised on alpha hardware before being committed to a custom PCB.

The combined effect of the removals (DVI, NeoPixels, ESP32-C6, IR) plus the MSPM0 wake controller is meant to enable:

- Deep sleep for the RP2350 between user input events
- Tens-of-µA-class idle current driven mostly by the MSPM0
- Wake latency low enough to feel immediate to the user (target TBD)
- All-day battery life as a design goal (specific runtime target TBD)

Specific numbers are not yet measured and are tracked as open questions.

## Connector layout

All user-facing connectors are placed on a **single edge of the PCB**. This treats the board as a "plug-in processor module" and dramatically simplifies enclosure design: cases only need to expose one edge.

Connectors expected on that edge:

- USB-C (data + charging)
- Headphone jack
- Main board-edge connector carrying speaker and other I/O
- Multiple display connectors (LCD / OLED)
- Multiple input connectors (AAC inputs via MSPM0)
- Battery connector (may or may not be on the same edge depending on enclosure ergonomics — TBD)

Exact connector types, pin counts, and ordering along the edge are TBD.

## Implications for `T-Rex_talker` firmware

Because the custom board is wire-compatible with the Fruit Jam dev platform (via the MSPM0 daughterboard), firmware portability is mostly about *gating absent peripherals* and *abstracting hardware-specific backends*, not rewriting drivers. Specifically:

- **Display backend** must be selectable at build time: DVI on Fruit Jam, LCD/OLED on the custom board. The talker UI code talks to a display abstraction, not directly to a panel.
- **USB host code** must tolerate the host port being physically absent (custom board without USB daughterboard) and continue running with MSPM0-mediated input only.
- **NeoPixel, ESP32-C6, IR, on-board-button** code must be optional / behind feature flags.
- **MSPM0 I/O** is the common path for AAC inputs (talker buttons, switch lines, sip-n-puff trigger, etc.) on both platforms. Application code should talk to the MSPM0, not directly to RP2350 GPIO, for these. Because the MSPM0 firmware speaks the Adafruit Seesaw I²C protocol, the host-side driver is `adafruit_seesaw` — no custom CircuitPython driver needs to be written for the standard register set.
- **Wake / sleep state machine** is shared logic and should live in a portable module.
- **Battery / power state** (charging, discharging, low-battery warning, critical shutdown) is needed on the custom board and harmless / no-op on the Fruit Jam dev platform. Same code path either way, with the battery monitoring sensor gated by feature flag.

This is the basis for Open Question #5 in [the input-layer feature request](./FEATURE_REQUEST_pointer_input_and_eye_tracking.md) about which peripherals to gate behind feature flags now.

## Open questions

1. **Flash size: 8 MB or 16 MB?** Depends on the final code + bundled asset (audio clips, board images) budget.
2. **MSPM0 part number.** Which specific MSPM0 part? (Host bus is settled: I²C, speaking the Adafruit Seesaw protocol.) The module still needs to be programmed against the Seesaw register layout and bench-verified.
3. **Display interfaces.** Which interface(s) drive the LCD/OLED connectors — SPI, parallel-via-PIO, MIPI, something else? How many connectors of each type, and what panel sizes/resolutions are supported?
4. **Daughterboard connector.** What's the pinout for the custom-board's USB-host-and-future-extras daughterboard? Is it on the same single-edge connector strip, or separate? (Note: this is distinct from the Fruit Jam daughterboard, whose header is already defined and compatible with v1/v2 hardware.)
5. **Speaker driver.** Is the I2S DAC retained from the Fruit Jam reference (TLV320DAC3100) or replaced with something simpler / lower-power?
6. **Battery capacity and charging IC.** Specific part selection (chemistry is settled — Li-ion 3.7 V nominal).
7. **Power numbers.** Measured idle / active / wake-latency targets, and target battery runtime.
8. **"Some other parts will be removed for cost savings."** Which ones, specifically?
9. **Eye-tracking variant SKU.** Does this board get an alternate-stuffed version with the ESP32-C6 populated for the eye-tracking variant, or does the eye-tracking variant stay on Fruit Jam?
10. **Connector edge ordering.** Final placement order of connectors along the single user-facing edge, and whether the battery connector is on that edge or elsewhere.

## Related documents

- [FEATURE_REQUEST_pointer_input_and_eye_tracking.md](./FEATURE_REQUEST_pointer_input_and_eye_tracking.md) — the input-layer feature request that this hardware needs to support
- [mkadie/SipNPuff](https://github.com/mkadie/SipNPuff) — first USB HID input device that will exercise the daughterboard / MSPM0 path

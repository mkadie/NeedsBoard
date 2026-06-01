# Plan Going Forward

> **Updated 2026-05-30:** This document was the project plan written ahead of Open Sauce 2025. Most of what it called for has since shipped or evolved. See *Status today* below for the current state; the original plan is preserved at the bottom as a snapshot of pre-Open-Sauce-2025 intent.
>
> *The original document opens with the line "this document will not age well" — which turned out to be accurate.*

---

## Status today

### Shipping or shipped

- ✅ **T-Rex Talk v3.0** released March 28, 2026 (this repo's first tagged release)
- ✅ **Modular separation**: input devices, processors, and the menu system are now decoupled and configurable via text files
- ✅ **Five AAC devices deployed** to users
- ✅ **Open Sauce 2025 attended** — Bay Area Maker Faire Editor's Choice Award
- ✅ **R.O.A.R. branding** established at [tssfaa.com](https://tssfaa.com) (Rex's Open Assistive Resources)
- ✅ **Four supported hardware variants** — CYD_PLUS, Fruit Jam, OLED Badge, Feather RP2350
- ✅ **SD-card auto-installer** — no manual flashing for end users
- ✅ **`.menu` file system** — vocabulary is data, not code
- ✅ **Bilingual support** — Thai/English tested

### In progress

- 🔄 **50-unit production prototype run** (goal: this year)
- 🔄 **SipNPuff** breath-controlled switch — separate repo at [`mkadie/SipNPuff`](https://github.com/mkadie/SipNPuff), working alpha/beta in hand, used to operate T-Rex Talker V3
- 🔄 **MVP test group recruitment** — 10 involuntary nonverbal individuals (formerly: selective mutism), recruited via the website
- 🔄 **Open Sauce 2026** booth prep (July 18, 2026, San Mateo)
- 🔄 **MSPM0_Seesaw** — [`mkadie/MSPM0_Seesaw`](https://github.com/mkadie/MSPM0_Seesaw) — Adafruit Seesaw-compatible I²C firmware for the TI MSPM0G3507 (low-power Cortex-M0+)

### Future / still queued

- **Hardware standard for assistive communications** — protocol-agnostic, CANBUS-style (still the long-term vision; not yet a formal standard)
- **IMU head tracking for the sip-and-puff** (Phase 2; BNO055 selected; both head-strap and tongue-joystick modes designed)
- **Medical-grade certified variant** — architectural direction documented (IEC 62304 / FDA Class II path), redundant pressure sensor + safety MCU
- **More language support** — beyond Thai/English

### What's now visible from the front end

- The website at [tssfaa.com](https://tssfaa.com) has the active schedule, the MVP recruitment, the R.O.A.R. branding, and the Sip-N-Puff announcement.
- The website at [mkadie.github.io](https://mkadie.github.io) is the personal page (Michael Kadie / T-Rex), with the developer landing and the credentials background.
- This repo (`mkadie/NeedsBoard`) is the canonical home of T-Rex Talk firmware, hardware files, and documentation.

---

## Original document (pre-Open-Sauce-2025)

> Original title: **Needs Devices Plan going forward next steps.** Preserved as written. Opens with the author's own self-aware caveat:
>
> *"(this document will not age well)"*

We know that we have an unmet need for communication devices for non-verbal children with minimal coordination and/or strength. There are several children in local LA school that we can build devices for, and so there are probably many people who could take advantage of this.

Our plan is to divide the modules and connect them via cables so that we can easily mix and match and only have to develop the parts that a particular individual needs and then configure it.

### For Open Sauce I would like to have

- 2 processor modules — one RP2350 and one Pi Zero 2.
- Lots of button combinations plugged into the button interface board via standard cables so we can demonstrate a mix and match. Big lever button, arcade button, break-a-light button, USB controller, straw button controlled by turkey blaster, joystick, rotary encoder, touch on demo units.
- Headphone jacks for switches — standard male from switch, maybe add stereo input for lights?

### Our Open Sauce goal

Finding more individuals with needs, getting a few volunteers (engineers, social media, special needs experts, documentation, someone to help organize this theoretical group of people), and free stuff to build the devices. A little baking in my own glory I suppose…

### Reference

- Symbols to review — [Metacom](https://www.metacom-symbole.de/metacom_en.html)
- **Open Sauce 2025** — #opensauce2025 — [https://youtu.be/n3s2r6SC2xQ](https://youtu.be/n3s2r6SC2xQ) (video instructions for unboxing and using the device)
- Project information / how to help — [https://tssfaa.com/](https://tssfaa.com/)
- *Get prepared for taking sponsorship — we will need filament and PCBs and components if we are going to build a lot of these.*

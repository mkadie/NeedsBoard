"""AAC Device Hardware Test Suite.

Deploy as code.py (or run via test_hardware import) to test individual
hardware subsystems during board bring-up.

Set TEST_ONLY in settings.toml to run a single test:
    TEST_ONLY = "i2c"
    TEST_ONLY = "display"
    TEST_ONLY = "touch"
    TEST_ONLY = "audio"
    TEST_ONLY = "buttons"
    TEST_ONLY = "encoder"
    TEST_ONLY = "neopixel"
    TEST_ONLY = "wake"
    TEST_ONLY = ""          (run all — default)
"""

import gc
import os
import time
import board
import busio
import digitalio

from hardware_config import VARIANTS, DEFAULT_VARIANT

# ---------------------------------------------------------------------------
# Test bookkeeping
# ---------------------------------------------------------------------------

passed = 0
failed = 0
skipped = 0

# Shared hardware objects to avoid "pin in use" conflicts between tests
_shared_pins = {}  # pin_name -> DigitalInOut object


def test(name, condition, detail=""):
    """Record and print a single PASS/FAIL assertion."""
    global passed, failed
    if condition:
        passed += 1
        print("  PASS:", name)
    else:
        failed += 1
        msg = "  FAIL: " + name
        if detail:
            msg += " (" + detail + ")"
        print(msg)


def skip(name, reason="not configured for this variant"):
    """Record and print a skipped test."""
    global skipped
    skipped += 1
    print("  SKIP:", name, "-", reason)


def section(title):
    """Print a section header."""
    print()
    print("-" * 40)
    print(title)
    print("-" * 40)


def _pin(name):
    """Resolve pin name string to board pin. Returns None if name is None."""
    if name is None:
        return None
    return getattr(board, name)


def _get_output_pin(name):
    """Get or create a DigitalInOut OUTPUT pin, reusing across tests."""
    if name is None:
        return None
    if name in _shared_pins:
        return _shared_pins[name]
    pin = digitalio.DigitalInOut(_pin(name))
    pin.direction = digitalio.Direction.OUTPUT
    _shared_pins[name] = pin
    return pin


# ---------------------------------------------------------------------------
# Test 1: I2C Bus Scan
# ---------------------------------------------------------------------------

def test_i2c(config):
    """Scan the I2C bus and verify expected devices are present.

    Returns the I2C bus object for reuse by other tests.
    """
    section("TEST: I2C Bus Scan")

    scl = _pin(config.get("i2c_scl"))
    sda = _pin(config.get("i2c_sda"))
    if scl is None or sda is None:
        skip("I2C bus", "no I2C pins configured")
        return None

    i2c = None
    try:
        i2c = busio.I2C(scl, sda, frequency=config.get("i2c_freq", 400_000))
        test("I2C bus created", True)
    except Exception as e:
        test("I2C bus created", False, str(e))
        return None

    # Reset touch controller before scanning (it won't appear otherwise)
    rst = _get_output_pin(config.get("touch_rst"))
    if rst:
        rst.value = False
        time.sleep(0.01)
        rst.value = True
        time.sleep(0.3)

    # Scan
    while not i2c.try_lock():
        pass
    try:
        found = i2c.scan()
    finally:
        i2c.unlock()

    found_hex = [hex(a) for a in found]
    print("  Found addresses:", found_hex)
    test("I2C scan completed", True)

    # Check expected devices
    if config.get("sound_system") == "ES8311":
        test("ES8311 codec at 0x18", 0x18 in found,
             "expected 0x18, found " + str(found_hex))

    if config.get("touch_screen", False):
        test("Touch controller at 0x38", 0x38 in found,
             "expected 0x38, found " + str(found_hex))

    return i2c


# ---------------------------------------------------------------------------
# Test 2: NeoPixel Status LED
# ---------------------------------------------------------------------------

def test_neopixel(config):
    """Cycle NeoPixel through colors to verify it works."""
    section("TEST: NeoPixel Status LED")

    neo_pin = _pin(config.get("neopixel_pin"))
    if neo_pin is None:
        skip("NeoPixel")
        return

    try:
        import neopixel
        pixel = neopixel.NeoPixel(neo_pin, 1, brightness=0.05, auto_write=True)
        test("NeoPixel init", True)

        colors = [
            ("Red", (255, 0, 0)),
            ("Green", (0, 255, 0)),
            ("Blue", (0, 0, 255)),
            ("Yellow", (255, 255, 0)),
            ("White", (255, 255, 255)),
        ]
        for name, color in colors:
            pixel[0] = color
            print("    NeoPixel:", name)
            time.sleep(0.5)
        pixel[0] = (0, 0, 0)
        test("NeoPixel color cycle", True, "visual confirmation needed")
    except Exception as e:
        test("NeoPixel color cycle", False, str(e))


# ---------------------------------------------------------------------------
# Test 3: Display
# ---------------------------------------------------------------------------

def test_display(config):
    """Initialize display, cycle solid colors, then load background image."""
    section("TEST: Display")

    import displayio
    import fourwire

    displayio.release_displays()

    # SPI bus
    try:
        spi_kwargs = {"MOSI": _pin(config["lcd_mosi"])}
        miso = _pin(config.get("lcd_miso"))
        if miso:
            spi_kwargs["MISO"] = miso
        spi = busio.SPI(_pin(config["lcd_sclk"]), **spi_kwargs)
        test("Display SPI init", True)
    except Exception as e:
        test("Display SPI init", False, str(e))
        return

    # FourWire bus
    try:
        fw_kwargs = {
            "command": _pin(config["lcd_dc"]),
            "chip_select": _pin(config["lcd_cs"]),
        }
        reset = _pin(config.get("lcd_reset"))
        if reset:
            fw_kwargs["reset"] = reset
        display_bus = fourwire.FourWire(spi, **fw_kwargs)
        test("Display FourWire bus", True)
    except Exception as e:
        test("Display FourWire bus", False, str(e))
        return

    # ILI9341 init
    try:
        import adafruit_ili9341
        width = config["screen_width"]
        height = config["screen_height"]
        display = adafruit_ili9341.ILI9341(
            display_bus,
            width=width,
            height=height,
            rotation=config["display_rotation"],
        )
        if config.get("display_inverted", False):
            display_bus.send(0x21, b"")
        test("ILI9341 init ({}x{}, rot={})".format(
            width, height, config["display_rotation"]), True)
    except Exception as e:
        test("ILI9341 init", False, str(e))
        return

    # Backlight
    bl_pin = _pin(config.get("lcd_backlight"))
    if bl_pin:
        bl = digitalio.DigitalInOut(bl_pin)
        bl.direction = digitalio.Direction.OUTPUT
        bl.value = True
        test("Backlight enabled", True)

    # Color fill test
    splash = displayio.Group()
    display.root_group = splash

    colors = [
        ("Red", 0xFF0000),
        ("Green", 0x00FF00),
        ("Blue", 0x0000FF),
        ("White", 0xFFFFFF),
        ("Black", 0x000000),
    ]

    bitmap = displayio.Bitmap(width, height, 1)
    palette = displayio.Palette(1)
    grid = displayio.TileGrid(bitmap, pixel_shader=palette)
    splash.append(grid)

    for name, color in colors:
        palette[0] = color
        print("    Display fill:", name)
        time.sleep(0.5)

    test("Color fill cycle", True, "visual confirmation needed")

    # Background image
    while len(splash):
        splash.pop()
    gc.collect()

    img_path = config.get("background_image", "")
    try:
        odb = displayio.OnDiskBitmap(img_path)
        face = displayio.TileGrid(odb, pixel_shader=odb.pixel_shader)
        splash.append(face)
        test("Background image loaded ({})".format(img_path), True)
    except Exception as e:
        test("Background image loaded ({})".format(img_path), False, str(e))


# ---------------------------------------------------------------------------
# Test 4: Touch Screen
# ---------------------------------------------------------------------------

def test_touch(config, i2c):
    """Initialize touch controller and read touch points for 10 seconds."""
    section("TEST: Touch Screen")

    if not config.get("touch_screen", False):
        skip("Touch screen")
        return

    if i2c is None:
        test("Touch screen", False, "I2C bus not available")
        return

    # Reset touch controller (reuses shared pin from I2C test)
    rst = _get_output_pin(config.get("touch_rst"))
    if rst:
        rst.value = False
        time.sleep(0.01)
        rst.value = True
        time.sleep(0.3)

    try:
        import adafruit_focaltouch
        touch = adafruit_focaltouch.Adafruit_FocalTouch(i2c)
        test("Touch controller init", True)
    except Exception as e:
        test("Touch controller init", False, str(e))
        return

    # Read calibration settings
    swap_xy = config.get("touch_swap_xy", False)
    flip_x = config.get("touch_flip_x", False)
    flip_y = config.get("touch_flip_y", False)
    width = config["screen_width"]
    height = config["screen_height"]

    print("  Touch the screen for 10 seconds...")
    print("  Calibration: swap_xy={}, flip_x={}, flip_y={}".format(
        swap_xy, flip_x, flip_y))
    touch_count = 0
    end_time = time.monotonic() + 10

    while time.monotonic() < end_time:
        touches = touch.touches
        if touches:
            point = touches[0]
            raw_x = point["x"]
            raw_y = point["y"]

            # Apply coordinate mapping
            if swap_xy:
                sx, sy = raw_y, raw_x
            else:
                sx, sy = raw_x, raw_y
            if flip_x:
                sx = width - 1 - sx
            if flip_y:
                sy = height - 1 - sy

            print("    raw=({},{}) screen=({},{})".format(
                raw_x, raw_y, sx, sy))
            touch_count += 1
            time.sleep(0.3)  # debounce for readability
        time.sleep(0.01)

    test("Touch events received", touch_count > 0,
         "{} touches detected".format(touch_count))


# ---------------------------------------------------------------------------
# Test 5: Audio
# ---------------------------------------------------------------------------

def test_audio(config, i2c):
    """Test audio codec init, tone generation, and MP3 playback."""
    section("TEST: Audio")

    import audiobusio
    import audiocore
    import array
    import math

    # Codec init (ES8311 only)
    codec = None
    if config["sound_system"] == "ES8311":
        if i2c is None:
            test("ES8311 codec", False, "I2C bus not available")
            return
        try:
            from es8311 import ES8311
            codec = ES8311(i2c)
            codec.init(sample_rate=config["codec_sample_rate"], bits=16)
            codec.set_volume(config["volume"])
            codec.mute(False)
            test("ES8311 codec init", True)

            # Verify chip responds by reading register 0
            chip_val = codec._read_reg(0x00)
            test("ES8311 register read (0x{:02X})".format(chip_val),
                 chip_val != 0x00 and chip_val != 0xFF)
        except Exception as e:
            test("ES8311 codec init", False, str(e))
            return
    else:
        skip("ES8311 codec", "sound_system=" + config["sound_system"])

    # Amplifier
    amp_en = None
    if config.get("amp_en_pin"):
        amp_en = digitalio.DigitalInOut(_pin(config["amp_en_pin"]))
        amp_en.direction = digitalio.Direction.OUTPUT
        amp_en.value = not config.get("amp_en_active_low", True)
        test("Amplifier enabled", True)

    # I2S output
    audio = None
    try:
        mclk = _pin(config.get("i2s_mclk"))
        kwargs = {}
        if mclk is not None:
            kwargs["main_clock"] = mclk
        audio = audiobusio.I2SOut(
            _pin(config["i2s_bclk"]),
            _pin(config["i2s_ws"]),
            _pin(config["i2s_dout"]),
            **kwargs,
        )
        test("I2S output init", True)
    except Exception as e:
        test("I2S output init", False, str(e))
        return

    # Tone test (440 Hz for 2 seconds)
    try:
        frequency = 440
        sample_rate = config["codec_sample_rate"]
        length = sample_rate // frequency
        if length < 2:
            length = 2
        sine_wave = array.array("h", [0] * length)
        for i in range(length):
            sine_wave[i] = int(
                math.sin(math.pi * 2 * i / length) * 0.3 * (2 ** 15 - 1)
            )
        tone = audiocore.RawSample(sine_wave, sample_rate=sample_rate)
        audio.play(tone, loop=True)
        print("    Playing 440 Hz tone for 2 seconds...")
        time.sleep(2)
        audio.stop()
        test("440 Hz tone playback", True, "audible confirmation needed")
    except Exception as e:
        test("440 Hz tone playback", False, str(e))

    # MP3 test
    try:
        import audiomp3
        import button_config
        sound_file = button_config.button_sound[0]
        print("    Playing MP3:", sound_file)
        f = open(sound_file, "rb")
        try:
            mp3 = audiomp3.MP3Decoder(f)
            mp3_rate = mp3.sample_rate
            print("    MP3 sample rate:", mp3_rate, "Hz")

            # Re-init codec if rate differs
            if codec and mp3_rate != config["codec_sample_rate"]:
                print("    Switching codec to", mp3_rate, "Hz")
                codec.init(sample_rate=mp3_rate, bits=16)
                codec.set_volume(config["volume"])
                codec.mute(False)

            audio.play(mp3)
            while audio.playing:
                time.sleep(0.01)
            test("MP3 playback ({})".format(sound_file), True)
        finally:
            f.close()
    except Exception as e:
        test("MP3 playback", False, str(e))

    # Cleanup
    audio.stop()
    audio.deinit()
    if amp_en:
        amp_en.value = config.get("amp_en_active_low", True)  # Disable amp


# ---------------------------------------------------------------------------
# Test 6: Physical Buttons (hardware decoder)
# ---------------------------------------------------------------------------

def test_buttons(config):
    """Poll hardware button decoder for 10 seconds."""
    section("TEST: Physical Buttons")

    if config.get("max_buttons", 0) == 0:
        skip("Physical buttons", "max_buttons=0")
        return

    data_pin_names = config.get("button_data_pins", [])
    int_pin_name = config.get("button_int_pin")
    latch_pin_name = config.get("button_latch_reset_pin")

    if not data_pin_names or not int_pin_name:
        skip("Physical buttons", "pins not configured")
        return

    # Init data pins
    data_pins = []
    for name in data_pin_names:
        pin = digitalio.DigitalInOut(_pin(name))
        pin.direction = digitalio.Direction.INPUT
        pin.pull = digitalio.Pull.DOWN
        data_pins.append(pin)
    test("Button data pins init ({})".format(len(data_pins)), True)

    # Interrupt pin
    int_pin = digitalio.DigitalInOut(_pin(int_pin_name))
    int_pin.direction = digitalio.Direction.INPUT
    int_pin.pull = digitalio.Pull.DOWN
    test("Button interrupt pin init", True)

    # Latch reset pin
    latch = None
    if latch_pin_name:
        latch = digitalio.DigitalInOut(_pin(latch_pin_name))
        latch.direction = digitalio.Direction.OUTPUT
        latch.value = False

    print("  Press buttons for 10 seconds...")
    press_count = 0
    end_time = time.monotonic() + 10

    while time.monotonic() < end_time:
        if int_pin.value:
            button_number = 0
            for i, pin in enumerate(data_pins):
                if pin.value:
                    button_number |= 1 << i
            print("    Button pressed:", button_number)
            press_count += 1

            if latch:
                latch.value = True
                time.sleep(0.1)
                latch.value = False
            time.sleep(0.3)
        time.sleep(0.01)

    test("Button presses received", press_count > 0,
         "{} presses detected".format(press_count))


# ---------------------------------------------------------------------------
# Test 7: Rotary Encoder
# ---------------------------------------------------------------------------

def test_encoder(config):
    """Poll rotary encoder rotation and button for 10 seconds."""
    section("TEST: Rotary Encoder")

    if not config.get("rotary_encoder", False):
        skip("Rotary encoder")
        return

    import rotaryio

    try:
        encoder = rotaryio.IncrementalEncoder(
            _pin(config["encoder_pin_a"]),
            _pin(config["encoder_pin_b"]),
        )
        test("Encoder init", True)
    except Exception as e:
        test("Encoder init", False, str(e))
        return

    # Encoder button
    enc_button = None
    btn_pin = _pin(config.get("encoder_button_pin"))
    if btn_pin:
        enc_button = digitalio.DigitalInOut(btn_pin)
        enc_button.direction = digitalio.Direction.INPUT
        enc_button.pull = digitalio.Pull.UP

    print("  Turn encoder and press button for 10 seconds...")
    last_position = encoder.position
    last_button = enc_button.value if enc_button else True
    rotation_detected = False
    button_detected = False
    end_time = time.monotonic() + 10

    while time.monotonic() < end_time:
        pos = encoder.position
        if pos != last_position:
            print("    Encoder position:", pos, "(delta:", pos - last_position, ")")
            last_position = pos
            rotation_detected = True

        if enc_button:
            btn = enc_button.value
            if btn != last_button:
                last_button = btn
                if not btn:
                    print("    Encoder button pressed")
                    button_detected = True
        time.sleep(0.01)

    test("Encoder rotation detected", rotation_detected)
    if enc_button:
        test("Encoder button detected", button_detected)


# ---------------------------------------------------------------------------
# Test 8: Wake Button
# ---------------------------------------------------------------------------

def test_wake(config):
    """Wait for wake button press for 5 seconds."""
    section("TEST: Wake Button")

    wake_pin = _pin(config.get("wake_button_pin"))
    if wake_pin is None:
        skip("Wake button")
        return

    try:
        btn = digitalio.DigitalInOut(wake_pin)
        btn.direction = digitalio.Direction.INPUT
        btn.pull = digitalio.Pull.UP
        test("Wake button pin init", True)
    except Exception as e:
        test("Wake button pin init", False, str(e))
        return

    print("  Press wake button (GPIO0/BOOT) within 5 seconds...")
    last_val = btn.value
    press_detected = False
    end_time = time.monotonic() + 5

    while time.monotonic() < end_time:
        val = btn.value
        if val != last_val:
            last_val = val
            if not val:
                print("    Wake button pressed!")
                press_detected = True
                break
        time.sleep(0.01)

    test("Wake button press detected", press_detected,
         "timed out" if not press_detected else "")


# ---------------------------------------------------------------------------
# Test 9: Sleep / Wake
# ---------------------------------------------------------------------------

def test_sleep(config):
    """Test sleep mode: power down peripherals, sleep 5s or until touch/button.

    Bypasses the USB-connected check so you can test without a battery.
    NOTE: On USB, light sleep may cause a soft reboot — that is expected
    and counts as a PASS (the device woke up).
    """
    section("TEST: Sleep / Wake")

    if not config.get("sleep_enabled", False):
        skip("Sleep", "sleep_enabled=False")
        return

    import alarm
    import alarm.pin
    import alarm.time
    import neopixel

    # Turn off NeoPixel
    neo_pin = _pin(config.get("neopixel_pin"))
    pixel = None
    if neo_pin:
        pixel = neopixel.NeoPixel(neo_pin, 1, brightness=0.05, auto_write=True)
        pixel[0] = (0, 0, 0)
        test("NeoPixel off", True)

    # Turn off backlight (hold pin low through sleep — do NOT deinit)
    bl = None
    bl_pin = _pin(config.get("lcd_backlight"))
    if bl_pin:
        bl = digitalio.DigitalInOut(bl_pin)
        bl.switch_to_output(value=False)
        test("Backlight off", True)

    # Disable amplifier (hold pin through sleep)
    amp = None
    amp_pin = _pin(config.get("amp_en_pin"))
    if amp_pin:
        amp = digitalio.DigitalInOut(amp_pin)
        active_low = config.get("amp_en_active_low", True)
        amp.switch_to_output(value=active_low)  # Disabled state
        test("Amplifier disabled", True)

    # Build wake alarms
    alarms = []

    # Timer alarm: 5 second safety net
    timer_alarm = alarm.time.TimeAlarm(monotonic_time=time.monotonic() + 5)
    alarms.append(timer_alarm)
    print("  Timer alarm: 5 seconds")

    # Pin alarms for touch and boot button
    for pin_name in config.get("sleep_wake_pins", []):
        pin = _pin(pin_name)
        if pin:
            a = alarm.pin.PinAlarm(pin=pin, value=False, pull=True)
            alarms.append(a)
            print("  Pin alarm:", pin_name)

    test("Wake alarms configured ({})".format(len(alarms)), len(alarms) > 0)

    # Enter light sleep
    print()
    print("  >>> ENTERING LIGHT SLEEP <<<")
    print("  Screen will go dark for up to 5 seconds.")
    print("  Touch the screen or press BOOT to wake early.")
    print()
    time.sleep(0.5)  # Let serial flush

    triggered = alarm.light_sleep_until_alarms(*alarms)

    # If we get here, light sleep worked and we woke up
    print()
    print("  >>> WOKE UP <<<")
    if triggered:
        print("  Wake source:", triggered)
        if isinstance(triggered, alarm.time.TimeAlarm):
            test("Wake from timer (5s elapsed)", True)
        elif isinstance(triggered, alarm.pin.PinAlarm):
            test("Wake from pin (touch or button)", True)
        else:
            test("Wake from unknown source", True)
    else:
        test("Wake (no alarm info)", True)

    # Restore backlight
    if bl:
        bl.value = True
        bl.deinit()
        test("Backlight restored", True)

    # Restore NeoPixel
    if pixel:
        pixel[0] = (0, 255, 0)  # Green = pass
        test("NeoPixel restored", True)

    # Restore amplifier
    if amp:
        active_low = config.get("amp_en_active_low", True)
        amp.value = not active_low  # Enabled state
        amp.deinit()


# ---------------------------------------------------------------------------
# Test Runner
# ---------------------------------------------------------------------------

def run_all(variant_name=None):
    """Run the full test suite for the specified variant."""
    global passed, failed, skipped
    passed = 0
    failed = 0
    skipped = 0

    if variant_name is None:
        variant_name = DEFAULT_VARIANT

    config = VARIANTS[variant_name]

    # Check settings.toml for single-test mode
    test_only = os.getenv("TEST_ONLY", "") or ""

    def should_run(name):
        return test_only == "" or test_only == name

    print("=" * 50)
    print("AAC Device Hardware Test Suite")
    print("Variant:", config["name"])
    if test_only:
        print("Running single test:", test_only)
    print("=" * 50)

    # I2C is shared — create once, pass to tests that need it
    i2c = None
    if should_run("i2c"):
        i2c = test_i2c(config)
        gc.collect()

    # Lazy-create I2C if needed but i2c test was skipped
    if i2c is None and (should_run("touch") or should_run("audio")):
        scl = _pin(config.get("i2c_scl"))
        sda = _pin(config.get("i2c_sda"))
        if scl and sda:
            rst = _get_output_pin(config.get("touch_rst"))
            if rst:
                rst.value = False
                time.sleep(0.01)
                rst.value = True
                time.sleep(0.3)
            i2c = busio.I2C(scl, sda, frequency=config.get("i2c_freq", 400_000))

    if should_run("neopixel"):
        test_neopixel(config)
        gc.collect()

    if should_run("display"):
        test_display(config)
        gc.collect()

    if should_run("touch"):
        test_touch(config, i2c)
        gc.collect()

    if should_run("audio"):
        test_audio(config, i2c)
        gc.collect()

    if should_run("buttons"):
        test_buttons(config)
        gc.collect()

    if should_run("encoder"):
        test_encoder(config)
        gc.collect()

    if should_run("wake"):
        test_wake(config)
        gc.collect()

    if should_run("sleep"):
        test_sleep(config)
        gc.collect()

    # Summary
    total = passed + failed + skipped
    print()
    print("=" * 50)
    print("Results: {} passed, {} failed, {} skipped, {} total".format(
        passed, failed, skipped, total))
    if failed == 0:
        print("ALL TESTS PASSED")
    else:
        print("SOME TESTS FAILED")
    print("=" * 50)


# Run if deployed as code.py
run_all()

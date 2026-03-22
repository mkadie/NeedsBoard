# AAC Device — Guide for Teachers and Parents

## What is This?

This is an AAC (Augmentative and Alternative Communication) device that
helps people communicate by selecting pictures on a screen. When a
picture is selected, the device speaks a word or phrase out loud.

The device runs on several different hardware platforms — from touch
screens to devices with rotary encoders and physical buttons. No matter
which version you have, the menus, sounds, and configuration work the
same way.

The device is fully customizable — you can change what pictures appear,
what sounds they make, and how the menus are organized. **No programming
knowledge is needed.** Everything is done by editing simple text files
and adding picture and sound files.

---

## Quick Start

### What You See

When the device turns on, it shows the **Base Menu** — a grid of
pictures the user can touch. For example:

```
+----------+----------+----------+----------+
| Thirsty  | Hungry   |   More   | Bathroom |
+----------+----------+----------+----------+
|  Stinky  |   Yes    |    No    |  Please  |
+----------+----------+----------+----------+
```

- Touch or select a picture → the device says that word
- Select "More" → opens a submenu with more choices (like Food & Drink)
- Select "Back" on any submenu → returns to the main screen

### The Boot Button

On touch screen devices, the small button on the side (labeled BOOT or
KEY2) is an extra button that can be assigned to any action. By default
it says "Read to me."

On encoder-based devices, the encoder button is used to select the
currently highlighted item.

---

## How the Files are Organized

When you plug the device into a computer via USB, it appears as a drive
called **CIRCUITPY**. Inside you will find:

```
CIRCUITPY/
    config.txt              ← Your settings file (volume, sleep, etc.)
    menus/                  ← All your menus live here
        base.menu           ← The main screen (edit this!)
        food.menu           ← Food & Drink submenu
        images/             ← Pictures for the buttons
            food/           ← Pictures for food menu
        sounds/             ← Sound files
            food/           ← Sounds for food menu
    button_sounds/          ← Original sound files
    needs_small.bmp         ← Main screen background picture
    code.py                 ← The program (don't edit this)
    ...other system files
```

**You will mostly work with the `menus/` folder and `config.txt`.**
The menus folder has all the menus, pictures, and sounds. The config
file lets you adjust device behavior without touching any code.

---

## Editing a Menu

### Opening a Menu File

Menu files end in `.menu` and can be opened with any text editor:
- **Windows**: Notepad, Notepad++
- **Mac**: TextEdit (use Format → Make Plain Text)
- **Chromebook**: Text app
- **Any computer**: VS Code, Sublime Text

### Understanding the Format

Here is a simple menu file with comments explaining each part:

```
# Lines starting with # are notes — the device ignores them.
# Use them to leave reminders for yourself!

# This section describes the menu itself:
[menu]
name = Food & Drink
type = grid
columns = 4
rows = 2
back = base.menu
background = images/food/food_board.bmp

# Each picture/button gets its own section.
# The name in [brackets] is just for your reference.

[water]
label = Water
image = images/food/water.bmp
sound = sounds/food/water.mp3
position = 1

[juice]
label = Juice
image = images/food/juice.bmp
sound = sounds/food/juice.mp3
position = 2
```

### Key Rules

1. **Every menu starts with `[menu]`** — this describes the menu itself
2. **Every button gets a `[name]` section** — the name in brackets is
   just a label for you; the user sees the `label` text
3. **Positions start at 1** — not 0. Position 1 is the top-left corner
4. **Lines starting with `#` are notes** — add as many as you want
5. **Blank lines are fine** — add them for readability

### Position Numbers

For a 4-column × 2-row grid, positions are numbered like this:

```
+--------+--------+--------+--------+
|   1    |   2    |   3    |   4    |
+--------+--------+--------+--------+
|   5    |   6    |   7    |   8    |
+--------+--------+--------+--------+
```

---

## Common Tasks

### Changing What a Button Says

Find the button's section in the `.menu` file and change the `sound`
line to point to a different sound file.

**Before:**
```
[water]
label = Water
sound = sounds/food/water.mp3
position = 1
```

**After:**
```
[water]
label = Water Please
sound = sounds/food/water_please.mp3
position = 1
```

Don't forget to put the new sound file (`water_please.mp3`) in the
`sounds/food/` folder!

### Adding a New Button

1. Add a new section to the `.menu` file:

```
[cookie]
label = Cookie
image = images/food/cookie.bmp
sound = sounds/food/cookie.mp3
position = 3
```

2. Put the picture file (`cookie.bmp`) in the `images/food/` folder
3. Put the sound file (`cookie.mp3`) in the `sounds/food/` folder
4. Safely eject and reconnect the device to test

### Removing a Button

Delete the entire section (from `[name]` to the last line before the
next `[name]`). Or simply add `#` at the start of every line to
"comment it out" — this hides it without deleting it, so you can
bring it back later:

```
# [cookie]
# label = Cookie
# image = images/food/cookie.bmp
# sound = sounds/food/cookie.mp3
# position = 3
```

### Swapping Two Buttons

Just change their `position` numbers. If you want Water and Juice to
swap places:

**Before:**
```
[water]
position = 1

[juice]
position = 2
```

**After:**
```
[water]
position = 2

[juice]
position = 1
```

### Creating a New Submenu

1. Create a new `.menu` file (e.g., `feelings.menu`) in the `menus/`
   folder. Copy an existing menu file as a starting point.

2. Change the `[menu]` section:
```
[menu]
name = Feelings
type = grid
columns = 4
rows = 2
back = base.menu
background = images/feelings/feelings_board.bmp
```

3. Add your buttons (see "Adding a New Button" above)

4. Always include a **Back button** so the user can return:
```
[back_button]
label = Back
image = images/back.bmp
position = 8
back =
```

5. Link to it from the base menu by adding `submenu = feelings.menu`
   to a button:
```
[feelings]
label = Feelings
image = images/feelings.bmp
submenu = feelings.menu
position = 7
```

---

## Pictures and Sounds

### Picture Requirements

- **Format**: BMP (bitmap) files work best
- **Size**: 320×240 pixels for full-screen backgrounds; 80×120 pixels
  for individual button images
- **Colors**: Up to 256 colors. More colors = better looking but
  slightly larger files
- **Tips**:
  - Use clear, simple images with high contrast
  - Real photos of familiar objects work well
  - Keep backgrounds simple so the pictures stand out
  - The device has a small screen — avoid tiny details

### Sound Requirements

- **Format**: MP3 files
- **Sample rate**: 44100 Hz (this is important — other rates may not
  play correctly)
- **Length**: Keep sounds under 5 seconds for best results
- **Tips**:
  - Record in a quiet room
  - Speak clearly and at a natural pace
  - Use a familiar voice (parent, teacher, sibling, or the user
    themselves)
  - Test each sound after adding it

### Creating Sounds

**Option 1: Record your own voice**
Use any voice recorder app on your phone or computer. Save as MP3 at
44100 Hz. Free apps that work well:
- Voice Memos (iPhone) — export as MP3
- Easy Voice Recorder (Android)
- Audacity (computer) — free, works on Windows/Mac/Linux

**Option 2: Text-to-speech**
Use a text-to-speech website to generate MP3 files:
- Google Translate (click the speaker icon, then use a screen recorder)
- Natural Reader (naturalreaders.com)
- Many other free TTS websites

Make sure to save the output as MP3 at 44100 Hz. If your file plays at
the wrong speed, it is probably at the wrong sample rate.

### Creating Background Images

The background image is what fills the entire screen. It should show
all the buttons in their grid positions with labels.

**Easy method**: Use any image editor (even PowerPoint or Google Slides)
to create a grid with pictures and labels, export as PNG, then convert:

1. Create your image at 1280×960 pixels (or any 4:3 ratio)
2. Save as PNG
3. Use an online converter to convert PNG → BMP
4. Resize to 320×240 pixels

**Note**: The device can display BMP files with up to 256 colors.
If your image looks wrong, try reducing the color count.

---

## Button Options Reference

Every button can have these settings:

| Setting | What It Does | Example |
|---------|-------------|---------|
| `label` | The name (for your reference) | `label = Water` |
| `position` | Where on the grid (1-8 for 4×2) | `position = 1` |
| `image` | Picture file to show | `image = images/food/water.bmp` |
| `sound` | Sound file to play | `sound = sounds/food/water.mp3` |
| `vibrate` | Make the device vibrate | `vibrate = short` |
| `light` | Light up in a color | `light = blue` |
| `submenu` | Open another menu | `submenu = food.menu` |
| `back` | Go back to previous menu | `back =` |
| `text` | Show text on screen | `text = I want water` |
| `text_description` | Description shown on OLED screens and as hint text on color screens | `text_description = I need the bathroom` |

### Vibration Options
- `short` — quick buzz
- `long` — longer buzz
- `double` — two quick buzzes

### Light Color Options
- `red`, `green`, `blue`, `yellow`, `orange`, `purple`, `pink`, `white`
- Or use a hex color code: `light = #FF6600`

---

## Configuration (config.txt)

The `config.txt` file lives in the root of the CIRCUITPY drive. It lets
you customize how the device behaves without editing any code. Open it
with any text editor — it works just like the `.menu` files.

Here is an example `config.txt` with all the available settings:

```
# Device configuration
# Lines starting with # are comments — the device ignores them.

sleep_enabled = true
sleep_timeout = 120

volume = 75

debounce_time = 200

encoder_direction_flip = false

show_border = false

display_hint_text = true

start_menu = base.menu

emergency_push_enabled = true
emergency_push_sound = sounds/help_me.mp3
```

### Settings Explained

| Setting | What It Does | Default |
|---------|-------------|---------|
| `sleep_enabled` | Whether the device goes to sleep after inactivity | `true` |
| `sleep_timeout` | Seconds of inactivity before sleep (e.g., 120 = 2 minutes) | `120` |
| `volume` | Speaker volume, 0 (silent) to 100 (max) | `75` |
| `debounce_time` | Milliseconds to ignore repeated presses (prevents accidental double-taps) | `200` |
| `encoder_direction_flip` | Flip the scroll direction of the rotary encoder (`true` or `false`) | `false` |
| `show_border` | On OLED screens: `true` shows a bordered single-line display; `false` shows 3-line scrolling mode (previous / current / next item) | `false` |
| `display_hint_text` | On color screens: show the `text_description` as an overlay on top of the image | `true` |
| `start_menu` | Which menu file loads first when the device turns on | `base.menu` |
| `emergency_push_enabled` | Enable the emergency push feature (see below) | `true` |
| `emergency_push_sound` | Sound file to play for emergency push | `sounds/help_me.mp3` |

You only need to include the settings you want to change. If a setting
is missing from your `config.txt`, the device uses its default value.

---

## Emergency Push

The emergency push feature gives the user a quick way to call for help
the moment the device turns on — before any menus appear.

**How it works:** Hold down the encoder button (or the boot button on
touch screen devices) while the device is powering up. If the button is
still held after about 1.2 seconds, the device immediately plays the
emergency sound. No menus, no navigation needed.

This is especially useful in situations where the user needs immediate
attention and cannot wait to navigate through menus.

### Configuring Emergency Push

In your `config.txt`:

```
emergency_push_enabled = true
emergency_push_sound = sounds/help_me.mp3
```

- Set `emergency_push_enabled = false` to turn it off entirely
- Change `emergency_push_sound` to any MP3 file on the device

---

## Supported Devices

The same menu files and configuration work across several different
hardware platforms. The device auto-detects which hardware it is running
on — you do not need to change anything when moving your files between
devices.

| Device | Screen | Input Method | Notes |
|--------|--------|-------------|-------|
| **CYD_PLUS** | 320×240 color touch screen | Touch | ESP32-S3 based, the original touch screen version |
| **FRUITJAM_V2** | 160×128 color LCD | Rotary encoder | Compact color screen with TLV320 DAC for audio |
| **RP2350_OLED_BADGE_V3** | 128×32 monochrome OLED | Rotary encoder | Small badge-style device, shows text instead of images |
| **RP2350_V2** | 320×240 color LCD | Physical buttons + encoder | Large screen with button controls |

### OLED Text Display

On devices with a small OLED screen (like the RP2350_OLED_BADGE_V3),
there is not enough room to show pictures. Instead, the device shows
text from each button's `text_description` field.

There are two display modes, controlled by the `show_border` setting in
`config.txt`:

- **`show_border = true`** — Bordered mode. Shows the current item's
  text inside a border, one item at a time.
- **`show_border = false`** — 3-line scrolling mode. Shows the previous
  item, the current item (highlighted), and the next item. This gives
  the user more context about what is nearby.

**Tip:** If you are using an OLED device, make sure every button has a
`text_description` so the user can tell the options apart. For example:

```
[bathroom]
label = Bathroom
image = images/bathroom.bmp
sound = sounds/i_need_the_bathroom.mp3
text_description = I need the bathroom
position = 4
```

### Encoder Direction

If the rotary encoder scrolls in the opposite direction from what feels
natural, you can flip it in `config.txt`:

```
encoder_direction_flip = true
```

This reverses which way turning the knob moves through the menu items.

---

## Troubleshooting

### The device doesn't start after I edited a file
- Check for typos in the `.menu` file
- Make sure every `[section]` has matching brackets
- Make sure every line with `=` has a space before and after it
- The device will fall back to the original buttons if it can't read
  the menu files

### A sound doesn't play
- Check that the file exists in the correct folder
- Check that the filename in the `.menu` file matches exactly
  (including uppercase/lowercase)
- Make sure the sound file is MP3 format at 44100 Hz
- Try playing the file on your computer first to make sure it works

### A picture doesn't show
- Check that the file exists in the correct folder
- Make sure it is BMP format (not PNG or JPG)
- Try a smaller image (320×240 or 80×120 pixels)

### The touch doesn't match the right button
- The touch calibration may need adjusting — contact the person who
  set up the device

### I want to start over
- The device keeps a backup mode using `button_config.py`. If you
  delete or rename the `menus/` folder, the device will automatically
  fall back to the original 8-button layout.

---

## Tips for Success

### For the User
- **Start simple**: 4-8 buttons is plenty to begin with
- **Be consistent**: Don't change the layout frequently
- **Practice together**: Model using the device yourself
- **Celebrate communication**: Every press is communication!

### For the Vocabulary
- **Core words first**: yes, no, more, help, stop, go, want
- **Add topic boards gradually**: food, feelings, activities, people
- **Match existing boards**: If the user already has a paper
  communication board, match that layout on the device
- **Include a "Back" button** on every submenu

### For the Setup
- **Test every button** after making changes
- **Keep backup copies** of your `.menu` files on your computer
- **Label the sound files clearly**: `i_want_water.mp3` is better
  than `sound7.mp3`
- **Use folders** to organize by topic: `sounds/food/`, `sounds/feelings/`

---

## Example: Adding a "Feelings" Menu from Scratch

Here is a step-by-step walkthrough of creating a new submenu:

### Step 1: Plan your buttons

Decide what feelings to include and sketch the layout:

```
+--------+--------+--------+--------+
| Happy  |  Sad   | Angry  | Scared |
+--------+--------+--------+--------+
| Tired  |  Sick  | Hungry |  Back  |
+--------+--------+--------+--------+
```

### Step 2: Gather your files

For each feeling, you need:
- A picture (BMP, 80×120 pixels)
- A sound (MP3, 44100 Hz) — e.g., "I feel happy"

Put pictures in `menus/images/feelings/`
Put sounds in `menus/sounds/feelings/`

Also create a background image (BMP, 320×240) showing all 8 buttons.
Put it in `menus/images/feelings/feelings_board.bmp`

### Step 3: Create the menu file

Create `menus/feelings.menu`:

```
# Feelings menu
# Created by: [your name]
# Date: [today's date]

[menu]
name = How I Feel
type = grid
columns = 4
rows = 2
back = base.menu
background = images/feelings/feelings_board.bmp

[happy]
label = Happy
image = images/feelings/happy.bmp
sound = sounds/feelings/i_feel_happy.mp3
light = green
position = 1

[sad]
label = Sad
image = images/feelings/sad.bmp
sound = sounds/feelings/i_feel_sad.mp3
light = blue
position = 2

[angry]
label = Angry
image = images/feelings/angry.bmp
sound = sounds/feelings/i_feel_angry.mp3
light = red
position = 3

[scared]
label = Scared
image = images/feelings/scared.bmp
sound = sounds/feelings/i_am_scared.mp3
position = 4

[tired]
label = Tired
image = images/feelings/tired.bmp
sound = sounds/feelings/i_am_tired.mp3
position = 5

[sick]
label = Sick
image = images/feelings/sick.bmp
sound = sounds/feelings/i_feel_sick.mp3
light = red
position = 6

[hungry]
label = Hungry
image = images/feelings/hungry.bmp
sound = sounds/feelings/i_am_hungry.mp3
position = 7

[back_button]
label = Back
image = images/feelings/back.bmp
position = 8
back =
```

### Step 4: Link it from the base menu

Open `menus/base.menu` and add or change a button to point to your
new menu:

```
[feelings]
label = Feelings
image = images/feelings.bmp
submenu = feelings.menu
position = 7
```

### Step 5: Test it

1. Safely eject the device from your computer
2. The device will restart automatically
3. Touch the "Feelings" button on the main screen
4. Verify each feeling button plays the right sound
5. Verify the "Back" button returns to the main screen

---

## Getting Help

If you run into problems or have questions:
- Check the troubleshooting section above
- Look at the existing `base.menu` and `food.menu` files as examples
- Report issues at: https://github.com/anthropics/claude-code/issues

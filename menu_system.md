# AAC Menu System Design

## Overview

This document describes the menu and configuration system for the AAC
(Augmentative and Alternative Communication) device. The system uses a
**HyperCard-like metaphor**: the user navigates between "cards" (menus),
each card showing a set of items they can press.

### Design Goals

1. **Readable by teachers and parents** — no programming knowledge required
2. **Easy to edit** — plain text files, clear syntax, lots of examples
3. **Flexible** — supports grids, scrollable lists, submenus, and future
   keyboard/TTS modes
4. **Transferable** — menu configurations can move between devices and be
   shared between classrooms
5. **Card/board compatible** — direct mapping to physical communication
   cards and boards, with future QR code support

### Key Concepts

| Term | Meaning |
|------|---------|
| **Press** | Any item the user can select (touch zone, physical button, list entry) |
| **Menu** | A collection of presses displayed as a grid (like a communication board) |
| **List** | A scrollable, sorted collection of presses (for literate users or large vocabularies) |
| **Action** | Something that happens when a press is activated (play sound, show image, etc.) |
| **Stack** | The full collection of menus and lists — like a deck of HyperCards |

---

## File Format: `.menu`

Menu files use a simple **INI-style** format chosen because:

- Teachers and parents already understand `name = value` patterns
- No brackets, braces, or quotes to get wrong (unlike JSON)
- Comments start with `#` for adding notes
- Sections are marked with `[square brackets]`
- Blank lines are ignored — add them freely for readability
- CircuitPython can parse it with a small, simple reader

### File Extension and Naming

- Menu files end in `.menu` (e.g., `base.menu`, `food.menu`)
- Use lowercase names with underscores: `daily_routine.menu`
- The starting menu is always `base.menu`

### Syntax Rules

```
# Lines starting with # are comments — use them freely!
# Blank lines are ignored

[section_name]
key = value
another_key = another value
```

- **Sections**: `[name]` on its own line starts a new section
- **Keys**: always lowercase with underscores (e.g., `sound_file`)
- **Values**: everything after the ` = ` (space-equals-space)
- **No quotes needed** around values
- **Lists of values**: separate with commas (e.g., `actions = sound, vibrate, light`)

---

## Directory Structure

All menu content lives under a `/menus/` directory on the device:

```
/menus/
    base.menu               <-- Starting menu (required)
    feelings.menu           <-- Submenu for feelings
    food.menu               <-- Submenu for food/drink
    daily_routine.menu      <-- Submenu for daily activities
    alphabet.menu           <-- Letter-by-letter spelling list
    words.menu              <-- Saved words list
    sentences.menu          <-- Sentence building list

    images/                 <-- Pictures for menu items
        thirsty.bmp
        hungry.bmp
        happy.bmp
        ...

    sounds/                 <-- Sound files for menu items
        thirsty.mp3
        hungry.mp3
        happy.mp3
        ...
```

**Organizing by topic**: For large vocabularies, group images and sounds
into subdirectories that mirror the menu structure:

```
/menus/
    food.menu
    images/food/
        milk.bmp
        juice.bmp
        cookie.bmp
    sounds/food/
        milk.mp3
        juice.mp3
        cookie.mp3
```

---

## Menu Types

### Grid Menu (type = grid)

A grid menu displays presses in a fixed grid, like a communication board.
Best for non-literate users and core vocabulary. Each press has a fixed
position on screen.

```
# ===================================================
#  Base Menu — the first screen the user sees
#  This is the "home" card of the device
# ===================================================

[menu]
name = Base Menu
type = grid
columns = 4
rows = 2
background = base_board.bmp

# ----- Row 1 -----

[thirsty]
label = Thirsty
image = images/thirsty.bmp
sound = sounds/thirsty.mp3
position = 1

[hungry]
label = Hungry
image = images/hungry.bmp
sound = sounds/hungry.mp3
position = 2

[more]
label = More
image = images/more.bmp
sound = sounds/more.mp3
position = 3

[bathroom]
label = Bathroom
image = images/bathroom.bmp
sound = sounds/bathroom.mp3
position = 4

# ----- Row 2 -----

[yes]
label = Yes
image = images/yes.bmp
sound = sounds/yes.mp3
vibrate = short
position = 5

[no]
label = No
image = images/no.bmp
sound = sounds/no.mp3
vibrate = short
position = 6

[feelings]
label = Feelings
image = images/feelings.bmp
sound = sounds/how_do_you_feel.mp3
submenu = feelings.menu
position = 7

[food]
label = Food & Drink
image = images/food.bmp
submenu = food.menu
position = 8
```

**Position numbering** for a 4x2 grid:

```
+--------+--------+--------+--------+
|   1    |   2    |   3    |   4    |
+--------+--------+--------+--------+
|   5    |   6    |   7    |   8    |
+--------+--------+--------+--------+
```

Positions are numbered left-to-right, top-to-bottom, starting at 1.

### List Menu (type = list)

A list menu displays items in a scrollable, **sorted** list. Best for
literate users, large vocabularies, or expanding categories. The device
automatically adds scroll controls.

```
# ===================================================
#  Food & Drink — scrollable list of food items
# ===================================================

[menu]
name = Food & Drink
type = list
back = base.menu

# Items are automatically sorted alphabetically.
# Position numbers are not needed — the sort order determines display.

[apple]
label = Apple
image = images/food/apple.bmp
sound = sounds/food/apple.mp3

[banana]
label = Banana
image = images/food/banana.bmp
sound = sounds/food/banana.mp3

[chocolate_milk]
label = Chocolate Milk
image = images/food/chocolate_milk.bmp
sound = sounds/food/i_want_chocolate_milk.mp3
vibrate = short

[cookie]
label = Cookie
image = images/food/cookie.bmp
sound = sounds/food/cookie.mp3

[juice]
label = Juice
image = images/food/juice.bmp
sound = sounds/food/juice.mp3

[milk]
label = Milk
image = images/food/milk.bmp
sound = sounds/food/milk.mp3

[water]
label = Water
image = images/food/water.bmp
sound = sounds/food/water.mp3
```

---

## Scrolling and Navigation

### Scroll Controls

Every list (and grids with more items than visible positions) gets
automatic scroll controls. The system provides these built-in presses:

| Control | What it does |
|---------|-------------|
| `scroll_up` or `+1` | Move highlight / selection up one item |
| `scroll_down` or `-1` | Move highlight / selection down one item |
| `select` | Activate the highlighted item |
| `page_up` | Jump up by one screen of items |
| `page_down` | Jump down by one screen of items |
| `back` | Return to the parent menu |

**Minimum controls**: `+1`, `-1`, `select` — these are always available.

**Extended controls**: `page_up`, `page_down` — added when the device
has enough press positions (5+ buttons or larger touch grids).

### Page Size

The number of items shown at once (and thus the page_up/page_down
jump distance) is determined by:

- **Touch screen grid**: `columns × rows` minus reserved positions for
  scroll controls
- **Physical buttons**: `max_buttons` minus reserved buttons for scroll
  controls
- **Rotary encoder**: shows 1 item at a time; rotate = scroll, press = select

The page size can also be set manually in the menu file:

```
[menu]
type = list
page_size = 6
```

### Scroll Layout on a Touch Grid

On a 4×2 grid showing a list, a typical layout reserves the right
column for navigation:

```
+----------+----------+----------+----------+
|  Item 1  |  Item 2  |  Item 3  |  ↑ Up    |
+----------+----------+----------+----------+
|  Item 4  |  Item 5  |  Item 6  |  ↓ Down  |
+----------+----------+----------+----------+
```

Or with back button:

```
+----------+----------+----------+----------+
|  ← Back  |  Item 1  |  Item 2  |  ↑ Up    |
+----------+----------+----------+----------+
|  Item 3  |  Item 4  |  Item 5  |  ↓ Down  |
+----------+----------+----------+----------+
```

### Rotary Encoder Navigation

When the device has a rotary encoder (`rotary_encoder = true` in
hardware config), **all menus behave like lists**:

- Rotate clockwise = next item (+1)
- Rotate counter-clockwise = previous item (-1)
- Press encoder button = select / activate
- The display shows the currently highlighted item large and centered
- Adjacent items can be shown smaller above/below if screen space allows

### Minimizing Presses

To help users find items quickly:

1. **Lists are always sorted** alphabetically by label
2. **Frequency sorting** (optional): items the user selects most often
   float to the top — set `sort = frequency` in the menu header
3. **Recent items** (optional): a "Recently Used" section at the top —
   set `show_recent = 3` to show the last 3 selections
4. **Jump-to-letter** (future): on keyboard-capable devices, press a
   letter to jump to that section of the list

---

## Actions

Every press can trigger **zero or more actions**. Actions happen in the
order listed. If no actions are specified, the press does nothing (useful
for placeholder/spacer items).

### Action Reference

| Action | Key | Values | Example |
|--------|-----|--------|---------|
| **Play sound** | `sound` | Path to MP3 file | `sound = sounds/thirsty.mp3` |
| **Vibrate** | `vibrate` | `short`, `long`, `double`, `pattern`, or `default` | `vibrate = short` |
| **Light** | `light` | Color name or hex code | `light = blue` |
| **Light pattern** | `light_pattern` | Named pattern | `light_pattern = rainbow` |
| **Display image** | `image` | Path to BMP file | `image = images/thirsty.bmp` |
| **Display text** | `text` | Text string to show on screen | `text = I am thirsty` |
| **Navigate to submenu** | `submenu` | Menu filename | `submenu = food.menu` |
| **Navigate to list** | `list` | Menu filename (type=list) | `list = food.menu` |
| **Go back** | `back` | (no value needed) | `back =` |
| **Speak text (TTS)** | `speak` | Text for text-to-speech (future) | `speak = I want chocolate milk` |
| **Display animation** | `animation` | Animation filename (future) | `animation = happy.gif` |

### Action Examples

**Simple sound button** — plays a sound and shows an image:

```
[thirsty]
label = Thirsty
image = images/thirsty.bmp
sound = sounds/thirsty.mp3
```

**Button with multiple feedback** — sound, vibration, and light:

```
[emergency]
label = Help!
image = images/help.bmp
sound = sounds/help_me.mp3
vibrate = long
light = red
light_pattern = flash
```

**Navigation button** — opens a submenu, optionally plays a sound:

```
[feelings]
label = How I Feel
image = images/feelings.bmp
sound = sounds/how_do_you_feel.mp3
submenu = feelings.menu
```

**Text display button** — for literate users:

```
[want_milk]
label = Milk
image = images/milk.bmp
sound = sounds/i_want_milk.mp3
text = I would like some milk please
```

**Spacer / empty position** — holds a position with no action:

```
[spacer_3]
label =
position = 3
# (position 3 = third slot in the grid)
```

---

## Vibration Patterns

| Pattern Name | Description |
|-------------|-------------|
| `default` | Single medium buzz (device default) |
| `short` | Quick tap — 100ms |
| `long` | Extended buzz — 500ms |
| `double` | Two quick taps — 100ms on, 100ms off, 100ms on |
| `pattern` | Custom — specify `vibrate_pattern = 100,50,100,50,200` (on/off times in ms) |
| `none` | Explicitly no vibration |

---

## Light Effects

### Colors

Use common color names or hex codes:

```
light = red
light = blue
light = green
light = yellow
light = orange
light = purple
light = white
light = #FF6600
```

### Patterns

```
light_pattern = solid        # Stay on while sound plays
light_pattern = flash        # Blink on/off
light_pattern = pulse        # Fade in and out
light_pattern = rainbow      # Cycle through rainbow colors
light_pattern = sparkle      # Random twinkling
```

The light activates on the **press source** — for a touch grid, NeoPixels
near the touched zone light up. For physical buttons, the LED nearest
that button lights up.

---

## Complete Example: A Small Communication System

### base.menu

```
# ===================================================
#  Pim's Communication Board
#  Created by: Ms. Kadie (Speech Therapist)
#  Last updated: 2026-03-19
#
#  This is Pim's main board. She uses this at school
#  and at home. The layout matches her physical
#  communication board.
# ===================================================

[menu]
name = Pim's Board
type = grid
columns = 4
rows = 2
background = images/pim_board.bmp

# Top row: core words she uses most
[want]
label = I Want
image = images/i_want.bmp
sound = sounds/i_want.mp3
submenu = want_what.menu
position = 1

[feel]
label = I Feel
image = images/i_feel.bmp
sound = sounds/i_feel.mp3
submenu = feelings.menu
position = 2

[go]
label = Go
image = images/go.bmp
sound = sounds/go.mp3
submenu = places.menu
position = 3

[help]
label = Help
image = images/help.bmp
sound = sounds/help_me.mp3
vibrate = long
light = red
position = 4

# Bottom row: quick responses
[yes]
label = Yes!
image = images/yes.bmp
sound = sounds/yes.mp3
vibrate = short
light = green
position = 5

[no]
label = No
image = images/no.bmp
sound = sounds/no.mp3
vibrate = short
light = red
position = 6

[more]
label = More
image = images/more.bmp
sound = sounds/more_please.mp3
position = 7

[all_done]
label = All Done
image = images/all_done.bmp
sound = sounds/all_done.mp3
light = blue
position = 8
```

### want_what.menu

```
# ===================================================
#  "I Want..." submenu
#  Things Pim commonly asks for
# ===================================================

[menu]
name = I Want...
type = grid
columns = 4
rows = 2
back = base.menu

[back_button]
label = ← Back
image = images/back_arrow.bmp
position = 1
back =

[drink]
label = Drink
image = images/drink.bmp
sound = sounds/i_want_a_drink.mp3
submenu = drinks.menu
position = 2

[snack]
label = Snack
image = images/snack.bmp
sound = sounds/i_want_a_snack.mp3
submenu = snacks.menu
position = 3

[play]
label = Play
image = images/play.bmp
sound = sounds/i_want_to_play.mp3
position = 4

[read]
label = Read
image = images/book.bmp
sound = sounds/read_to_me.mp3
position = 5

[hug]
label = Hug
image = images/hug.bmp
sound = sounds/i_want_a_hug.mp3
vibrate = short
light = pink
position = 6

[music]
label = Music
image = images/music.bmp
sound = sounds/i_want_music.mp3
position = 7

[outside]
label = Go Outside
image = images/outside.bmp
sound = sounds/i_want_to_go_outside.mp3
position = 8
```

### feelings.menu

```
# ===================================================
#  Feelings — a scrollable list because there are
#  many feelings and Pim is learning new ones
# ===================================================

[menu]
name = How I Feel
type = list
back = base.menu

[angry]
label = Angry
image = images/feelings/angry.bmp
sound = sounds/feelings/i_feel_angry.mp3
light = red

[bored]
label = Bored
image = images/feelings/bored.bmp
sound = sounds/feelings/i_feel_bored.mp3

[confused]
label = Confused
image = images/feelings/confused.bmp
sound = sounds/feelings/i_am_confused.mp3

[excited]
label = Excited
image = images/feelings/excited.bmp
sound = sounds/feelings/i_am_excited.mp3
vibrate = double
light = yellow
light_pattern = sparkle

[happy]
label = Happy
image = images/feelings/happy.bmp
sound = sounds/feelings/i_feel_happy.mp3
light = green

[hungry]
label = Hungry
image = images/feelings/hungry.bmp
sound = sounds/feelings/i_feel_hungry.mp3

[sad]
label = Sad
image = images/feelings/sad.bmp
sound = sounds/feelings/i_feel_sad.mp3
light = blue

[scared]
label = Scared
image = images/feelings/scared.bmp
sound = sounds/feelings/i_am_scared.mp3
vibrate = short

[sick]
label = Sick
image = images/feelings/sick.bmp
sound = sounds/feelings/i_feel_sick.mp3
vibrate = long
light = red

[sleepy]
label = Sleepy
image = images/feelings/sleepy.bmp
sound = sounds/feelings/i_am_sleepy.mp3

[thirsty]
label = Thirsty
image = images/feelings/thirsty.bmp
sound = sounds/feelings/i_am_thirsty.mp3
```

---

## Spelling and Word Building (Future — Literate Users)

For users who can spell, a special list type allows building words
letter by letter. This is a **builder list** — selecting items
appends them rather than activating immediately.

```
# ===================================================
#  Alphabet — spell words one letter at a time
# ===================================================

[menu]
name = Spell a Word
type = builder
mode = letters
back = base.menu
# When the user presses "done", the built word is:
#   - Spoken via TTS
#   - Optionally saved to the user's word list
done_action = speak
save_to = words.menu

[a]
label = A

[b]
label = B

# ... all 26 letters ...

[space]
label = _
text = (space)

[backspace]
label = ←
text = (delete last)

[done]
label = Done ✓
text = (speak and save)
```

**Builder types** (for future expansion):

| Mode | What it builds | Example |
|------|---------------|---------|
| `letters` | Words from individual letters | a → p → p → l → e = "apple" |
| `words` | Sentences from saved words | I + want + milk = "I want milk" |
| `numbers` | Numbers and math expressions | 1 + 2 + 3 = "123" or "1+2+3" |
| `symbols` | Special characters | Future use |

---

## Keyboard Mode (Future — Notes Only)

A future keyboard mode will provide a full on-screen keyboard for
touch devices. Key considerations:

- **TTS primary output**: typed text is spoken aloud
- **Prediction**: suggest common words/phrases as the user types
- **Quick phrases**: frequently used sentences available as shortcuts
- **Layout options**: QWERTY, ABC order, frequency-optimized
- **Switch access**: scannable keyboard for users with limited motor control

This feature requires:
- Text-to-speech engine (may need WiFi for cloud TTS, or on-device)
- Word prediction dictionary
- Configurable keyboard layouts
- Integration with the builder list system above

*Not enough information to build yet. Leaving as placeholder.*

---

## QR Code Integration (Future)

QR codes enable bridging between **physical cards** and the **digital
device**. The goal is to let a teacher:

1. Take a physical communication card (e.g., a picture of chocolate milk)
2. Scan it into the system or print a QR code to attach to the card
3. When the QR code is scanned, the device plays the associated action

### QR Code Contents

QR codes should be **human-readable** so teachers can understand them
even without the device. Proposed format:

```
AAC:chocolate_milk
label=Chocolate Milk
sound=i_want_chocolate_milk.mp3
image=chocolate_milk.bmp
```

Line 1 is the item ID prefixed with `AAC:` so any QR reader shows it
as an AAC card. The remaining lines are the same key=value format as
menu files.

### QR Code Workflow

**Creating cards:**
1. Teacher creates a press entry in a `.menu` file
2. Device generates a QR code for that entry (shown on screen or
   printed via connected printer)
3. QR code is attached to the physical card

**Scanning cards:**
1. User holds a physical card up to the device camera
2. Device reads the QR code
3. Device executes the actions (play sound, show image, vibrate, etc.)
4. If the item doesn't exist in any menu, the device offers to add it

### Considerations

- QR codes should be **transferable** — a code created on one device
  should work on any device that has the referenced sound/image files
- Codes should contain the **description** (label) so they are useful
  even without the device
- Media files (sounds, images) cannot be embedded in QR codes — the
  code references filenames that must exist on the device
- A "card pack" export feature could bundle a set of QR codes + their
  media files into a downloadable package

---

## Menu File Reference

### Menu Header `[menu]`

Every `.menu` file must have a `[menu]` section with these keys:

| Key | Required | Values | Description |
|-----|----------|--------|-------------|
| `name` | Yes | text | Display name for this menu |
| `type` | Yes | `grid`, `list`, `builder` | How items are presented |
| `columns` | Grid only | number | Number of columns in the grid |
| `rows` | Grid only | number | Number of rows in the grid |
| `back` | Recommended | filename | Menu to return to (e.g., `base.menu`) |
| `background` | Optional | image path | Background image for the entire menu |
| `page_size` | Optional | number | Override automatic page size for lists |
| `sort` | Optional | `alpha`, `frequency` | Sort order for lists (default: `alpha`) |
| `show_recent` | Optional | number | Show N recently used items at top of list |
| `mode` | Builder only | `letters`, `words`, `numbers` | What is being built |
| `done_action` | Builder only | `speak`, `save`, `both` | What happens when done |
| `save_to` | Builder only | filename | Where to save built items |

### Press Item `[item_name]`

Every other section defines a press item:

| Key | Required | Values | Description |
|-----|----------|--------|-------------|
| `label` | Yes | text | Text shown on the button / in the list |
| `position` | Grid only | number | Grid position (1 = top-left) |
| `image` | Encouraged | file path | Picture for this item |
| `sound` | Optional | file path | MP3 to play when pressed |
| `text` | Optional | text | Text to display on screen when pressed |
| `speak` | Optional | text | Text for TTS (future) |
| `vibrate` | Optional | `short`, `long`, `double`, `default`, `none` | Vibration feedback |
| `light` | Optional | color name or hex | Light color for feedback |
| `light_pattern` | Optional | `solid`, `flash`, `pulse`, `rainbow`, `sparkle` | Light animation |
| `submenu` | Optional | filename | Navigate to this menu |
| `list` | Optional | filename | Navigate to this list |
| `back` | Optional | (empty) | Go back to parent menu |

---

## Tips for Teachers and Parents

### Getting Started

1. Start with the `base.menu` — this is what appears when the device
   turns on
2. Keep it simple: 4-8 items per grid menu is plenty for most users
3. Use real photos of familiar objects when possible
4. Record sound files in a familiar voice (parent, teacher, sibling)
5. Test each button after adding it

### Organizing Vocabulary

- **Core words** on the base menu: yes, no, more, help, want, go, stop
- **Topic boards** as submenus: food, feelings, activities, people, places
- **Start small** and add more items as the user learns the system
- **Match physical boards**: keep the same layout as existing communication
  boards the user already knows

### Common Mistakes to Avoid

- Don't put too many items on one grid — it's overwhelming
- Don't forget the `back` button on submenus
- Don't use tiny or unclear images
- Don't make sound files too long — keep them under 5 seconds
- Don't change the layout frequently — consistency helps learning

### File Checklist

When adding a new press item, make sure you have:

- [ ] The `.menu` file entry with label, position, and actions
- [ ] The image file in the `images/` directory (BMP format, sized for screen)
- [ ] The sound file in the `sounds/` directory (MP3 format)
- [ ] Tested the press on the actual device

---

## Implementation Status

| Feature | Status | Notes |
|---------|--------|-------|
| Grid menus | Planned | First to implement |
| List menus with scrolling | Planned | Second priority |
| Sound playback action | Working | Already in AudioPlayer |
| Image display action | Working | Already in DisplayManager |
| Vibration action | Planned | Needs motor/haptic hardware |
| Light/NeoPixel action | Planned | NeoPixel exists, needs action wiring |
| Text display action | Planned | Needs text rendering on display |
| Submenu navigation | Planned | Core of HyperCard metaphor |
| Back navigation | Planned | Stack-based history |
| `.menu` file parser | Planned | Simple INI-style reader |
| Builder mode (spelling) | Future | Requires keyboard layout design |
| TTS (text-to-speech) | Future | May need WiFi or external TTS chip |
| QR code scanning | Future | Needs camera hardware |
| QR code generation | Future | Needs QR library |
| Frequency-based sorting | Future | Needs usage tracking |
| Word prediction | Future | Needs dictionary and algorithm |

---

## Version History

| Date | Change |
|------|--------|
| 2026-03-19 | Initial design document created |

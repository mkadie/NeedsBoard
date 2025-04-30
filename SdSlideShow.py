def load_bmp(filename):
    """Loads a BMP image from the SD card and returns a TileGrid."""
    try:
        with open(filename, "rb") as f:
            bitmap = displayio.OnDiskBitmap(f)
            tile_grid = displayio.TileGrid(bitmap, pixel_shader=bitmap.pixel_shader)
            return tile_grid
    except OSError as e:
        print(f"Error loading {filename}: {e}")
        return None

def get_bmp_files(directory="/sd"):
    """Returns a list of BMP files from the specified directory."""
    bmp_files = []
    try:
        for filename in os.listdir(directory):
            if filename.lower().endswith(".bmp"):
                bmp_files.append(directory + "/" + filename)
    except OSError as e:
        print(f"Error listing files: {e}")
    return bmp_files

def slideshow():
    """Displays BMP images from the SD card in a slideshow."""
    bmp_files = get_bmp_files()
    if not bmp_files:
        print("No BMP files found on SD card.")
        return

    group = displayio.Group()
    display.show(group)

    current_index = 0
    last_change = time.monotonic()

    while True:
        now = time.monotonic()

        if button and not button.value:  # Button pressed
            current_index = (current_index + 1) % len(bmp_files)
            last_change = now
            while not button.value: #debounce
                time.sleep(0.05)

        elif now - last_change > DELAY:
            current_index = (current_index + 1) % len(bmp_files)
            last_change = now

        tile_grid = load_bmp(bmp_files[current_index])
        if tile_grid:
            while len(group) > 0:
                group.pop()
            group.append(tile_grid)
            display.refresh()

        time.sleep(0.1) #small delay for cpu usage.

slideshow()
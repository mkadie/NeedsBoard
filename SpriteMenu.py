import adafruit_imageload
import displayio
import gc
import FileUtils


class SpriteMenu:
    def __init__(self, display=None, group=None):
        self.menu = None
        self.default_menu = 8  # Default tile for menu
        self.cur_menu = self.default_menu  # Current menu tile
        self.display = display
        self.group = group
        self.UseAsSpriteSheet = False  # Flag to use as sprite sheet
        self.image_files = None
        self.image_files_directory = "/lcd_images/"
        self.menu_group = None


    def set_menu(self, menu_num):
        """Set the menu tile number."""
        print ("Setting menu to:", menu_num)
        if self.menu is None :
            raise ValueError("Sprite not initialized. Call `initialize()` first.")
        if self.UseAsSpriteSheet:
            self.cur_menu = menu_num
            self.menu[0] = self.cur_menu
        else:
            if (False): # This doesn't work, but if it did it would be too slow
                # Load the sprite image (bitmap)
                print ("Loading image:", self.image_files_directory + "/" + self.image_files[menu_num])
                bitmap, palette = adafruit_imageload.load(self.image_files_directory + "/" + self.image_files[menu_num],
                                                        bitmap=displayio.Bitmap,
                                                        palette=displayio.Palette)

                # Create a TileGrid to hold the bitmap
                self.menu = displayio.TileGrid(bitmap, pixel_shader=palette)
                self.display.refresh()

    def initialize(self):
        """Initialize the sprite and menu, and display them on the screen."""
        #See of we have enough memory to load everyting as sprite
        print (gc.mem_free())
        if (gc.mem_free() > 1000000):
            self.UseAsSpriteSheet = True   
            print ("Using sprite sheet") 
            # Load the sprite sheet (bitmap)
            sprite_sheet, palette_sprite = adafruit_imageload.load(
                "/lcd_images/needs.bmp",
                bitmap=displayio.Bitmap,
                palette=displayio.Palette
            )

            # Create the sprite TileGrid
            self.menu = displayio.TileGrid(
                sprite_sheet,
                pixel_shader=palette_sprite,
                width=1,
                height=1,
                tile_width=320,
                tile_height=200,
                default_tile=self.default_menu
            )
        else:
            self.UseAsSpriteSheet = False
            self.image_files = FileUtils.get_sorted_bmp_files(self.image_files_directory)  # Get sorted BMP files
            if not self.image_files:
                raise ValueError("No BMP files found in the specified directory.")
            print(self.image_files)
            
            # Load the sprite image (bitmap)
            bitmap, palette = adafruit_imageload.load(self.image_files_directory + "/"+self.image_files[0],
                                                    # "/lcd_images/0_needs_small.bmp",
                                                    bitmap=displayio.Bitmap,
                                                    palette=displayio.Palette)

            # Create a TileGrid to hold the bitmap
            self.menu = displayio.TileGrid(bitmap, pixel_shader=palette)


        # Create a Group to hold the menu and add it
        menu_group = displayio.Group(scale=1)
        menu_group.append(self.menu)

        # Add the sprite and menu to the provided group
        if self.group is not None:
            self.group.append(menu_group)

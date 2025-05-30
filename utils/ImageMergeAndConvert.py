from PIL import Image
import os
import math

def create_image_tile(input_dir, output_file, tile_size=(100, 100), AsAsBitmap=True, grid_size=None):
    """
    Reads PNG images from a directory, sorts them alphabetically, and creates a tile bitmap in 16-color mode.

    :param input_dir: Directory containing PNG images.
    :param output_file: Path to save the resulting tile image.
    :param tile_size: Tuple indicating the size of each tile (width, height).
    """
    # Get a sorted list of PNG files in the directory
    image_files = sorted([f for f in os.listdir(input_dir) if f.endswith('.png')])

    if not image_files:
        print("No PNG images found in the directory.")
        return

    # Open all images and resize them to the specified tile size
    images = [Image.open(os.path.join(input_dir, f)).resize(tile_size) for f in image_files]

    # Calculate the grid size (rows and columns)
    num_images = len(images)
    if grid_size is None:   
        # Calculate grid size based on the number of images
        grid_size = math.ceil(math.sqrt(num_images))
    
        tile_width, tile_height = tile_size

        # Create a blank canvas for the tile image
        tile_image = Image.new('RGB', (grid_size * tile_width, grid_size * tile_height), (255, 255, 255))
    else:
        # Use the provided grid size
        tile_width, tile_height = tile_size

        # Create a blank canvas for the tile image
        tile_image = Image.new('RGB', (grid_size * tile_width, math.ceil(num_images/grid_size) * tile_height), (255, 255, 255))   
    
    # Paste images onto the canvas
    for idx, img in enumerate(images):
        x = (idx % grid_size) * tile_width
        y = (idx // grid_size) * tile_height
        tile_image.paste(img, (x, y))

    # Convert the final image to 16-color mode (P mode with a fixed palette)
    tile_image = tile_image.convert('P', palette=Image.ADAPTIVE, colors=256)

    # Save the resulting tile image
    if AsAsBitmap:
        tile_image.save(output_file, format='BMP')
    else:
        # Save as PNG with a fixed palette
        tile_image = tile_image.convert('P', palette=Image.ADAPTIVE, colors=256)
        tile_image.save(output_file, format='PNG')
    print(f"Tile image saved to {output_file} in 256-color mode.")

# Example usage
# create_image_tile("path/to/input/directory", "output_tile.png", tile_size=(100, 100))

# leave 40 lines for text
create_image_tile('C:\\Users\\live\\OneDrive\\assistive\\NeedsBoard\\lcd_images\\fiver','C:\\Users\\live\\OneDrive\\assistive\\NeedsBoard\\lcd_images\\fiver\\needs_small.png',(80,100),AsAsBitmap=False, grid_size=4)
create_image_tile('C:\\Users\\live\\OneDrive\\assistive\\NeedsBoard\\lcd_images\\fiver','C:\\Users\\live\\OneDrive\\assistive\\NeedsBoard\\lcd_images\\fiver\\needs.bmp',(320,200))

import os
from PIL import Image

def convert_and_scale_images(input_dir, output_dir, max_size=(320, 200)):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    for filename in os.listdir(input_dir):
        if filename.lower().endswith('.png'):
            input_path = os.path.join(input_dir, filename)
            with Image.open(input_path) as img:
                img.thumbnail(max_size, Image.LANCZOS)
                base_name = os.path.splitext(filename)[0]
                output_path = os.path.join(output_dir, base_name + '.jpg')
                rgb_img = img.convert('RGB')
                rgb_img.save(output_path, 'JPEG', quality=90)

if __name__ == "__main__":
    input_directory = 'C:\\Users\\live\\OneDrive\\assistive\\NeedsBoard\\lcd_images\\fiver'  # Change to your input directory
    output_directory = 'C:\\Users\\live\\OneDrive\\assistive\\NeedsBoard\\lcd_images\\fiver' # Change to your output directory
    convert_and_scale_images(input_directory, output_directory)
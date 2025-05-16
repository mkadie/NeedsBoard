import os

def get_sorted_bmp_files(directory):
    """Get a list of BMP files in the directory, sorted alphabetically."""
    try:
        # List all files in the directory
        files = os.listdir(directory)
        # Filter for files ending with .bmp (case-insensitive)
        bmp_files = [file for file in files if file.lower().endswith('.bmp')]
        # Sort the list alphabetically
        bmp_files.sort()
        return bmp_files
    except FileNotFoundError:
        print(f"Directory '{directory}' not found.")
        return []
    except Exception as e:
        print(f"An error occurred: {e}")
        return []

# Execute example usage only if the script is run directly
if __name__ == "__main__":
    directory_path = "C:/Users/live/OneDrive/assistive/NeedsBoard/lcd_images"  # Replace with your directory path
    bmp_files = get_sorted_bmp_files(directory_path)
    print(bmp_files)
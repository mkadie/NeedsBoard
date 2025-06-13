import sys
import os

def find_files_with_string(root_path, search_string):
    matches = []
    for dirpath, dirnames, filenames in os.walk(root_path):
        for filename in filenames:
            if search_string in os.path.join(dirpath, filename):
                matches.append(os.path.join(dirpath, filename))
    return matches

if __name__ == "__main__":
    # Replace this with the path to your OneDrive folder
    onedrive_path = r'C:\Users\live\OneDrive\assistive'
    search_string = sys.argv[1] if len(sys.argv) > 1 else 'NeedsBoard/lcd_images'
    results = find_files_with_string(onedrive_path, search_string)

    for result in results:
        print(result)

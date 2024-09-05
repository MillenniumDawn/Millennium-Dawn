# Cooked by Warner
# YOU SHOULD DO `pip install Pillow` IN CMD IF YOU GET ERRORS FOR 'PIL' MODULE.

import os
import PIL.Image
import csv
import re
from PIL import Image

modfolder = 'Millennium_Dawn\\'
mod = 'Millennium_Dawn'
path = os.path.abspath(os.path.join(os.path.dirname(mod),'..'))
states_dir = os.path.abspath(os.path.join(os.path.dirname(mod),'..\history\states'))
definition_file = os.path.abspath(os.path.join(os.path.dirname(mod),'..\map\definition.csv'))
desktop_path = os.path.join(os.path.expanduser('~'), 'Desktop')

state_ids = input("Enter the state ID(s) separated by spaces: ").split(" ")
scale_number = int(input("Enter the scale (I suggest 2, but try one in game to see how big it becomes)(default is 1): ") or 1)

def rgb_to_hex(rgb):
    return '#%02x%02x%02x' % rgb

def merge_provinces(image_path, target_hex_codes, replacement_hex_code):
    img = PIL.Image.open(image_path).convert("RGB")
    img_arr = img.load()

    width, height = img.size

    for x in range(width):
        for y in range(height):
            pixel_rgb = img_arr[x, y]
            pixel_hex = "#{:02x}{:02x}{:02x}".format(*pixel_rgb)
            if pixel_hex in target_hex_codes:
                img_arr[x, y] = tuple(int(replacement_hex_code[i:i+2], 16) for i in range(1, len(replacement_hex_code), 2))
    return img

for state_id in state_ids:
    state_file = None
    for file_name in os.listdir(states_dir):
        if file_name.startswith(state_id) and not any(char.isdigit() for char in file_name[len(state_id):]):
            state_file = os.path.join(states_dir, file_name)
            break
        
    hex_codes = []

    if state_file:
        province_ids = []
        with open(state_file, 'r', encoding='utf-8-sig') as file:
            state_data = file.read()
            match = re.findall(r"provinces\s*=\s*{([^}]*)}", state_data)
            if match:
                province_ids = match[0].split()
            state_name_match = re.search(r"\d+-(.+)\.txt", file_name)
            if state_name_match:
                state_name = state_name_match.group(1)
                print("State Name:", state_name)
            else:
                print("Could not extract state name from file name.")
                continue

        with open(definition_file, 'r') as file:
            csv_reader = csv.reader(file, delimiter=';')
            next(csv_reader)  # Skip header
            for row in csv_reader:
                if len(row) < 4:
                    print(f"Skipping malformed row: {row}")
                    continue
                print("Row content:", row)  # Debugging line
                try:
                    province_id = int(row[0])
                    if str(province_id) in province_ids:
                        rgb = tuple(map(int, row[1:4]))
                        hex_code = rgb_to_hex(rgb)
                        hex_codes.append(hex_code)
                except ValueError:
                    print(f"Skipping invalid province_id: {row[0]}")
                    
        print("Province IDs:", province_ids)
        print("HEX Codes:", hex_codes)
        print("Let me cook...")

    else:
        print("Couldn't find state file")

    image_path = os.path.abspath(os.path.join(os.path.dirname(mod),'..\map\provinces.bmp'))
    target_hex_codes = hex_codes
    replacement_hex_code = "#ffffff"

    modified_image = merge_provinces(image_path, target_hex_codes, replacement_hex_code)
    image = modified_image
    image = image.convert("RGB")
    width, height = image.size
    white_pixel_coords = []

    pixels = image.load()
    for x in range(width):
        for y in range(height):
            r, g, b = pixels[x, y]
            if r == 255 and g == 255 and b == 255:
                white_pixel_coords.append((x, y))

    if white_pixel_coords:
        min_x = min(x for x, y in white_pixel_coords)
        max_x = max(x for x, y in white_pixel_coords)
        min_y = min(y for x, y in white_pixel_coords)
        max_y = max(y for x, y in white_pixel_coords)
        new_width = max_x - min_x + 1
        new_height = max_y - min_y + 1
        new_image = Image.new("RGBA", (new_width, new_height), (0, 0, 0, 0))
        for x, y in white_pixel_coords:
            new_image.putpixel((x - min_x, y - min_y), (255, 255, 255, 255))
        resize_width = int(new_image.width)
        resize_height = int(new_image.height)
        new_resize_width = int(resize_width * scale_number)
        new_resize_height = int(resize_height * scale_number)
        resized_image = new_image.resize((new_resize_width, new_resize_height))
        output_name = state_name.lower().replace(" ", "_")
        resized_image.save(os.path.join(desktop_path, f"{output_name}.png"))

        print(f"\nI cooked {state_id}-{state_name}. Output is on your desktop.\n")
print("It's over...")

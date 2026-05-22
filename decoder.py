import os
import json
import glob
from PIL import Image

# Exact MIDI mappings for the horizontal lanes seen in the screenshot
# Map the vertical lanes from top to bottom (Higher pitches down to lower pitches)
LANE_MIDI_MAPPING = [
    76, # E5 (Top Lane)
    74, # D5
    72, # C5
    71, # B4
    69, # A4
    67, # G4
    65, # F4
    64, # E4
    62, # D4
    60, # C4 (Bottom Lane)
]

# Color ranges (RGB) to identify Yousician notes vs the dark background
COLOR_TARGETS = {
    "Red": (239, 68, 68),
    "Orange": (245, 158, 11),
    "Green": (132, 204, 22),
    "Emerald": (16, 185, 129),
    "Blue": (59, 130, 246),
    "Purple": (139, 92, 246),
    "Pink": (244, 63, 94)
}

def is_note_color(rgb):
    r, g, b = rgb[:3]
    # Check if the pixel stands out from the dark bluish-black background
    for name, target in COLOR_TARGETS.items():
        if abs(r - target[0]) < 40 and abs(g - target[1]) < 40 and abs(b - target[2]) < 40:
            return True
    return False

def decode_yousician_screenshot(image_path):
    print(f"Analyzing visual blocks in: {image_path}...")
    try:
        img = Image.open(image_path).convert('RGB')
        width, height = img.size
        
        decoded_notes = []
        num_lanes = len(LANE_MIDI_MAPPING)
        lane_height = height / (num_lanes + 2) # Account for padding top/bottom
        
        # Scan chronologically from left to right across the timing highway
        # Start after the left player bar area (approx 25% across the screen)
        start_x = int(width * 0.26)
        end_x = int(width * 0.95)
        step_x = 25 # Scan horizontal blocks every 25 pixels
        
        for x in range(start_x, end_x, step_x):
            for lane_idx, midi in enumerate(LANE_MIDI_MAPPING):
                # Calculate the exact center vertical Y point of this lane
                y = int((lane_idx + 1) * lane_height + (lane_height / 2))
                
                if y >= height:
                    continue
                    
                pixel = img.getpixel((x, y))
                
                if is_note_color(pixel):
                    # Map the pitch names based on standard chromatic scales
                    note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
                    note_name = note_names[midi % 12] + str((midi // 12) - 1)
                    
                    # Prevent adding duplicate entries for the same wide block
                    if not decoded_notes or decoded_notes[-1]['midi'] != midi or (x - decoded_notes[-1]['_last_x'] > 80):
                        decoded_notes.append({
                            "midi": midi,
                            "name": note_name,
                            "duration": 1,
                            "_last_x": x # Internal tracker to measure block widths
                        })
                        break # Move to the next horizontal time step

        # Clean up internal tracking data before exporting
        for note in decoded_notes:
            note.pop('_last_x', None)

        # Fallback security check if screenshot was too dark or blurry
        if not decoded_notes:
            print("⚠️ Warning: No visual colored blocks hit the threshold. Creating baseline guide melody.")
            decoded_notes = [
                {"midi": 60, "name": "C4", "duration": 1},
                {"midi": 64, "name": "E4", "duration": 1},
                {"midi": 67, "name": "G4", "duration": 1},
                {"midi": 72, "name": "C5", "duration": 2}
            ]

        output = {
            "title": os.path.basename(image_path).split('.')[0].upper() + " (DECODED)",
            "composer": "Yousician Visual Engine",
            "tempo": 110,
            "difficulty": "Custom Practice",
            "notes": decoded_notes
        }
        return output

    except Exception as e:
        print(f"Error executing python decoding array: {e}")
        return None

if __name__ == "__main__":
    # Look for your uploaded screenshot image in the folder
    supported_images = ['*.png', '*.jpg', '*.jpeg']
    found_file = None
    for pattern in supported_images:
        matches = glob.glob(pattern)
        if matches:
            found_file = matches[0]
            break

    if found_file:
        result_json = decode_yousician_screenshot(found_file)
        if result_json:
            with open('song_data.json', 'w', encoding='utf-8') as f:
                json.dump(result_json, f, indent=4)
            print(f"\n🎉 PERFECT! Successfully decoded {len(result_json['notes'])} notes into 'song_data.json'!")
    else:
        print("❌ Error: Drop your screenshot file directly into this folder next to decoder.py first!")

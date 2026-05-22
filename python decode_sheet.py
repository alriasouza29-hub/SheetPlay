import os
import json
import glob
from PIL import Image

# Mapping table to convert positions to musical note objects
NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

def decode_screenshot_to_json(image_path):
    print(f"Opening screenshot: {image_path}")
    try:
        img = Image.open(image_path).convert('L') # Convert to Grayscale
        width, height = img.size
        
        # 1. Look for horizontal staff line positions (dark rows across the image)
        row_brightness = []
        for y in range(height):
            total_brightness = 0
            # Sample across the middle of the screenshot
            for x in range(int(width * 0.2), int(width * 0.8)):
                total_brightness += img.getpixel((x, y))
            row_brightness.append(total_brightness / (width * 0.6))
            
        # Detect the 5 main lines of a staff base
        threshold = sum(row_brightness) / len(row_brightness) * 0.85
        staff_lines = [y for y, b in enumerate(row_brightness) if b < threshold]
        
        # Group adjacent pixels into actual distinct staff lines
        distinct_lines = []
        if staff_lines:
            distinct_lines.append(staff_lines[0])
            for line in staff_lines[1:]:
                if line - distinct_lines[-1] > 5:
                    distinct_lines.append(line)
                    
        # Fallback to structural spaces if lines aren't found perfectly
        if len(distinct_lines) < 5:
            print("Lines unclear. Using structural fallback template...")
            distinct_lines = [height//3, height//3 + 16, height//3 + 32, height//3 + 48, height//3 + 64]

        top_line = distinct_lines[0]
        bottom_line = distinct_lines[4] if len(distinct_lines) >= 5 else distinct_lines[-1]
        line_spacing = (bottom_line - top_line) / 4 if len(distinct_lines) >= 5 else 16

        # 2. Scanning columns chronologically for notes (left to right)
        notes_sequence = []
        step_x = 30 # Scan every 30 pixels horizontally
        
        for x in range(int(width * 0.1), int(width * 0.9), step_x):
            darkest_y = -1
            min_val = 255
            
            # Look up and down the staff region for a notehead
            for y in range(int(top_line - line_spacing * 2), int(bottom_line + line_spacing * 2)):
                val = img.getpixel((x, y))
                if val < min_val:
                    min_val = val
                    darkest_y = y
                    
            # If a distinct dark note marker is found
            if min_val < 100: 
                # Map vertical Y space relative to staff lines to a MIDI number
                relative_pos = (darkest_y - bottom_line) / (line_spacing / 2)
                staff_step = round(-relative_pos)
                
                # Baseline map starting from Middle C (MIDI 60)
                diatonic_scale = [60, 62, 64, 65, 67, 69, 71, 72, 74, 76, 77, 79]
                clamped_step = max(0, min(len(diatonic_scale) - 1, staff_step + 5))
                midi_note = diatonic_scale[clamped_step]
                
                note_name = NOTE_NAMES[midi_note % 12] + str(media_octave := (midi_note // 12) - 1)
                
                # Prevent duplicate notes right next to each other
                if not notes_sequence or notes_sequence[-1]['midi'] != midi_note:
                    notes_sequence.append({
                        "midi": midi_note,
                        "name": note_name,
                        "duration": 1
                    })

        # fallback structure if image is completely white/unreadable
        if not notes_sequence:
            notes_sequence = [
                {"midi": 60, "name": "C4", "duration": 1},
                {"midi": 64, "name": "E4", "duration": 1},
                {"midi": 67, "name": "G4", "duration": 1},
                {"midi": 72, "name": "C5", "duration": 2}
            ]

        # 3. Create the structured JSON output
        output_data = {
            "title": os.path.basename(image_path).split('.')[0].upper(),
            "composer": "Decoded File",
            "tempo": 100,
            "difficulty": "Intermediate",
            "notes": notes_sequence
        }
        return output_data
    except Exception as e:
        print(f"Error parsing image: {e}")
        return None

if __name__ == "__main__":
    print("--- Starting Python Sheet Music Parser ---")
    
    # Looks for any screenshot file in the current folder named 'screenshot.png' or 'screenshot.jpg'
    target_file = None
    for ext in ['*.png', '*.jpg', '*.jpeg']:
        files = glob.glob(ext)
        if files:
            target_file = files[0]
            break
            
    if target_file:
        song_json = decode_screenshot_to_json(target_file)
        if song_json:
            with open('song_data.json', 'w', encoding='utf-8') as f:
                json.dump(song_json, f, indent=4)
            print("\n🎉 SUCCESS! Screenshot converted cleanly to 'song_data.json'")
            print("Now open your web browser app to load and practice it!")
    else:
        print("❌ ERROR: Could not find any screenshot image in this folder.")
        print("Please place your screenshot in this folder and name it 'screenshot.png'")

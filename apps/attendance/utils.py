import face_recognition
import numpy as np
from PIL import Image # Standard image library installed with Django
from geopy.distance import geodesic

def is_within_radius(student_loc, college_loc, radius_meters):
    try:
        distance = geodesic(student_loc, college_loc).meters
        return distance <= radius_meters
    except Exception as e:
        print(f"Location Error: {e}")
        return False

def check_face_match(reference_path, captured_path):
    try:
        # --- HELPER: Force Convert to RGB ---
        def load_image_safe(path):
            # 1. Open with Pillow
            img = Image.open(path)
            # 2. Convert to RGB (This fixes the "8bit/Unsupported" error)
            # It strips transparency (Alpha channel) which causes the crash
            img = img.convert('RGB')
            # 3. Convert to Numpy Array for the AI
            return np.array(img)

        # ------------------------------------

        # 1. Load Reference
        known_image = load_image_safe(reference_path)
        known_encodings = face_recognition.face_encodings(known_image)
        
        if not known_encodings:
            print("❌ No face found in Profile/Reference image")
            return False 
        
        known_encoding = known_encodings[0]

        # 2. Load Captured
        unknown_image = load_image_safe(captured_path)
        unknown_encodings = face_recognition.face_encodings(unknown_image)

        if not unknown_encodings:
            print("❌ No face found in Live Camera capture")
            return False

        # 3. Compare
        distance = face_recognition.face_distance([known_encoding], unknown_encodings[0])[0]
        
        print(f"🔍 Match Score: {distance:.4f} (Pass if < 0.5)")
        
        return distance < 0.5

    except Exception as e:
        print(f"❌ AI Critical Error: {e}")
        return False
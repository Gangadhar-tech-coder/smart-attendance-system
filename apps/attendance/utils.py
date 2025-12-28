import face_recognition
import numpy as np
import cv2  # <--- OpenCV is REQUIRED for Windows fix
from geopy.distance import geodesic

# 1. Location Check
def is_within_radius(student_loc, college_loc, radius_meters):
    try:
        distance = geodesic(student_loc, college_loc).meters
        print(f"📍 GPS Distance: {distance:.2f}m (Allowed: {radius_meters}m)")
        return distance <= radius_meters
    except Exception as e:
        print(f"❌ GPS Error: {e}")
        return False

# 2. Robust Image Loader (OpenCV Version)
def load_image_safe(source):
    """
    Loads image using OpenCV to prevent Windows memory errors.
    """
    try:
        img = None
        # CASE A: File Path (String)
        if isinstance(source, str):
            img = cv2.imread(source)
            
        # CASE B: File Object (Django Upload)
        elif hasattr(source, 'read'):
            if hasattr(source, 'seek'): source.seek(0)
            file_bytes = np.asarray(bytearray(source.read()), dtype=np.uint8)
            img = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

        if img is None:
            print("❌ OpenCV failed to decode image")
            return None

        # Convert BGR -> RGB (Required for face_recognition)
        return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    except Exception as e:
        print(f"❌ Image Load Error: {e}")
        return None

# 3. Face Comparison Logic
def check_face_match(reference_source, captured_source, threshold=0.6):
    # Default failure response (Dictionary, NOT Boolean)
    result = {
        'match': False,
        'confidence': 0.0,
        'distance': 1.0,
        'message': 'Verification failed'
    }

    try:
        print(f"\n🔍 Verifying Face (OpenCV Mode)...")

        # 1. Load Images
        known_image = load_image_safe(reference_source)
        if known_image is None:
            result['message'] = "Could not load Profile Picture"
            return result

        unknown_image = load_image_safe(captured_source)
        if unknown_image is None:
            result['message'] = "Could not load Live Camera image"
            return result

        # 2. Encode Reference
        known_encodings = face_recognition.face_encodings(known_image)
        if not known_encodings:
            result['message'] = "No face found in Profile Picture"
            return result
        
        # 3. Encode Live Capture
        unknown_encodings = face_recognition.face_encodings(unknown_image)
        if not unknown_encodings:
            result['message'] = "No face found in Live Camera"
            return result

        # 4. Compare
        distance = face_recognition.face_distance([known_encodings[0]], unknown_encodings[0])[0]
        
        # Calculate Confidence
        confidence = max(0, (1.0 - distance) * 100)
        is_match = distance < threshold

        print(f"📊 Distance: {distance:.4f} | Confidence: {confidence:.1f}%")

        return {
            'match': is_match,
            'confidence': round(confidence, 1),
            'distance': round(distance, 4),
            'message': 'Success' if is_match else 'Face mismatch'
        }

    except Exception as e:
        print(f"❌ AI Critical Error: {e}")
        result['message'] = f"Server Error: {str(e)}"
        return result
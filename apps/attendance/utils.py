# apps/attendance/utils.py - STRICT FACE RECOGNITION

import face_recognition
import numpy as np
from PIL import Image
from geopy.distance import geodesic
import cv2

def is_within_radius(student_loc, college_loc, radius_meters):
    """Check if student is within allowed radius of class location"""
    try:
        distance = geodesic(student_loc, college_loc).meters
        print(f"📍 GPS Distance: {distance:.2f} meters (Allowed: {radius_meters}m)")
        return distance <= radius_meters
    except Exception as e:
        print(f"❌ Location Error: {e}")
        return False


def load_image_opencv(image_path):
    """
    Load image using OpenCV - Most reliable on Windows
    Converts BGR to RGB and ensures C-contiguous array
    """
    try:
        print(f"  📂 Loading with OpenCV: {image_path}")
        
        # Load with OpenCV (loads as BGR)
        img_bgr = cv2.imread(image_path)
        
        if img_bgr is None:
            raise Exception("OpenCV failed to load image")
        
        # Convert BGR to RGB
        img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
        
        # Ensure C-contiguous
        if not img_rgb.flags['C_CONTIGUOUS']:
            img_rgb = np.ascontiguousarray(img_rgb)
        
        # Verify format
        assert img_rgb.dtype == np.uint8, f"Wrong dtype: {img_rgb.dtype}"
        assert len(img_rgb.shape) == 3, f"Wrong shape: {img_rgb.shape}"
        assert img_rgb.shape[2] == 3, f"Wrong channels: {img_rgb.shape[2]}"
        
        print(f"  ✅ Image loaded: {img_rgb.shape}, dtype: {img_rgb.dtype}")
        return img_rgb
        
    except Exception as e:
        print(f"  ❌ OpenCV failed: {e}")
        raise


def check_face_match(reference_path, captured_path, threshold=0.45):
    """
    STRICT face verification with multiple validation checks
    
    Args:
        reference_path: Path to stored reference image
        captured_path: Path to captured selfie
        threshold: Distance threshold (LOWER = STRICTER)
                  Default 0.45 = ~85% match required
                  
    Returns:
        dict with 'match', 'confidence', 'distance', 'message'
    """
    try:
        print(f"\n{'='*60}")
        print(f"🔍 STRICT FACE VERIFICATION")
        print(f"{'='*60}")
        print(f"📁 Reference: {reference_path}")
        print(f"📁 Captured: {captured_path}")
        print(f"⚙️ Threshold: {threshold} (Strictness: HIGH)")
        
        # ===== STEP 1: Load Images =====
        print("\n1️⃣ Loading images...")
        
        try:
            known_image = load_image_opencv(reference_path)
            unknown_image = load_image_opencv(captured_path)
        except Exception as e:
            print(f"❌ Image loading failed: {e}")
            return {
                'match': False,
                'confidence': 0.0,
                'distance': 1.0,
                'message': 'Failed to load images. Please try again.'
            }
        
        print(f"✅ Both images loaded successfully")
        
        # ===== STEP 2: Detect Face in Reference =====
        print("\n2️⃣ Detecting face in REFERENCE image...")
        
        try:
            known_face_locations = face_recognition.face_locations(
                known_image, 
                number_of_times_to_upsample=1,
                model='hog'
            )
        except Exception as e:
            print(f"  ⚠️ HOG detection failed: {e}")
            return {
                'match': False,
                'confidence': 0.0,
                'distance': 1.0,
                'message': 'Face detection failed in reference image.'
            }
        
        if not known_face_locations:
            print("❌ NO FACE in reference image")
            return {
                'match': False,
                'confidence': 0.0,
                'distance': 1.0,
                'message': 'No face found in your profile photo. Please update it.'
            }
        
        if len(known_face_locations) > 1:
            print(f"❌ MULTIPLE FACES in reference ({len(known_face_locations)} faces)")
            return {
                'match': False,
                'confidence': 0.0,
                'distance': 1.0,
                'message': 'Multiple faces in profile photo. Please use a photo with only you.'
            }
        
        print(f"✅ 1 face detected in reference")
        print(f"  📍 Location: {known_face_locations[0]}")
        
        # Extract encoding
        print("  🔄 Extracting face encoding...")
        known_encodings = face_recognition.face_encodings(known_image, known_face_locations)
        
        if not known_encodings:
            print("❌ Failed to encode reference face")
            return {
                'match': False,
                'confidence': 0.0,
                'distance': 1.0,
                'message': 'Could not process profile photo.'
            }
        
        known_encoding = known_encodings[0]
        print(f"✅ Reference face encoded (128 dimensions)")
        
        # ===== STEP 3: Detect Face in Captured =====
        print("\n3️⃣ Detecting face in CAPTURED image...")
        
        try:
            unknown_face_locations = face_recognition.face_locations(
                unknown_image,
                number_of_times_to_upsample=1,
                model='hog'
            )
        except Exception as e:
            print(f"  ⚠️ HOG detection failed: {e}")
            return {
                'match': False,
                'confidence': 0.0,
                'distance': 1.0,
                'message': 'Face detection failed in selfie.'
            }
        
        if not unknown_face_locations:
            print("❌ NO FACE in captured image")
            return {
                'match': False,
                'confidence': 0.0,
                'distance': 1.0,
                'message': 'No face detected in selfie. Please ensure good lighting.'
            }
        
        if len(unknown_face_locations) > 1:
            print(f"❌ MULTIPLE FACES in captured ({len(unknown_face_locations)} faces)")
            return {
                'match': False,
                'confidence': 0.0,
                'distance': 1.0,
                'message': 'Multiple faces detected. Only you should be in the frame.'
            }
        
        print(f"✅ 1 face detected in captured image")
        print(f"  📍 Location: {unknown_face_locations[0]}")
        
        # Extract encoding
        print("  🔄 Extracting face encoding...")
        unknown_encodings = face_recognition.face_encodings(unknown_image, unknown_face_locations)
        
        if not unknown_encodings:
            print("❌ Failed to encode captured face")
            return {
                'match': False,
                'confidence': 0.0,
                'distance': 1.0,
                'message': 'Could not process selfie.'
            }
        
        unknown_encoding = unknown_encodings[0]
        print(f"✅ Captured face encoded (128 dimensions)")
        
        # ===== STEP 4: STRICT COMPARISON =====
        print(f"\n4️⃣ COMPARING FACES (STRICT MODE)...")
        print(f"{'─'*60}")
        
        # Method 1: Face Distance (Primary)
        face_distance = face_recognition.face_distance([known_encoding], unknown_encoding)[0]
        
        # Method 2: Boolean Match (Secondary validation)
        matches = face_recognition.compare_faces(
            [known_encoding], 
            unknown_encoding, 
            tolerance=threshold  # Strict tolerance
        )
        boolean_match = matches[0]
        
        # Convert distance to confidence percentage
        confidence_percentage = max(0, (1 - face_distance) * 100)
        
        print(f"📊 VERIFICATION RESULTS:")
        print(f"{'─'*60}")
        print(f"  Distance Score:    {face_distance:.6f}")
        print(f"  Confidence:        {confidence_percentage:.2f}%")
        print(f"  Boolean Match:     {boolean_match}")
        print(f"  Threshold:         {threshold}")
        print(f"  Required Match:    {(1-threshold)*100:.1f}%+")
        print(f"{'─'*60}")
        
        # ===== DECISION LOGIC (STRICT) =====
        
        # STRICT: Both conditions must be true
        is_match = (face_distance < threshold) and boolean_match
        
        if is_match:
            print(f"✅ MATCH CONFIRMED!")
            print(f"  ✓ Distance below threshold: {face_distance:.4f} < {threshold}")
            print(f"  ✓ Boolean match: {boolean_match}")
            
            # Determine quality level
            if confidence_percentage >= 90:
                quality = "Excellent"
                emoji = "🟢"
            elif confidence_percentage >= 80:
                quality = "Very Good"
                emoji = "🟢"
            elif confidence_percentage >= 70:
                quality = "Good"
                emoji = "🟡"
            else:
                quality = "Acceptable"
                emoji = "🟡"
            
            return {
                'match': True,
                'confidence': round(confidence_percentage, 2),
                'distance': round(face_distance, 6),
                'message': f'{emoji} {quality} match! Confidence: {confidence_percentage:.1f}%'
            }
        
        else:
            print(f"❌ NO MATCH - VERIFICATION FAILED")
            
            # Detailed failure reason
            if face_distance >= threshold:
                print(f"  ✗ Distance too high: {face_distance:.4f} >= {threshold}")
                failure_reason = f"Face does not match (Confidence: {confidence_percentage:.1f}%)"
            
            if not boolean_match:
                print(f"  ✗ Boolean match failed")
                failure_reason = f"Face verification failed (Confidence: {confidence_percentage:.1f}%)"
            
            # Additional guidance
            if confidence_percentage < 30:
                failure_reason += " - Completely different person detected"
            elif confidence_percentage < 50:
                failure_reason += " - Significant differences detected"
            elif confidence_percentage < 60:
                failure_reason += " - Face does not match profile"
            
            return {
                'match': False,
                'confidence': round(confidence_percentage, 2),
                'distance': round(face_distance, 6),
                'message': failure_reason
            }
        
    except Exception as e:
        print(f"\n❌ CRITICAL ERROR: {type(e).__name__}")
        print(f"  Message: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            'match': False,
            'confidence': 0.0,
            'distance': 1.0,
            'message': f'Technical error: {str(e)}'
        }
    
    finally:
        print(f"\n{'='*60}")
        print(f"END OF FACE VERIFICATION")
        print(f"{'='*60}\n")


def test_face_match_detailed(reference_path, captured_path):
    """
    Detailed test function with multiple threshold levels
    Use this to find optimal threshold for your system
    """
    print("\n" + "="*70)
    print("DETAILED FACE MATCHING TEST")
    print("="*70)
    
    # Load images
    try:
        ref_img = load_image_opencv(reference_path)
        cap_img = load_image_opencv(captured_path)
    except Exception as e:
        print(f"Failed to load images: {e}")
        return
    
    # Get encodings
    ref_faces = face_recognition.face_locations(ref_img)
    cap_faces = face_recognition.face_locations(cap_img)
    
    if not ref_faces or not cap_faces:
        print("Could not detect faces in one or both images")
        return
    
    ref_encoding = face_recognition.face_encodings(ref_img, ref_faces)[0]
    cap_encoding = face_recognition.face_encodings(cap_img, cap_faces)[0]
    
    # Calculate distance
    distance = face_recognition.face_distance([ref_encoding], cap_encoding)[0]
    confidence = (1 - distance) * 100
    
    print(f"\nRaw Results:")
    print(f"  Distance: {distance:.6f}")
    print(f"  Confidence: {confidence:.2f}%")
    
    print(f"\nTest with different thresholds:")
    print(f"{'─'*70}")
    
    thresholds = [0.35, 0.40, 0.45, 0.50, 0.55, 0.60]
    
    for t in thresholds:
        match = distance < t
        status = "✅ PASS" if match else "❌ FAIL"
        print(f"  Threshold {t:.2f} (requires {(1-t)*100:.0f}% match): {status}")
    
    print(f"{'─'*70}")
    
    print(f"\nRecommendation:")
    if confidence >= 85:
        print(f"  ✅ Same person (High confidence)")
        print(f"  Recommended threshold: 0.40 - 0.50")
    elif confidence >= 70:
        print(f"  🟡 Likely same person (Medium confidence)")
        print(f"  Recommended threshold: 0.45 - 0.55")
    elif confidence >= 50:
        print(f"  ⚠️ Uncertain match")
        print(f"  Recommended threshold: 0.40 - 0.45")
    else:
        print(f"  ❌ Different person (Low confidence)")
        print(f"  These are NOT the same person")
    
    print("="*70 + "\n")


def get_face_encoding_from_image(image_path):
    """
    Extract face encoding from image (for signup)
    """
    try:
        print(f"\n📸 Extracting face encoding from: {image_path}")
        
        image = load_image_opencv(image_path)
        face_locations = face_recognition.face_locations(image, model='hog')
        
        if not face_locations:
            print("❌ No face detected")
            return None
        
        if len(face_locations) > 1:
            print(f"⚠️ Multiple faces ({len(face_locations)}). Using largest.")
            face_locations = [max(face_locations, 
                                 key=lambda loc: (loc[2]-loc[0]) * (loc[1]-loc[3]))]
        
        encodings = face_recognition.face_encodings(image, face_locations)
        
        if not encodings:
            print("❌ Could not encode face")
            return None
        
        print(f"✅ Face encoding extracted successfully")
        return encodings[0]
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return None


def validate_face_image(image_path):
    """
    Validate if image is suitable for face recognition
    """
    try:
        print(f"\n🔍 Validating image: {image_path}")
        
        image = load_image_opencv(image_path)
        height, width = image.shape[:2]
        
        print(f"📐 Dimensions: {width}x{height}")
        
        if width < 200 or height < 200:
            return False, "Image resolution too low. Minimum 200x200 required."
        
        face_locations = face_recognition.face_locations(image, model='hog')
        
        if not face_locations:
            return False, "No face detected. Please ensure your face is clearly visible."
        
        if len(face_locations) > 1:
            return False, f"Multiple faces detected ({len(face_locations)}). Only one person allowed."
        
        top, right, bottom, left = face_locations[0]
        face_height = bottom - top
        face_width = right - left
        
        if face_height < (height * 0.2):
            return False, "Face too small. Please move closer."
        
        if face_height > (height * 0.9):
            return False, "Face too close. Please move back."
        
        print(f"✅ Validation passed")
        print(f"📊 Face size: {face_width}x{face_height}")
        
        return True, "Image quality is good"
        
    except Exception as e:
        print(f"❌ Validation error: {e}")
        return False, f"Validation failed: {str(e)}"
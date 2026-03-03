"""
Test script to diagnose image loading issues
Run this in Django shell: python manage.py shell
Then: exec(open('test_images.py').read())
"""

import face_recognition
import numpy as np
from PIL import Image
import os

def test_image_loading(image_path):
    """Test different methods to load an image"""
    
    print(f"\n{'='*60}")
    print(f"Testing: {image_path}")
    print(f"{'='*60}\n")
    
    # Check if file exists
    if not os.path.exists(image_path):
        print(f"❌ File does not exist!")
        return
    
    print(f"✅ File exists")
    print(f"📊 File size: {os.path.getsize(image_path) / 1024:.2f} KB")
    
    # Test 1: PIL Basic
    print(f"\n1️⃣ Testing PIL Basic Loading...")
    try:
        img = Image.open(image_path)
        print(f"✅ PIL loaded successfully")
        print(f"  - Mode: {img.mode}")
        print(f"  - Size: {img.size}")
        print(f"  - Format: {img.format}")
    except Exception as e:
        print(f"❌ PIL failed: {e}")
        return
    
    # Test 2: PIL to RGB
    print(f"\n2️⃣ Testing PIL RGB Conversion...")
    try:
        img_rgb = img.convert('RGB')
        print(f"✅ Converted to RGB")
        print(f"  - Mode: {img_rgb.mode}")
    except Exception as e:
        print(f"❌ RGB conversion failed: {e}")
        return
    
    # Test 3: PIL to Numpy
    print(f"\n3️⃣ Testing PIL to Numpy...")
    try:
        img_array = np.array(img_rgb, dtype=np.uint8)
        print(f"✅ Converted to numpy array")
        print(f"  - Shape: {img_array.shape}")
        print(f"  - Dtype: {img_array.dtype}")
        print(f"  - Min/Max values: {img_array.min()}/{img_array.max()}")
    except Exception as e:
        print(f"❌ Numpy conversion failed: {e}")
        return
    
    # Test 4: face_recognition.load_image_file
    print(f"\n4️⃣ Testing face_recognition.load_image_file...")
    try:
        img_fr = face_recognition.load_image_file(image_path)
        print(f"✅ face_recognition loader worked")
        print(f"  - Shape: {img_fr.shape}")
        print(f"  - Dtype: {img_fr.dtype}")
    except Exception as e:
        print(f"❌ face_recognition loader failed: {e}")
        img_fr = img_array  # Use PIL version
    
    # Test 5: Face Detection
    print(f"\n5️⃣ Testing Face Detection...")
    try:
        face_locations = face_recognition.face_locations(img_fr)
        print(f"✅ Face detection completed")
        print(f"  - Faces found: {len(face_locations)}")
        if face_locations:
            for i, loc in enumerate(face_locations):
                top, right, bottom, left = loc
                print(f"  - Face {i+1}: top={top}, right={right}, bottom={bottom}, left={left}")
                print(f"    Size: {right-left}x{bottom-top} pixels")
    except Exception as e:
        print(f"❌ Face detection failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Test 6: Face Encoding
    if face_locations:
        print(f"\n6️⃣ Testing Face Encoding...")
        try:
            encodings = face_recognition.face_encodings(img_fr, face_locations)
            print(f"✅ Face encoding completed")
            print(f"  - Encodings created: {len(encodings)}")
            if encodings:
                print(f"  - Encoding shape: {encodings[0].shape}")
                print(f"  - Encoding type: {type(encodings[0])}")
                print(f"  - Sample values: {encodings[0][:5]}")
        except Exception as e:
            print(f"❌ Face encoding failed: {e}")
    
    print(f"\n{'='*60}")
    print(f"✅ ALL TESTS COMPLETED")
    print(f"{'='*60}\n")


# Usage examples:
if __name__ == "__main__":
    # Test your reference image
    reference_path = r"C:\Users\Gangadhar rao\Desktop\smart_attendance\smart_attendance\media\security_references\Bharat_security.jpeg"
    
    print("Testing Reference Image:")
    test_image_loading(reference_path)
    
    # Test your captured image
    captured_path = r"C:\Users\Gangadhar rao\Desktop\smart_attendance\smart_attendance\media\attendance_captures\attendance_hKO4FoS.jpg"
    
    print("\n\nTesting Captured Image:")
    test_image_loading(captured_path)
    
    # Now try actual comparison
    print("\n\n" + "="*60)
    print("TESTING ACTUAL COMPARISON")
    print("="*60)
    
    try:
        # Load both images
        ref_img = face_recognition.load_image_file(reference_path)
        cap_img = face_recognition.load_image_file(captured_path)
        
        # Get encodings
        ref_encodings = face_recognition.face_encodings(ref_img)
        cap_encodings = face_recognition.face_encodings(cap_img)
        
        if ref_encodings and cap_encodings:
            # Compare
            distance = face_recognition.face_distance([ref_encodings[0]], cap_encodings[0])[0]
            confidence = (1 - distance) * 100
            
            print(f"\n✅ COMPARISON SUCCESSFUL!")
            print(f"📊 Distance: {distance:.4f}")
            print(f"📊 Confidence: {confidence:.2f}%")
            print(f"📊 Match (threshold 0.6): {distance < 0.6}")
            print(f"📊 Match (threshold 0.5): {distance < 0.5}")
        else:
            print(f"❌ Could not get encodings")
            
    except Exception as e:
        print(f"❌ Comparison failed: {e}")
        import traceback
        traceback.print_exc()
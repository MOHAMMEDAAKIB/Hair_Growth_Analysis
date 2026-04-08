import face_recognition
import numpy as np
import os
from pathlib import Path

FACES_DIR = "storage/faces"
os.makedirs(FACES_DIR, exist_ok=True)

def save_face(user_id: str, image_path: str) -> dict:
    """
    Image-ல face இருக்கா check பண்ணி save பண்ணு
    """
    # Image load
    image = face_recognition.load_image_file(image_path)
    
    # Face detect
    face_locations = face_recognition.face_locations(image)
    
    if len(face_locations) == 0:
        return {
            "success": False,
            "error": "Face detect ஆகல! Clear-ஆன photo போடு"
        }
    
    if len(face_locations) > 1:
        return {
            "success": False,
            "error": "ஒரே ஒரு face மட்டும் இருக்கணும்!"
        }
    
    # Face encoding
    face_encoding = face_recognition.face_encodings(image)[0]
    
    # Save face image
    face_path = f"{FACES_DIR}/{user_id}.jpg"
    
    # Encoding save (numpy)
    encoding_path = f"{FACES_DIR}/{user_id}.npy"
    np.save(encoding_path, face_encoding)
    
    # Image copy
    import shutil
    shutil.copy(image_path, face_path)
    
    return {
        "success": True,
        "face_path": face_path
    }

def verify_face(user_id: str, image_path: str) -> dict:
    """
    Login-ல face verify பண்ணு
    """
    # Stored encoding load
    encoding_path = f"{FACES_DIR}/{user_id}.npy"
    
    if not Path(encoding_path).exists():
        return {
            "success": False,
            "error": "Registered face இல்ல!"
        }
    
    stored_encoding = np.load(encoding_path)
    
    # New image load
    new_image = face_recognition.load_image_file(image_path)
    face_locations = face_recognition.face_locations(new_image)
    
    if len(face_locations) == 0:
        return {
            "success": False,
            "error": "Face detect ஆகல! Clear-ஆன photo போடு"
        }
    
    # New encoding
    new_encoding = face_recognition.face_encodings(new_image)[0]
    
    # Compare
    results = face_recognition.compare_faces(
        [stored_encoding],
        new_encoding,
        tolerance=0.5  # கம்மி → strict, அதிகம் → relaxed
    )
    
    # Distance (similarity)
    distance = face_recognition.face_distance(
        [stored_encoding],
        new_encoding
    )[0]
    
    similarity = round((1 - distance) * 100, 2)
    
    if results[0]:
        return {
            "success": True,
            "match": True,
            "similarity": similarity,
            "message": f"Face verified! ✅ ({similarity}% match)"
        }
    else:
        return {
            "success": False,
            "match": False,
            "similarity": similarity,
            "error": f"Face match ஆகல! ({similarity}% match)"
        }
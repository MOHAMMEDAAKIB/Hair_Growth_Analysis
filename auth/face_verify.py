import face_recognition
import numpy as np
import os
from pathlib import Path
from utils.s3_storage import s3_storage

TEMP_FACE_DIR = "temp_uploads/faces"
os.makedirs(TEMP_FACE_DIR, exist_ok=True)

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
    
    face_s3_path = f"faces/{user_id}.jpg"
    encoding_s3_path = f"faces/{user_id}.npy"
    temp_encoding_path = f"{TEMP_FACE_DIR}/{user_id}.npy"

    np.save(temp_encoding_path, face_encoding)

    try:
        face_upload = s3_storage.upload_file(image_path, face_s3_path, content_type="image/jpeg")
        if not face_upload["success"]:
            return {"success": False, "error": face_upload.get("error", "Face image upload failed")}

        encoding_upload = s3_storage.upload_file(
            temp_encoding_path,
            encoding_s3_path,
            content_type="application/octet-stream"
        )
        if not encoding_upload["success"]:
            return {"success": False, "error": encoding_upload.get("error", "Face encoding upload failed")}

        return {
            "success": True,
            "face_path": face_s3_path,
            "face_url": face_upload.get("s3_url"),
            "encoding_path": encoding_s3_path
        }
    finally:
        if Path(temp_encoding_path).exists():
            os.remove(temp_encoding_path)

def verify_face(user_id: str, image_path: str) -> dict:
    """
    Login-ல face verify பண்ணு
    """
    encoding_s3_path = f"faces/{user_id}.npy"
    local_encoding_path = f"temp_downloads/faces/{user_id}.npy"

    download_result = s3_storage.download_file(encoding_s3_path, local_encoding_path)
    if not download_result["success"]:
        error_text = str(download_result.get("error", "")).lower()
        if "not found" in error_text or "nosuchkey" in error_text or "404" in error_text:
            return {"success": False, "error": "Registered face இல்ல!"}
        return {
            "success": False,
            "error": download_result.get("error", "Failed to load registered face")
        }

    try:
        stored_encoding = np.load(local_encoding_path)
    finally:
        if Path(local_encoding_path).exists():
            os.remove(local_encoding_path)
    
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
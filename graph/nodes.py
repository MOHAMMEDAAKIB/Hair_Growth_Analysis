from ultralytics import YOLO
import cv2
import os
from pathlib import Path
import base64
from groq import Groq
from dotenv import load_dotenv
from utils.s3_storage import s3_storage

load_dotenv()

yolo_model = YOLO("best.pt")
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

# ── Node 1: Head Detect ──
def detect_head(state):
    print("🔍 Node 1: Head Detecting...")

    results = yolo_model(state["image_path"], verbose=False)
    boxes = results[0].boxes

    if len(boxes) == 0:
        return {
            "head_detected": False,
            "error": "Head detect ஆகல! Clear image upload பண்ணுங்க"
        }

    best_box = max(boxes, key=lambda b: b.conf[0])
    confidence = best_box.conf[0].item()
    x1, y1, x2, y2 = map(int, best_box.xyxy[0].tolist())

    return {
        "head_detected": True,
        "confidence": round(confidence, 2),
        "bbox": [x1, y1, x2, y2]
    }

# ── Node 2: Head Crop ──
def crop_head(state):
    print("✂️  Node 2: Head Cropping...")

    img = cv2.imread(state["image_path"])
    x1, y1, x2, y2 = state["bbox"]

    pad = 20
    h, w = img.shape[:2]
    x1 = max(0, x1 - pad)
    y1 = max(0, y1 - pad)
    x2 = min(w, x2 + pad)
    y2 = min(h, y2 + pad)

    head_crop = img[y1:y2, x1:x2]

    # Save temporarily to disk
    os.makedirs("temp_uploads", exist_ok=True)
    temp_crop_path = f"temp_uploads/crop_{state['user_id']}.jpg"
    cv2.imwrite(temp_crop_path, head_crop)
    
    # Get count from S3
    list_result = s3_storage.list_user_images(state["user_id"])
    count = len(list_result.get("images", [])) + 1
    
    # Upload to S3
    s3_path = f"users/{state['user_id']}/image_{count}.jpg"
    upload_result = s3_storage.upload_image(temp_crop_path, s3_path)
    
    # Clean up temp file
    os.remove(temp_crop_path)
    
    if not upload_result["success"]:
        return {"error": f"Failed to upload to S3: {upload_result.get('error')}"}
    
    return {
        "head_crop_path": upload_result["s3_path"],
        "head_crop_url": upload_result["s3_url"]
    }

# ── Node 3: Analyze Hair ──
def analyze_hair(state):
    print("📊 Node 3: Analyzing Hair...")

    if state["is_first_image"]:
        return {"analysis_result": "First image stored successfully!"}

    def to_base64(s3_path):
        # Download from S3 temporarily
        download_result = s3_storage.download_image(s3_path)
        if not download_result["success"]:
            raise Exception(f"Failed to download {s3_path}: {download_result.get('error')}")
        
        local_path = download_result["local_path"]
        with open(local_path, "rb") as f:
            b64 = base64.standard_b64encode(f.read()).decode("utf-8")
        
        # Clean up
        os.remove(local_path)
        return b64

    before_b64 = to_base64(state["previous_image_path"])
    after_b64  = to_base64(state["head_crop_path"])

    # Groq call
    response = groq_client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        max_tokens=1024,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """இந்த 2 images-ல hair growth analyze பண்ணு.
                        Before & After compare பண்ணி:
                        1. Hair density மாறுதா?
                        2. Hair thickness மாறுதா?
                        3. Growth areas எங்க இருக்கு?
                        4. Overall growth percentage estimate பண்ணு
                        5. Recommendation என்ன?
                        Tamil-ல detailed-ஆ சொல்லு."""
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{before_b64}"
                        }
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{after_b64}"
                        }
                    }
                ]
            }
        ]
    )

    analysis = response.choices[0].message.content
    print("✅ Groq Analysis Done!")
    return {"analysis_result": analysis}

# ── Node 4: Generate Report ──
def generate_report(state):
    print("📝 Node 4: Generating Report...")

    if state["is_first_image"]:
        report = {
            "status": "success",
            "message": "First image registered!",
            "user_id": state["user_id"],
            "image_stored": state["head_crop_path"],
            "image_url": state.get("head_crop_url", ""),
            "confidence": state["confidence"]
        }
    else:
        report = {
            "status": "success",
            "user_id": state["user_id"],
            "confidence": state["confidence"],
            "before_image": state["previous_image_path"],
            "after_image": state["head_crop_path"],
            "after_image_url": state.get("head_crop_url", ""),
            "hair_analysis": state["analysis_result"]
        }

    return {"report": report}

# ── Error Check ──
def check_error(state):
    if state.get("error"):
        return "error"
    return "continue"
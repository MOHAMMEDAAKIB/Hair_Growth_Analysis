from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from pathlib import Path
import shutil
import os
from graph.flow import hair_graph
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

app = FastAPI(title="Hair Growth Analysis API 💇")

UPLOAD_TEMP = "temp_uploads"
os.makedirs(UPLOAD_TEMP, exist_ok=True)

@app.get("/")
def home():
    return FileResponse("index.html")

@app.get("/ui")
def serve_ui():
    return FileResponse("templates/index.html")

@app.post("/first-image")
async def register_first_image(
    user_id: str = Form(...),
    file: UploadFile = File(...)
):
    # Temp save
    temp_path = f"{UPLOAD_TEMP}/{file.filename}"
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Graph run
    result = hair_graph.invoke({
        "user_id": user_id,
        "image_path": temp_path,
        "is_first_image": True,
        "head_detected": False,
        "bbox": None,              # ← இது add பண்ணு
        "head_crop_path": None,
        "confidence": None,
        "previous_image_path": None,
        "analysis_result": None,
        "report": None,
        "error": None
    })

    # Temp file delete
    os.remove(temp_path)

    if result.get("error"):
        return JSONResponse({"error": result["error"]}, status_code=400)

    return JSONResponse(result["report"])

@app.post("/analyze")
async def analyze_hair_growth(
    user_id: str = Form(...),
    file: UploadFile = File(...)
):
    # Previous image find
    user_folder = f"storage/users/{user_id}"
    if not Path(user_folder).exists():
        return JSONResponse(
            {"error": "User இல்ல! முதல்ல /register பண்ணுங்க"},
            status_code=404
        )

    # Previous image
    images = sorted(Path(user_folder).glob("*.jpg"))
    if not images:
        return JSONResponse(
            {"error": "Previous image இல்ல!"},
            status_code=404
        )

    previous_path = str(images[-1])

    # Temp save
    temp_path = f"{UPLOAD_TEMP}/{file.filename}"
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Graph run
    result = hair_graph.invoke({
        "user_id": user_id,
        "image_path": temp_path,
        "is_first_image": False,
        "head_detected": False,
        "bbox": None,
        "head_crop_path": None,
        "confidence": None,
        "previous_image_path": previous_path,
        "analysis_result": None,
        "report": None,
        "error": None
    })

    os.remove(temp_path)

    if result.get("error"):
        return JSONResponse({"error": result["error"]}, status_code=400)

    return JSONResponse(result["report"])
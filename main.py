from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path
import shutil
import os
from graph.flow import hair_graph
from fastapi.staticfiles import StaticFiles
from auth.routes import router as auth_router
from auth.database import supabase
from auth.face_verify import save_face
from utils.s3_storage import s3_storage


app = FastAPI(title="Hair Growth Analysis API 💇")
app.include_router(auth_router)

# Serve saved images/files (e.g., profile face images) to frontend.
app.mount("/storage", StaticFiles(directory="storage"), name="storage")
# Serve dashboard UI assets (logos/icons) used by templates.
app.mount("/ui/assets", StaticFiles(directory="templates/assats"), name="ui-assets")

UPLOAD_TEMP = "temp_uploads"
os.makedirs(UPLOAD_TEMP, exist_ok=True)

#@app.get("/")
#def home():
#    return FileResponse("index.html")

@app.get("/img/{user_id}/")
async def get_image(user_id: str):
    """Get the latest image for a user from S3"""
    result = s3_storage.get_latest_user_image(user_id)
    
    if not result["success"]:
        return JSONResponse(
            {"error": "Image இல்ல! முதல்ல register பண்ணுங்க"},
            status_code=404
        )
    
    # Return S3 URL for the image
    return JSONResponse({
        "image_url": result.get("s3_url"),
        "s3_path": result.get("s3_path")
    })

@app.get("/user/register")
def register_page():
    return FileResponse("templates/register.html")

@app.get("/")
def login_page():
    return FileResponse("templates/login.html")

@app.get("/ui/dashboard")
def dashboard_page():
    return FileResponse("templates/dashboard.html")

@app.get("/allImages/{user_id}/")
async def get_all_images(user_id: str):
    """Get all images for a user from S3"""
    result = s3_storage.get_all_user_images(user_id)
    
    if not result["success"]:
        return JSONResponse(
            {"error": "Images இல்ல! முதல்ல register பண்ணுங்க"},
            status_code=404
        )
    
    # Return list of S3 URLs for the images
    return JSONResponse({
        "images": result.get("images", [])
    })

@app.post("/register")
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
        "bbox": None,              
        "head_crop_path": None,
        "confidence": None,
        "previous_image_path": None,
        "analysis_result": None,
        "report": None,
        "error": None
    })

    if result.get("error"):
        os.remove(temp_path)
        return JSONResponse({"error": result["error"]}, status_code=400)

    # If this user has no face registered yet, use first uploaded image to create face profile.
    user_row = (
        supabase.table("users")
        .select("id, email, face_path")
        .eq("id", user_id)
        .execute()
    )

    if user_row.data:
        user_data = user_row.data[0]
        if not user_data.get("face_path"):
            email = user_data.get("email")
            if not email:
                os.remove(temp_path)
                return JSONResponse({"error": "User email missing for face setup"}, status_code=400)

            face_user_id = email.split("@")[0]
            face_result = save_face(face_user_id, temp_path)
            if not face_result.get("success"):
                os.remove(temp_path)
                return JSONResponse({"error": face_result.get("error", "Face setup failed")}, status_code=400)

            supabase.table("users").update({
                "face_path": face_result["face_path"]
            }).eq("id", user_id).execute()

    # Temp file delete
    os.remove(temp_path)

    report = result["report"]
    # S3 URL is already included in the report
    return JSONResponse(report)

@app.post("/analyze")
async def analyze_hair_growth(
    user_id: str = Form(...),
    file: UploadFile = File(...)
):
    # Get previous image from S3
    latest_image_result = s3_storage.get_latest_user_image(user_id)
    if not latest_image_result["success"]:
        return JSONResponse(
            {"error": "Previous image இல்ல!"},
            status_code=404
        )
    
    previous_s3_path = latest_image_result["s3_path"]

    # Temp save new image
    temp_path = f"{UPLOAD_TEMP}/{file.filename}"
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # Graph run - pass S3 path for previous image
    result = hair_graph.invoke({
        "user_id": user_id,
        "image_path": temp_path,
        "is_first_image": False,
        "head_detected": False,
        "bbox": None,
        "head_crop_path": None,
        "confidence": None,
        "previous_image_path": previous_s3_path,
        "analysis_result": None,
        "report": None,
        "error": None
    })

    os.remove(temp_path)

    if result.get("error"):
        return JSONResponse({"error": result["error"]}, status_code=400)

    return JSONResponse(result["report"])


@app.get("/history/{user_id}")
async def get_user_history(user_id: str):
    try:
        result = (
            supabase.table("history")
            .select("id, user_id, type, date, confidence, summary, created_at")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .execute()
        )
        return JSONResponse({"history": result.data or []})
    except Exception as e:
        error_text = str(e)
        if "PGRST205" in error_text or "Could not find the table 'public.history'" in error_text:
            return JSONResponse(
                {"history": [], "detail": "History table is not created in Supabase yet."},
                status_code=200
            )
        return JSONResponse(
            {"detail": f"Failed to fetch history: {str(e)}"},
            status_code=500
        )


@app.post("/history")
async def save_user_history(
    user_id: str = Form(...),
    type: str = Form(...),
    date: str = Form(...),
    confidence: float = Form(None),
    summary: str = Form(None)
):
    try:
        payload = {
            "user_id": user_id,
            "type": type,
            "date": date,
            "confidence": confidence,
            "summary": summary,
        }

        result = supabase.table("history").insert(payload).execute()
        return JSONResponse({"status": "success", "history": result.data[0] if result.data else payload})
    except Exception as e:
        error_text = str(e)
        if "PGRST205" in error_text or "Could not find the table 'public.history'" in error_text:
            return JSONResponse(
                {"detail": "History table is missing in Supabase. Create it before saving history."},
                status_code=503
            )
        return JSONResponse(
            {"detail": f"Failed to save history: {str(e)}"},
            status_code=500
        )
from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import JSONResponse
from pathlib import Path
import shutil
import os
from graph.flow import hair_graph
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from auth.routes import router as auth_router
from fastapi.responses import FileResponse
from auth.database import supabase


app = FastAPI(title="Hair Growth Analysis API 💇")
app.include_router(auth_router)

# Serve saved images/files (e.g., profile face images) to frontend.
app.mount("/storage", StaticFiles(directory="storage"), name="storage")

UPLOAD_TEMP = "temp_uploads"
os.makedirs(UPLOAD_TEMP, exist_ok=True)

#@app.get("/")
#def home():
#    return FileResponse("index.html")

@app.get("/user/register")
def register_page():
    return FileResponse("templates/register.html")

@app.get("/")
def login_page():
    return FileResponse("templates/login.html")

@app.get("/ui/dashboard")
def dashboard_page():
    return FileResponse("templates/dashboard.html")

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
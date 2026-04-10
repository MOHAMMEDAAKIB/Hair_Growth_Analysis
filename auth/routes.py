from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse
from passlib.context import CryptContext
from auth.database import supabase
from auth.face_verify import save_face, verify_face
import shutil
import os

router = APIRouter(prefix="/auth", tags=["Authentication"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TEMP_DIR = "temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)

# ── Register ──
@router.post("/register")
async def register(
    name:     str        = Form(...),
    email:    str        = Form(...),
    password: str        = Form(...),
    face:     UploadFile = File(...)
):
    # Email exists check
    existing = supabase.table("users")\
        .select("id")\
        .eq("email", email)\
        .execute()

    if existing.data:
        raise HTTPException(
            status_code=400,
            detail="Email already registered!"
        )

    # Face temp save
    temp_path = f"{TEMP_DIR}/reg_{face.filename}"
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(face.file, f)

    user_id = email.split("@")[0]

    # Face save
    face_result = save_face(user_id, temp_path)
    os.remove(temp_path)

    if not face_result["success"]:
        raise HTTPException(
            status_code=400,
            detail=face_result["error"]
        )

    # Password hash
    hashed_password = pwd_context.hash(password)

    # Supabase-ல save
    result = supabase.table("users").insert({
        "name":      name,
        "email":     email,
        "password":  hashed_password,
        "face_path": face_result["face_path"]
    }).execute()

    return JSONResponse({
        "status":  "success",
        "message": f"Welcome {name}! Registration complete ✅",
        "user_id": result.data[0]["id"],
        "email":   email,
        "face_path": face_result["face_path"],
        "face_url": f"/{face_result['face_path'].replace(os.sep, '/')}"
    })

# ── Login ──
@router.post("/login")
async def login(
    email:    str        = Form(...),
    password: str        = Form(...),
    face:     UploadFile = File(...)
):
    # User find
    result = supabase.table("users")\
        .select("*")\
        .eq("email", email)\
        .execute()

    if not result.data:
        raise HTTPException(
            status_code=404,
            detail="Email registered இல்ல!"
        )

    user = result.data[0]

    # Password check
    if not pwd_context.verify(password, user["password"]):
        raise HTTPException(
            status_code=401,
            detail="Password தப்பு!"
        )

    # Face temp save
    temp_path = f"{TEMP_DIR}/login_{face.filename}"
    with open(temp_path, "wb") as f:
        shutil.copyfileobj(face.file, f)

    user_id = email.split("@")[0]

    # Face verify
    face_result = verify_face(user_id, temp_path)
    os.remove(temp_path)

    if not face_result["success"]:
        raise HTTPException(
            status_code=401,
            detail=face_result["error"]
        )

    return JSONResponse({
        "status":          "success",
        "message":         f"Welcome back {user['name']}! 👋",
        "user_id":         user["id"],
        "email":           user["email"],
        "name":            user["name"],
        "face_similarity": face_result["similarity"],
        "face_path":       user.get("face_path"),
        "face_url":        f"/{user['face_path'].replace(os.sep, '/')}" if user.get("face_path") else None
    })

# ── Get User ──
@router.get("/user/{email}")
async def get_user(email: str):
    result = supabase.table("users")\
        .select("id, name, email, created_at")\
        .eq("email", email)\
        .execute()

    if not result.data:
        raise HTTPException(
            status_code=404,
            detail="User இல்ல!"
        )

    return JSONResponse(result.data[0])
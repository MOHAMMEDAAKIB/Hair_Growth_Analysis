from fastapi import APIRouter, File, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from passlib.context import CryptContext
from auth.database import supabase
from auth.face_verify import verify_face
from utils.s3_storage import s3_storage
import shutil
import os

router = APIRouter(prefix="/auth", tags=["Authentication"])

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

TEMP_DIR = "temp_uploads"
os.makedirs(TEMP_DIR, exist_ok=True)


def _normalize_face_s3_path(face_path: str, email: str = None) -> str:
    """Normalize various face path formats to S3 key format: faces/<user>.jpg."""
    if face_path:
        p = str(face_path).strip().replace("\\", "/")
        if p.startswith("http://") or p.startswith("https://"):
            return p
        if p.startswith("storage/"):
            p = p[len("storage/"):]
        if p.startswith("faces/"):
            return p

    if email and "@" in email:
        return f"faces/{email.split('@')[0]}.jpg"

    return ""


def _build_face_url(face_path: str, email: str = None) -> str:
    normalized = _normalize_face_s3_path(face_path, email)
    if not normalized:
        return None
    if normalized.startswith("http://") or normalized.startswith("https://"):
        return normalized
    return s3_storage.get_public_url(normalized)

# ── Register ──
@router.post("/register")
async def register(
    name:     str        = Form(...),
    email:    str        = Form(...),
    password: str        = Form(...)
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

    # Password hash
    hashed_password = pwd_context.hash(password)

    # Supabase-ல save
    result = supabase.table("users").insert({
        "name":      name,
        "email":     email,
        "password":  hashed_password,
        "face_path": None
    }).execute()

    return JSONResponse({
        "status":  "success",
        "message": "Step 1 complete. Upload first image to finish registration.",
        "user_id": result.data[0]["id"],
        "email":   email,
        "name": name
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
        "face_url":        _build_face_url(user.get("face_path"), user.get("email"))
    })

# ── Get User ──
@router.get("/user/{email}")
async def get_user(email: str):
    result = supabase.table("users")\
        .select("id, name, email, created_at, face_path")\
        .eq("email", email)\
        .execute()

    if not result.data:
        raise HTTPException(
            status_code=404,
            detail="User இல்ல!"
        )

    user = result.data[0]
    return JSONResponse({
        **user,
        "face_url": _build_face_url(user.get("face_path"), user.get("email"))
    })


@router.get("/face-image/{email}")
async def get_face_image(email: str):
    """Resolve user face image and redirect to public S3 URL."""
    result = supabase.table("users")\
        .select("email, face_path")\
        .eq("email", email)\
        .execute()

    if not result.data:
        raise HTTPException(status_code=404, detail="User இல்ல!")

    user = result.data[0]
    url = _build_face_url(user.get("face_path"), user.get("email"))
    if not url:
        raise HTTPException(status_code=404, detail="Face image not found")

    return RedirectResponse(url=url, status_code=307)
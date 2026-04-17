# S3 Storage Setup Guide

## Overview
Your Hair AI project now uses Supabase S3 buckets for image storage instead of local file storage. This provides scalability, security, and cloud-based backup.

## Prerequisites
1. ✅ Python 3.9+
2. ✅ Supabase account
3. ✅ Active Supabase project

## Step 1: Supabase Configuration

### 1.1 Create S3 Bucket in Supabase
1. Go to your Supabase project dashboard
2. Navigate to **Storage** → **Buckets**
3. Create a new bucket named: `hair-ai-images`
4. Make it **Public** for easy image access from frontend
5. Leave other settings as default

### 1.2 Get Credentials
1. In Supabase dashboard, go to **Settings** → **API**
2. Copy:
  - **Project URL** (SUPABASE_URL)
  - **service_role** key (SUPABASE_KEY) for database/backend APIs
3. In Supabase dashboard, create S3-compatible credentials:
  - **Storage** → **S3 Access Keys**
  - Create an access key pair and copy:
    - SUPABASE_S3_ACCESS_KEY_ID
    - SUPABASE_S3_SECRET_ACCESS_KEY

  **⚠️ Do not use `sb_publishable_*` as S3 credentials**

## Step 2: Environment Configuration

### 2.1 Create `.env` file
Create a `.env` file in the project root:

```bash
# Supabase
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_KEY=your-service-role-key-here
SUPABASE_S3_ACCESS_KEY_ID=your-s3-access-key-id
SUPABASE_S3_SECRET_ACCESS_KEY=your-s3-secret-access-key
SUPABASE_BUCKET_NAME=hair-ai-images

# Groq API (existing)
GROQ_API_KEY=your-groq-api-key-here
```

### 2.2 Never commit `.env` to Git
Ensure `.env` is in `.gitignore`:
```
echo ".env" >> .gitignore
```

## Step 3: Install Dependencies

```bash
# Install/update packages
pip install -r requirements.txt
```

New packages added:
- **boto3** - AWS SDK for S3 operations
- **supabase** - Supabase client (updated)

## Step 4: Test Configuration

Run a quick test:
```bash
python -c "from utils.s3_storage import s3_storage; print('✅ S3 configured successfully!')"
```

If you see ✅, configuration is complete!

## Step 5: Start the Application

```bash
# Make sure you're in the project directory
cd e:\Projects\hair_AI_pro\headDetectModule

# Start the API server
uvicorn main:app --reload
```

Should see: `✅ Application startup complete`

## API Changes

### Image Retrieval
**Old:** `GET /img/user123/` → Direct image file
**New:** `GET /img/user123/` → S3 URL JSON

Example response:
```json
{
  "image_url": "https://project.supabase.co/storage/v1/object/public/hair-ai-images/users/user123/image_1.jpg",
  "s3_path": "users/user123/image_1.jpg"
}
```

### Image Upload/Analysis
- `/register` endpoint saves to S3 automatically
- `/analyze` endpoint retrieves previous image from S3
- Returns `image_url` in response for frontend use

## File Structure

```
headDetectModule/
├── utils/
│   └── s3_storage.py          ← NEW: S3 operations
├── graph/
│   └── nodes.py               ← UPDATED: Uses S3
├── main.py                    ← UPDATED: S3 integration
├── requirements.txt           ← UPDATED: boto3, supabase
├── .env                       ← NEW: Your credentials (don't commit!)
├── .env.example               ← Example template
└── temp_uploads/              ← Still used for temp processing
```

## Troubleshooting

### ❌ "SUPABASE_URL not found"
- Check `.env` file exists in project root
- Check `python-dotenv` is installed: `pip install python-dotenv`
- Verify variable names exactly match `.env`

### ❌ "Bucket not found"
- Check bucket exists in Supabase: **Storage** → **Buckets**
- Verify bucket name matches `SUPABASE_BUCKET_NAME` in `.env`
- Ensure bucket is **Public**

### ❌ "Access denied" or "Unauthorized"
- Check `SUPABASE_S3_ACCESS_KEY_ID` and `SUPABASE_S3_SECRET_ACCESS_KEY`
- Ensure you are using S3 access keys from **Storage → S3 Access Keys**
- Use **service_role** key for backend database/API calls, not for S3 auth
- Verify bucket permissions

### ❌ "boto3" module not found
```bash
pip install boto3
```

### ❌ "S3 upload fails"
- Check internet connection
- Verify Supabase project is active
- Check S3 bucket storage quota

## Migration from Local Storage

If you have existing images in `storage/users/`:

### Option 1: Manual Migration (GUI)
1. Go to Supabase Storage dashboard
2. Create `users/` folder in `hair-ai-images` bucket
3. Upload existing images manually

### Option 2: Programmatic Migration
Run this Python script:
```python
from utils.s3_storage import s3_storage
import os
from pathlib import Path

# Upload all existing images
for user_folder in Path("storage/users").glob("*"):
    user_id = user_folder.name
    for img_file in user_folder.glob("*.jpg"):
        s3_path = f"users/{user_id}/{img_file.name}"
        s3_storage.upload_image(str(img_file), s3_path)
        print(f"✅ Migrated {s3_path}")
```

After migration, you can optionally delete local `storage/users/` folder.

## S3 API Methods Available

In your code, you can use S3Storage methods:

```python
from utils.s3_storage import s3_storage

# Upload image
result = s3_storage.upload_image("local_file.jpg", "users/user123/image.jpg")

# Download image
result = s3_storage.download_image("users/user123/image.jpg", "local_path.jpg")

# Get latest user image
result = s3_storage.get_latest_user_image("user123")

# List user images
result = s3_storage.list_user_images("user123")

# Delete image
result = s3_storage.delete_image("users/user123/image.jpg")

# Get signed URL (expires in 1 hour by default)
result = s3_storage.get_signed_url("users/user123/image.jpg")
```

All methods return: `{"success": bool, ...}`

## Production Considerations

### 1. Bucket Policies
In Supabase, set appropriate bucket policies for:
- Public read access for displaying images
- Backend write access via API key
- Optional: Restrict to specific roles

### 2. Storage Quota
Monitor your Supabase storage:
- Go to **Settings** → **Usage**
- Set billing alerts if needed

### 3. Cleanup
- Temp files in `temp_uploads/` and `temp_downloads/` are auto-cleaned
- Old image versions can be manually deleted from S3
- Consider archiving old user images

### 4. Backup
- Supabase provides automatic backups
- Configure in **Settings** → **Backups**

## Support

For Supabase S3 issues:
- Docs: https://supabase.com/docs/guides/storage

For boto3 issues:
- Docs: https://boto3.amazonaws.com/v1/documentation/api/latest/index.html

---

**✅ Setup Complete!** Your Hair AI app now uses S3 storage. 🎉

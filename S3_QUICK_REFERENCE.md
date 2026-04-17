# S3 Storage - Quick Reference Card

## Environment Setup
```bash
# Copy template
cp .env.example .env

# Add to .env
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
SUPABASE_S3_ACCESS_KEY_ID=your-s3-access-key-id
SUPABASE_S3_SECRET_ACCESS_KEY=your-s3-secret-access-key
SUPABASE_BUCKET_NAME=hair-ai-images
GROQ_API_KEY=your-groq-key
```

## Installation
```bash
pip install -r requirements.txt
```

## Testing
```bash
# Test configuration
python test_s3_setup.py

# Migrate existing images
python migrate_to_s3.py

# Start server
uvicorn main:app --reload
```

---

## API Usage

### Python (Backend)

#### Import
```python
from utils.s3_storage import s3_storage
```

#### Upload
```python
result = s3_storage.upload_image("local.jpg", "users/user123/image_1.jpg")
# Returns: {"success": True, "s3_path": "...", "s3_url": "..."}
```

#### Download
```python
result = s3_storage.download_image("users/user123/image_1.jpg")
# Returns: {"success": True, "local_path": "temp_downloads/image_1.jpg"}
```

#### Get Latest
```python
result = s3_storage.get_latest_user_image("user123")
# Returns: {"success": True, "s3_path": "...", "s3_url": "..."}
```

#### List
```python
result = s3_storage.list_user_images("user123")
# Returns: {"success": True, "images": ["users/user123/image_1.jpg", ...]}
```

#### Delete
```python
result = s3_storage.delete_image("users/user123/image_1.jpg")
# Returns: {"success": True}
```

#### Signed URL
```python
result = s3_storage.get_signed_url("users/user123/image_1.jpg", expiration=3600)
# Returns: {"success": True, "url": "https://...?token=..."}
```

---

### HTTP Endpoints

#### Get Latest Image
```
GET /img/{user_id}/
```
Response:
```json
{
    "image_url": "https://...",
    "s3_path": "users/user123/image_1.jpg"
}
```

#### Register (Upload)
```
POST /register
Form Data:
  - user_id: string
  - file: image file
```
Response:
```json
{
    "status": "success",
    "image_url": "https://...",
    "image_stored": "users/user123/image_1.jpg"
}
```

#### Analyze (Compare)
```
POST /analyze
Form Data:
  - user_id: string
  - file: image file
```
Response:
```json
{
    "status": "success",
    "after_image_url": "https://...",
    "hair_analysis": "..."
}
```

---

### JavaScript (Frontend)

#### Display Image
```javascript
async function displayUserImage(userId) {
  const response = await fetch(`/img/${userId}/`);
  const data = await response.json();
  document.getElementById('image').src = data.image_url;
}
```

#### Upload Image
```javascript
async function uploadImage(userId, file) {
  const formData = new FormData();
  formData.append('user_id', userId);
  formData.append('file', file);
  
  const response = await fetch('/register', {
    method: 'POST',
    body: formData
  });
  
  const data = await response.json();
  console.log('Image URL:', data.image_url);
}
```

---

## S3 Path Format

```
users/{user_id}/image_{count}.jpg
```

Examples:
- `users/john123/image_1.jpg` - First registration
- `users/john123/image_2.jpg` - First analysis
- `users/john123/image_3.jpg` - Second analysis

---

## Storage Structure

```
headDetectModule/
├── utils/
│   └── s3_storage.py          # Main module
├── graph/
│   └── nodes.py               # Updated nodes
├── main.py                    # Updated endpoints
├── requirements.txt           # Updated
├── test_s3_setup.py          # Test script
├── migrate_to_s3.py          # Migration
├── S3_SETUP_GUIDE.md         # Full guide
├── S3_DEVELOPER_GUIDE.md     # Dev reference
├── S3_MIGRATION_COMPLETE.md  # Summary
├── .env                       # Your credentials
├── .env.example              # Template
├── temp_uploads/             # Temp processing
└── temp_downloads/           # Temp analysis
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| "S3 client error" | Check .env variables |
| "Bucket not found" | Create bucket in Supabase |
| "Access denied" | Use service_role key |
| "InvalidAccessKeyId" | Use SUPABASE_S3_ACCESS_KEY_ID and SUPABASE_S3_SECRET_ACCESS_KEY |
| "Import error" | `pip install boto3` |
| "Upload fails" | Check internet & quota |
| "Download fails" | Check S3 path exists |

---

## Key Files

- **utils/s3_storage.py** - All S3 operations
- **graph/nodes.py** - Graph nodes (updated)
- **main.py** - FastAPI endpoints (updated)
- **requirements.txt** - Dependencies
- **test_s3_setup.py** - Verify setup
- **S3_SETUP_GUIDE.md** - Full instructions
- **S3_DEVELOPER_GUIDE.md** - API reference

---

## Common Workflows

### First Time Setup
1. `cp .env.example .env`
2. Edit .env
3. `pip install -r requirements.txt`
4. `python test_s3_setup.py`
5. `uvicorn main:app --reload`

### Migrate Existing Images
1. Ensure .env is configured
2. `python migrate_to_s3.py`
3. Confirm deletion of local files

### Debug S3 Issue
1. `python test_s3_setup.py`
2. Check error messages
3. See S3_SETUP_GUIDE.md Troubleshooting

### Use S3 in Custom Code
```python
from utils.s3_storage import s3_storage

result = s3_storage.upload_image("file.jpg", "users/123/img.jpg")
if result["success"]:
    print(f"URL: {result['s3_url']}")
```

---

## Important Reminders

✅ Never commit .env to Git
✅ Use service_role key (not anon)
✅ Bucket must be Public
✅ Temp files auto-cleanup
✅ Check storage quota regularly
✅ Update frontend for new URL format
✅ Keep SUPABASE_KEY private

---

For detailed information, see:
- S3_SETUP_GUIDE.md
- S3_DEVELOPER_GUIDE.md
- utils/s3_storage.py (code comments)

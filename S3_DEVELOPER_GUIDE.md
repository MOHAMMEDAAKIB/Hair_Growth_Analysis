# S3 Storage Integration - Developer Guide

## Overview

The Hair AI application now uses Supabase S3 for scalable image storage. This guide explains how the integration works and how to use it.

## Architecture

```
User Upload
     ↓
Temp Save (temp_uploads/)
     ↓
Process (Head Detection, Crop)
     ↓
Upload to S3
     ↓
Clean Temp Files
     ↓
Return S3 URL to Frontend
```

## S3 Storage Module

### Location
`utils/s3_storage.py`

### Usage

```python
from utils.s3_storage import s3_storage

# Global singleton instance - always use this
storage = s3_storage
```

### Available Methods

#### 1. Upload Image
```python
result = s3_storage.upload_image(
    local_path="path/to/image.jpg",
    s3_path="users/user123/image_1.jpg"
)

# Returns:
{
    "success": True,
    "s3_path": "users/user123/image_1.jpg",
    "s3_url": "https://project.supabase.co/storage/..."
}
```

#### 2. Download Image
```python
result = s3_storage.download_image(
    s3_path="users/user123/image_1.jpg",
    local_path="temp_downloads/image_1.jpg"  # Optional
)

# Returns:
{
    "success": True,
    "local_path": "temp_downloads/image_1.jpg"
}
```

#### 3. Get Latest User Image
```python
result = s3_storage.get_latest_user_image("user123")

# Returns:
{
    "success": True,
    "s3_path": "users/user123/image_3.jpg",
    "s3_url": "https://project.supabase.co/storage/..."
}
```

#### 4. List User Images
```python
result = s3_storage.list_user_images("user123")

# Returns:
{
    "success": True,
    "images": [
        "users/user123/image_1.jpg",
        "users/user123/image_2.jpg",
        "users/user123/image_3.jpg"
    ]
}
```

#### 5. Delete Image
```python
result = s3_storage.delete_image("users/user123/image_1.jpg")

# Returns:
{
    "success": True
}
```

#### 6. Get Signed URL
```python
result = s3_storage.get_signed_url(
    s3_path="users/user123/image_1.jpg",
    expiration=3600  # 1 hour in seconds
)

# Returns:
{
    "success": True,
    "url": "https://project.supabase.co/storage/...?token=..."
}
```

## Graph Flow Integration

### Node: crop_head()
Located in `graph/nodes.py`

**Changes:**
- Saves cropped head image to temp storage
- Counts existing images in S3
- Uploads crop to S3 with counter: `users/{user_id}/image_{count}.jpg`
- Returns S3 path and URL
- Cleans up temp file

**Error Handling:**
- Returns error if S3 upload fails
- Doesn't proceed to next node if upload fails

### Node: analyze_hair()
Located in `graph/nodes.py`

**Changes:**
- Receives S3 paths instead of local paths
- Downloads both images temporarily
- Converts to base64 for Groq API
- Cleans up temp files after analysis

**Workflow:**
```
previous_image_path (S3) → download → base64 → Groq
head_crop_path (S3) → download → base64 → Groq
```

### Node: generate_report()
Located in `graph/nodes.py`

**Changes:**
- Includes `image_url` in report for frontend display
- Maintains backward compatibility with S3 paths

## API Endpoints

### GET /img/{user_id}/
**Purpose:** Retrieve latest user image

**Response:**
```json
{
    "image_url": "https://project.supabase.co/storage/v1/object/public/hair-ai-images/users/user123/image_3.jpg",
    "s3_path": "users/user123/image_3.jpg"
}
```

**Frontend Usage:**
```html
<img src="https://project.supabase.co/storage/..." alt="User Hair">
```

### POST /register
**Purpose:** Register first image for user

**Returns:**
```json
{
    "status": "success",
    "message": "First image registered!",
    "user_id": "user123",
    "image_stored": "users/user123/image_1.jpg",
    "image_url": "https://project.supabase.co/storage/...",
    "confidence": 0.95
}
```

### POST /analyze
**Purpose:** Analyze hair growth with new image

**Returns:**
```json
{
    "status": "success",
    "user_id": "user123",
    "confidence": 0.93,
    "before_image": "users/user123/image_1.jpg",
    "after_image": "users/user123/image_2.jpg",
    "after_image_url": "https://project.supabase.co/storage/...",
    "hair_analysis": "Hair density has improved by 15%..."
}
```

## Frontend Integration

### Displaying Images from S3

```javascript
// Get latest image
const response = await fetch(`/img/user123/`);
const data = await response.json();
const imageUrl = data.image_url;

// Display
document.getElementById('profile-image').src = imageUrl;
```

### Using Public S3 URLs

S3 bucket is **public**, so you can:
- Direct link to images: `<img src="https://..." />`
- Download via API: `GET /img/{user_id}/`
- Embed in reports

## Storage Structure

```
S3 Bucket: hair-ai-images
├── users/
│   ├── user123/
│   │   ├── image_1.jpg    (First registration)
│   │   ├── image_2.jpg    (First analysis)
│   │   ├── image_3.jpg    (Second analysis)
│   │   └── ...
│   ├── user456/
│   │   ├── image_1.jpg
│   │   └── ...
│   └── ...
└── [future folders]
```

## Temp File Management

### Directories

| Directory | Purpose | Cleanup |
|-----------|---------|---------|
| `temp_uploads/` | User uploads | Auto-deleted after processing |
| `temp_downloads/` | S3 downloads during analysis | Auto-deleted after use |

### Cleanup Strategy
- All temp files are deleted after successful S3 upload
- Download temp files deleted after base64 conversion
- No manual cleanup needed (automatic)

## Error Handling

### Common Errors

#### 1. "Bucket not found"
```
Error: NoSuchBucket
Solution: 
- Check bucket exists in Supabase
- Verify SUPABASE_BUCKET_NAME in .env
```

#### 2. "Access denied"
```
Error: Forbidden / Unauthorized
Solution:
- Use service_role key (not anon key)
- Check bucket is public
- Verify SUPABASE_KEY in .env
```

#### 3. "SUPABASE_URL not configured"
```
Error: NoneType has no attribute 'format'
Solution:
- Create .env file
- Set SUPABASE_URL and SUPABASE_KEY
- Restart server
```

### Error Response Format

All S3 operations return:
```python
{
    "success": False,
    "error": "Descriptive error message"
}
```

## Performance Considerations

### Upload Performance
- Individual image: ~500ms - 2s (depends on size and internet)
- Parallel uploads possible but uses more bandwidth
- Consider batch uploads for multiple images

### Download Performance
- Per image: ~300ms - 1s
- Analysis downloads 2 images = ~1-2s additional latency
- Cached S3 URLs speed up repeated access

### Storage Quota
Monitor in Supabase:
- Settings → Usage
- Set billing alerts for overages
- Typical: ~1-5 MB per user

## Testing S3 Operations

### Manual Test
```python
from utils.s3_storage import s3_storage

# Test upload
result = s3_storage.upload_image(
    "test_image.jpg",
    "test/image.jpg"
)
print(result)

# Test download
result = s3_storage.download_image("test/image.jpg")
print(result)

# Cleanup
s3_storage.delete_image("test/image.jpg")
```

### Automated Test
```bash
python test_s3_setup.py
```

## Production Checklist

- [ ] S3 bucket created in Supabase
- [ ] Bucket set to public
- [ ] SUPABASE_URL and SUPABASE_KEY configured
- [ ] boto3 installed
- [ ] test_s3_setup.py passes
- [ ] temp_uploads/ and temp_downloads/ created
- [ ] Existing images migrated (optional)
- [ ] API tested with real images
- [ ] Frontend URLs updated to use new format
- [ ] Error handling tested
- [ ] Backup strategy configured

## Troubleshooting

### S3 Upload Slow
```
Cause: Large image size or poor internet
Solution:
- Compress images before upload
- Use CDN for faster delivery
- Consider image resizing before S3
```

### S3 Download Fails During Analysis
```
Cause: S3 path doesn't exist or network issue
Solution:
- Check user has images in S3
- Verify internet connection
- Check S3 bucket permissions
```

### Memory Issues with Large Images
```
Cause: Large images → large base64 strings
Solution:
- Resize images before upload
- Crop to needed area only
- Use 1-2 MB max per image
```

## Future Enhancements

- [ ] Image compression on upload
- [ ] Thumbnail generation
- [ ] Image versioning/history
- [ ] Batch operations
- [ ] Cache layer for frequently accessed images
- [ ] Analytics on image storage usage

---

For more information:
- [Supabase Storage Docs](https://supabase.com/docs/guides/storage)
- [boto3 Documentation](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html)

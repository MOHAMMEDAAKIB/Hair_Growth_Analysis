import boto3
import os
from dotenv import load_dotenv, find_dotenv
from pathlib import Path

# Load .env from project root even when app is started from another working directory.
load_dotenv(find_dotenv(usecwd=True))

class S3Storage:
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.bucket_name = os.getenv("SUPABASE_BUCKET_NAME", "hair-ai-images")
        self._config_error = None

        # Supabase S3-compatible credentials (recommended)
        self.s3_access_key_id = (
            os.getenv("SUPABASE_S3_ACCESS_KEY_ID")
            or os.getenv("AWS_ACCESS_KEY_ID")
        )
        self.s3_secret_access_key = (
            os.getenv("SUPABASE_S3_SECRET_ACCESS_KEY")
            or os.getenv("AWS_SECRET_ACCESS_KEY")
        )

        # Backward compatibility for older setup docs.
        fallback_key = os.getenv("SUPABASE_KEY")
        if not self.s3_access_key_id and not self.s3_secret_access_key and fallback_key:
            self.s3_access_key_id = fallback_key
            self.s3_secret_access_key = fallback_key
            print("⚠️ Using SUPABASE_KEY as S3 credentials fallback. Prefer SUPABASE_S3_ACCESS_KEY_ID and SUPABASE_S3_SECRET_ACCESS_KEY.")

        if not self.supabase_url:
            self._config_error = "SUPABASE_URL is missing. Set it in .env"
        elif not self.s3_access_key_id or not self.s3_secret_access_key:
            self._config_error = (
                "S3 credentials missing. Set SUPABASE_S3_ACCESS_KEY_ID and "
                "SUPABASE_S3_SECRET_ACCESS_KEY in .env"
            )
        elif str(self.s3_access_key_id).startswith("sb_publishable_"):
            self._config_error = (
                "SUPABASE_KEY is set to a publishable key, which cannot be used for S3. "
                "Create S3 access keys in Supabase Storage settings and set "
                "SUPABASE_S3_ACCESS_KEY_ID and SUPABASE_S3_SECRET_ACCESS_KEY."
            )
        
        # Supabase S3 endpoint
        self.s3_url = f"{self.supabase_url}/storage/v1/s3"

        self.s3_client = None
        if self._config_error:
            print(f"❌ S3 Config Error: {self._config_error}")
            return

        # Initialize boto3 S3 client for Supabase
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=self.s3_url,
            aws_access_key_id=self.s3_access_key_id,
            aws_secret_access_key=self.s3_secret_access_key,
            region_name="us-east-1"
        )

    def _ensure_client(self):
        if self._config_error:
            return {"success": False, "error": self._config_error}
        if not self.s3_client:
            return {"success": False, "error": "S3 client is not initialized"}
        return None

    def get_public_url(self, s3_path: str) -> str:
        return f"{self.supabase_url}/storage/v1/object/public/{self.bucket_name}/{s3_path}"

    def upload_file(self, local_path: str, s3_path: str, content_type: str = None) -> dict:
        """
        Upload any local file to S3.
        Args:
            local_path: Path to local file
            s3_path: S3 object key/path
            content_type: Optional MIME type
        """
        try:
            client_error = self._ensure_client()
            if client_error:
                return client_error

            if not os.path.exists(local_path):
                return {"success": False, "error": f"File not found: {local_path}"}

            extra_args = {"ContentType": content_type} if content_type else None
            with open(local_path, "rb") as f:
                if extra_args:
                    self.s3_client.upload_fileobj(f, self.bucket_name, s3_path, ExtraArgs=extra_args)
                else:
                    self.s3_client.upload_fileobj(f, self.bucket_name, s3_path)

            s3_url = self.get_public_url(s3_path)
            return {"success": True, "s3_path": s3_path, "s3_url": s3_url}
        except Exception as e:
            print(f"❌ S3 Upload Error: {str(e)}")
            return {"success": False, "error": str(e)}

    def download_file(self, s3_path: str, local_path: str = None) -> dict:
        """
        Download any S3 object to local path.
        Args:
            s3_path: S3 object key/path
            local_path: Optional local file path
        """
        try:
            client_error = self._ensure_client()
            if client_error:
                return client_error

            if not local_path:
                os.makedirs("temp_downloads", exist_ok=True)
                local_path = f"temp_downloads/{Path(s3_path).name}"

            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            self.s3_client.download_file(self.bucket_name, s3_path, local_path)
            return {"success": True, "local_path": local_path}
        except Exception as e:
            print(f"❌ S3 Download Error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def upload_image(self, local_path: str, s3_path: str) -> dict:
        """
        Upload local image to S3
        Args:
            local_path: Path to local image file
            s3_path: S3 path (e.g., 'users/user123/image_1.jpg')
        Returns:
            dict with success status and S3 URL
        """
        result = self.upload_file(local_path, s3_path, content_type="image/jpeg")
        if result.get("success"):
            print(f"✅ Uploaded to S3: {s3_path}")
        return result
    
    def download_image(self, s3_path: str, local_path: str = None) -> dict:
        """
        Download image from S3 to local temp storage
        Args:
            s3_path: S3 path (e.g., 'users/user123/image_1.jpg')
            local_path: Optional local path to save. If None, saves to temp_downloads/
        Returns:
            dict with success status and local file path
        """
        result = self.download_file(s3_path, local_path)
        if result.get("success"):
            print(f"✅ Downloaded from S3: {s3_path}")
        return result
    
    def list_user_images(self, user_id: str) -> dict:
        """
        List all images for a user
        Args:
            user_id: User ID
        Returns:
            dict with success status and list of image paths
        """
        try:
            client_error = self._ensure_client()
            if client_error:
                return client_error

            prefix = f"users/{user_id}/"
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            if "Contents" not in response:
                return {"success": True, "images": []}
            
            images = [obj["Key"] for obj in sorted(response["Contents"], key=lambda x: x["LastModified"])]
            
            return {"success": True, "images": images}
        except Exception as e:
            print(f"❌ S3 List Error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_latest_user_image(self, user_id: str) -> dict:
        """
        Get the latest image for a user
        Args:
            user_id: User ID
        Returns:
            dict with success status and latest image S3 path
        """
        try:
            client_error = self._ensure_client()
            if client_error:
                return client_error

            prefix = f"users/{user_id}/"
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            if "Contents" not in response or len(response["Contents"]) == 0:
                return {"success": False, "error": "No images found for user"}
            
            # Get latest by modification time
            latest = max(response["Contents"], key=lambda x: x["LastModified"])
            s3_path = latest["Key"]
            s3_url = self.get_public_url(s3_path)
            
            return {
                "success": True,
                "s3_path": s3_path,
                "s3_url": s3_url
            }
        except Exception as e:
            print(f"❌ S3 Error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def delete_image(self, s3_path: str) -> dict:
        """
        Delete image from S3
        Args:
            s3_path: S3 path (e.g., 'users/user123/image_1.jpg')
        Returns:
            dict with success status
        """
        try:
            client_error = self._ensure_client()
            if client_error:
                return client_error

            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=s3_path
            )
            print(f"✅ Deleted from S3: {s3_path}")
            return {"success": True}
        except Exception as e:
            print(f"❌ S3 Delete Error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_signed_url(self, s3_path: str, expiration: int = 3600) -> dict:
        """
        Get signed URL for S3 object
        Args:
            s3_path: S3 path
            expiration: URL expiration time in seconds (default 1 hour)
        Returns:
            dict with success status and signed URL
        """
        try:
            client_error = self._ensure_client()
            if client_error:
                return client_error

            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": s3_path
                },
                ExpiresIn=expiration
            )
            return {"success": True, "url": url}
        except Exception as e:
            print(f"❌ S3 URL Error: {str(e)}")
            return {"success": False, "error": str(e)}
        
    def get_all_user_images(self, user_id: str) -> dict:
        """
        Get all images for a user with their S3 URLs
        Args:
            user_id: User ID
        Returns:
            dict with success status and list of images with S3 paths and URLs
        """
        list_result = self.list_user_images(user_id)
        if not list_result.get("success"):
            return list_result
        
        images_info = []
        for s3_path in list_result.get("images", []):
            s3_url = self.get_public_url(s3_path)
            images_info.append({"s3_path": s3_path, "s3_url": s3_url})
        
        return {"success": True, "images": images_info}


# Global instance
s3_storage = S3Storage()

#!/usr/bin/env python3
"""
Migration script to move existing local files to S3.
Includes:
- user images from storage/users/
- face images and encodings from storage/faces/
Run: python migrate_to_s3.py
"""

import os
from pathlib import Path
from dotenv import load_dotenv

def migrate_images():
    """Migrate existing local images and face artifacts to S3"""
    load_dotenv()
    
    print("\n" + "="*60)
    print("  Hair AI: Local Storage → S3 Migration")
    print("="*60 + "\n")
    
    users_storage = Path("storage/users")
    faces_storage = Path("storage/faces")

    if not users_storage.exists() and not faces_storage.exists():
        print("ℹ️  No local storage found at 'storage/users/' or 'storage/faces/'")
        print("✅ Nothing to migrate!")
        return

    if users_storage.exists():
        print(f"Found user image storage at: {users_storage}")
    if faces_storage.exists():
        print(f"Found face storage at: {faces_storage}")
    print()
    
    try:
        from utils.s3_storage import s3_storage
    except ImportError as e:
        print(f"❌ Error: Could not import S3 storage module")
        print(f"   {str(e)}")
        print("\nMake sure:")
        print("  1. boto3 is installed: pip install boto3")
        print("  2. .env file is configured")
        print("  3. You're in the project root directory")
        return
    
    # Count assets
    user_folders = list(users_storage.glob("*")) if users_storage.exists() else []
    total_user_images = sum(len(list(folder.glob("*.jpg"))) for folder in user_folders)
    total_face_images = len(list(faces_storage.glob("*.jpg"))) if faces_storage.exists() else 0
    total_face_encodings = len(list(faces_storage.glob("*.npy"))) if faces_storage.exists() else 0
    total_assets = total_user_images + total_face_images + total_face_encodings

    if total_assets == 0:
        print("ℹ️  No local assets found in storage folders")
        print("✅ Nothing to migrate!")
        return
    
    print(f"Found:")
    print(f"  • {len(user_folders)} users")
    print(f"  • {total_user_images} user images")
    print(f"  • {total_face_images} face images")
    print(f"  • {total_face_encodings} face encodings (.npy)")
    print(f"  • {total_assets} total files\n")
    
    # Confirm before migrating
    response = input("Proceed with migration to S3? (yes/no): ").strip().lower()
    if response != "yes":
        print("Migration cancelled.")
        return
    
    print("\n" + "-"*60)
    print("Starting migration...\n")
    
    migrated = 0
    failed = 0
    
    # Migrate each user's images
    for user_folder in user_folders:
        user_id = user_folder.name
        images = sorted(user_folder.glob("*.jpg"))

        if not images:
            continue

        print(f"Migrating user '{user_id}' images...")

        for img_file in images:
            s3_path = f"users/{user_id}/{img_file.name}"

            try:
                result = s3_storage.upload_image(str(img_file), s3_path)

                if result["success"]:
                    print(f"  ✅ {img_file.name}")
                    migrated += 1
                else:
                    print(f"  ❌ {img_file.name} - {result.get('error', 'Unknown error')}")
                    failed += 1
            except Exception as e:
                print(f"  ❌ {img_file.name} - {str(e)}")
                failed += 1

        print()

    # Migrate face image + encoding files
    if faces_storage.exists():
        print("Migrating face artifacts...")
        face_files = sorted(list(faces_storage.glob("*.jpg")) + list(faces_storage.glob("*.npy")))
        for face_file in face_files:
            s3_path = f"faces/{face_file.name}"
            content_type = "image/jpeg" if face_file.suffix.lower() == ".jpg" else "application/octet-stream"
            try:
                result = s3_storage.upload_file(str(face_file), s3_path, content_type=content_type)
                if result["success"]:
                    print(f"  ✅ {face_file.name}")
                    migrated += 1
                else:
                    print(f"  ❌ {face_file.name} - {result.get('error', 'Unknown error')}")
                    failed += 1
            except Exception as e:
                print(f"  ❌ {face_file.name} - {str(e)}")
                failed += 1
        print()
    
    # Summary
    print("-"*60)
    print("\nMigration Summary:")
    print(f"  ✅ Migrated: {migrated} images")
    print(f"  ❌ Failed: {failed} images")
    print(f"  Total: {migrated + failed} images")
    
    if failed == 0:
        print("\n✅ All images migrated successfully!")
        
        # Ask about cleanup
        cleanup = input("\nDelete local storage folders after successful migration? (yes/no): ").strip().lower()
        if cleanup == "yes":
            import shutil
            if users_storage.exists():
                shutil.rmtree(users_storage)
                print(f"✅ Deleted {users_storage}")
            if faces_storage.exists():
                shutil.rmtree(faces_storage)
                print(f"✅ Deleted {faces_storage}")
    else:
        print(f"\n⚠️  {failed} images failed to migrate. Check your S3 configuration.")
    
    print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    try:
        migrate_images()
    except KeyboardInterrupt:
        print("\n\nMigration cancelled by user.")
    except Exception as e:
        print(f"\n❌ Migration error: {str(e)}")
        raise

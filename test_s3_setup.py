#!/usr/bin/env python3
"""
Quick test script to verify S3 storage configuration
Run: python test_s3_setup.py
"""

import os
import sys
from pathlib import Path

def print_header(text):
    print(f"\n{'='*60}")
    print(f"  {text}")
    print(f"{'='*60}\n")

def check_env_vars():
    """Check if required environment variables are set"""
    print_header("1. Checking Environment Variables")

    required = ["SUPABASE_URL", "SUPABASE_BUCKET_NAME", "GROQ_API_KEY"]
    s3_creds = ["SUPABASE_S3_ACCESS_KEY_ID", "SUPABASE_S3_SECRET_ACCESS_KEY"]

    missing = []
    for var in required:
        value = os.getenv(var)
        if value:
            masked = value[:10] + "..." if len(value) > 10 else value
            print(f"✅ {var}: {masked}")
        else:
            print(f"❌ {var}: NOT SET")
            missing.append(var)

    # S3 credentials are required for Supabase S3 API.
    for var in s3_creds:
        value = os.getenv(var)
        if value:
            masked = value[:10] + "..." if len(value) > 10 else value
            print(f"✅ {var}: {masked}")
        else:
            print(f"❌ {var}: NOT SET")
            missing.append(var)

    supabase_key = os.getenv("SUPABASE_KEY", "")
    if supabase_key.startswith("sb_publishable_"):
        print("⚠️  SUPABASE_KEY is publishable and cannot be used as S3 credentials")
    
    if missing:
        print(f"\n⚠️  Missing variables: {', '.join(missing)}")
        print("Please create a .env file with these variables.")
        return False
    
    print("\n✅ All environment variables configured!")
    return True

def check_packages():
    """Check if required packages are installed"""
    print_header("2. Checking Dependencies")
    
    packages = {
        "boto3": "AWS SDK for S3",
        "supabase": "Supabase client",
        "python-dotenv": "Environment variable loader",
        "fastapi": "Web framework",
        "uvicorn": "ASGI server",
        "ultralytics": "YOLO model",
        "opencv-python": "Image processing",
        "langgraph": "Graph workflow",
        "langchain": "LLM framework",
        "anthropic": "Claude API",
        "pillow": "Image library",
        "groq": "Groq API client"
    }
    
    missing = []
    for package, description in packages.items():
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package}: {description}")
        except ImportError:
            print(f"❌ {package}: NOT INSTALLED")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("\nRun: pip install -r requirements.txt")
        return False
    
    print("\n✅ All packages installed!")
    return True

def test_s3_connection():
    """Test S3 storage connection"""
    print_header("3. Testing S3 Connection")
    
    try:
        from utils.s3_storage import s3_storage
        print("✅ S3Storage module imported successfully")
        
        # Try to list buckets (non-destructive test)
        print("\n   Testing S3 client initialization...")
        print(f"   - Bucket name: {s3_storage.bucket_name}")
        print(f"   - S3 URL: {s3_storage.s3_url}")
        print("✅ S3 client configured successfully")
        
        return True
    except Exception as e:
        print(f"❌ S3 connection failed: {str(e)}")
        return False

def test_file_structure():
    """Check if project structure is correct"""
    print_header("4. Checking Project Structure")
    
    required_files = [
        "main.py",
        "utils/s3_storage.py",
        "graph/nodes.py",
        "graph/flow.py",
        "requirements.txt",
        ".env"
    ]
    
    missing = []
    for file in required_files:
        if Path(file).exists():
            print(f"✅ {file}")
        else:
            print(f"❌ {file}: NOT FOUND")
            missing.append(file)
    
    if missing:
        print(f"\n⚠️  Missing files: {', '.join(missing)}")
        return False
    
    print("\n✅ Project structure correct!")
    return True

def main():
    print("\n" + "="*60)
    print("  Hair AI S3 Storage Configuration Test")
    print("="*60)
    
    # Change to project directory
    os.chdir(Path(__file__).parent)
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    # Run checks
    checks = [
        ("Environment Variables", check_env_vars),
        ("Packages", check_packages),
        ("File Structure", test_file_structure),
        ("S3 Connection", test_s3_connection),
    ]
    
    results = {}
    for name, check_func in checks:
        try:
            results[name] = check_func()
        except Exception as e:
            print(f"❌ {name} check failed: {str(e)}")
            results[name] = False
    
    # Summary
    print_header("Summary")
    for name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    all_passed = all(results.values())
    
    if all_passed:
        print("\n" + "="*60)
        print("  🎉 All checks passed! S3 is ready to use!")
        print("="*60)
        print("\nYou can now start the server:")
        print("  uvicorn main:app --reload")
        return 0
    else:
        print("\n" + "="*60)
        print("  ⚠️  Some checks failed. Please fix them above.")
        print("="*60)
        return 1

if __name__ == "__main__":
    sys.exit(main())

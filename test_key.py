# test_key.py
from dotenv import load_dotenv
import os

load_dotenv()
key = os.getenv("GOOGLE_API_KEY")
print(f"Key found: {key[:20]}...")  
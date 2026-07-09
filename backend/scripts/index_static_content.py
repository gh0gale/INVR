import os
import sys
import json

# Add backend directory to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.vector_store import upsert_static_content_to_vectorstore

def index_static_content():
    # Index Educational Content
    edu_path = os.path.join(os.path.dirname(__file__), "..", "data", "educational_content.json")
    if os.path.exists(edu_path):
        with open(edu_path, "r") as f:
            edu_data = json.load(f)
            edu_content = [item["content"] for item in edu_data]
            upsert_static_content_to_vectorstore("educational", edu_content)
            print(f"Indexed {len(edu_content)} educational chunks.")
    
    # Index Gate Thresholds
    try:
        # Assuming gate_thresholds is in config module at root
        from config.gate_thresholds import GATE_THRESHOLDS
        threshold_content = []
        for key, value in GATE_THRESHOLDS.items():
            threshold_content.append(f"{key}: {json.dumps(value)}")
        if threshold_content:
            upsert_static_content_to_vectorstore("gate_threshold", threshold_content)
            print(f"Indexed {len(threshold_content)} gate threshold chunks.")
    except ImportError as e:
        print(f"GATE_THRESHOLDS not found, skipping. ({e})")

if __name__ == "__main__":
    index_static_content()

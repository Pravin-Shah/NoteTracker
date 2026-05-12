"""
Script to trigger brain ingestion.
Can be run manually or via cron.
Usage: python scripts/brain_ingest.py --user_id 1
"""
import argparse
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from apps.general.utils.brain_engine import BrainEngine

def main():
    parser = argparse.ArgumentParser(description="Ingest raw brain dumps.")
    parser.get_default("user_id")
    parser.add_argument("--user_id", type=int, default=1, help="User ID to process for")
    args = parser.parse_args()

    print(f"Starting brain ingestion for user {args.user_id}...")
    
    try:
        engine = BrainEngine(args.user_id)
        result = engine.ingest()
        print(f"Result: {result}")
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

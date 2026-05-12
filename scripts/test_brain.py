"""
Test script for Second Brain operations.
"""
import os
import sys

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from apps.general.utils.brain_ops import add_raw_dump, get_unprocessed, list_wiki_pages
from apps.general.utils.brain_engine import BrainEngine

def test_db_ops():
    print("Testing DB operations...")
    user_id = 1
    raw_id = add_raw_dump(user_id, "This is a test thought from a script.", source_type='test')
    print(f"Added raw dump {raw_id}")
    
    unprocessed = get_unprocessed(user_id)
    print(f"Found {len(unprocessed)} unprocessed dumps")
    assert any(r['id'] == raw_id for r in unprocessed)
    print("DB ops test PASSED")

def test_engine_mock():
    # This would require valid API keys, so we just check if it can initialize
    print("Testing BrainEngine initialization...")
    try:
        engine = BrainEngine(user_id=1)
        print("BrainEngine initialized")
    except Exception as e:
        print(f"BrainEngine init FAILED: {e}")

if __name__ == "__main__":
    test_db_ops()
    test_engine_mock()

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive refactoring script to add db_path parameter to all utility functions.
"""

import os
import re
import sys
import io
from pathlib import Path

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def refactor_file(file_path):
    """Refactor a single file to add db_path parameters."""
    print(f"Processing: {file_path}")

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    original_content = content

    # Pattern to match function definitions
    # This matches: def function_name(args):
    func_pattern = r'def\s+(\w+)\s*\(([^)]+)\)\s*(->\s*[^:]+)?\s*:'

    def add_db_path_to_function(match):
        func_name = match.group(1)
        params = match.group(2)
        return_type = match.group(3) or ''

        # Skip if already has db_path
        if 'db_path' in params:
            return match.group(0)

        # Skip special functions
        if func_name in ['__init__', '__str__', '__repr__', 'pytest_configure']:
            return match.group(0)

        # Add db_path parameter
        if params.strip():
            new_params = f"{params.rstrip()}, db_path: str = None"
        else:
            new_params = "db_path: str = None"

        return f"def {func_name}({new_params}) {return_type}:"

    # Replace all function definitions
    content = re.sub(func_pattern, add_db_path_to_function, content)

    # Now add db_path to all database calls
    db_calls = [
        'create_record', 'get_record', 'update_record', 'delete_record',
        'execute_query', 'execute_update', 'search_records'
    ]

    for call in db_calls:
        # Pattern: call_name( ... ) without db_path - replace with version including db_path
        # This handles various cases: single line, multiline, etc.

        # Pattern 1: Simple case: call_name(args)
        pattern1 = rf'(\b{call}\s*\(\s*["\']?[^)]*?["\']?\s*\))'

        # Pattern 2: With arguments: call_name('table', data)
        pattern2 = rf'(\b{call}\s*\([^)]*\))'

        # For each match, check if it already has db_path and add if not
        def add_db_path_to_call(match):
            call_str = match.group(0)

            # Skip if already has db_path
            if 'db_path' in call_str:
                return call_str

            # Find the closing parenthesis and insert db_path before it
            # Handle both cases: call(...) and call(...\n...  )
            if call_str.rstrip().endswith(')'):
                # Simple case
                return call_str[:-1] + ', db_path)'

            return call_str

        content = re.sub(pattern2, add_db_path_to_call, content)

    # Write back if changed
    if content != original_content:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  [OK] Refactored successfully")
        return True
    else:
        print(f"  [SKIP] No changes needed")
        return False

def main():
    """Main refactoring process."""
    project_root = Path(__file__).parent
    utils_dirs = [
        project_root / 'apps' / 'general' / 'utils',
        project_root / 'apps' / 'tradevault' / 'utils',
    ]

    # Files to refactor (excluding __init__.py)
    files_to_refactor = [
        'task_ops.py',
        'calendar_ops.py',
        'search_general.py',
        'edge_ops.py',
        'prompt_ops.py',
        'insight_ops.py',
        'analytics.py',
        'search.py',
    ]

    total_refactored = 0

    for utils_dir in utils_dirs:
        if not utils_dir.exists():
            print(f"Skipping (not found): {utils_dir}")
            continue

        print(f"\nProcessing directory: {utils_dir}")
        print("=" * 70)

        for filename in files_to_refactor:
            filepath = utils_dir / filename
            if filepath.exists():
                if refactor_file(str(filepath)):
                    total_refactored += 1
            else:
                print(f"Skipping (not found): {filepath}")

    print("\n" + "=" * 70)
    print(f"Total files refactored: {total_refactored}")
    print("=" * 70)

if __name__ == '__main__':
    main()

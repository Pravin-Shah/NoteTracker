#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test runner script for NoteTracker project.
Executes all tests with comprehensive reporting and coverage analysis.
"""

import subprocess
import sys
import os
from pathlib import Path
from typing import List, Tuple

# Set UTF-8 encoding for output
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class TestRunner:
    """Orchestrates test execution and reporting."""

    def __init__(self, project_root: str = None):
        """Initialize test runner."""
        self.project_root = project_root or str(Path(__file__).parent)
        self.test_dir = os.path.join(self.project_root, 'tests')
        self.reports_dir = os.path.join(self.project_root, 'test_reports')

        # Create reports directory if it doesn't exist
        os.makedirs(self.reports_dir, exist_ok=True)

    def run_unit_tests(self, verbose: bool = True) -> Tuple[int, str]:
        """Run all unit tests."""
        print("\n" + "="*70)
        print("[TEST] RUNNING UNIT TESTS")
        print("="*70 + "\n")

        cmd = [
            sys.executable, '-m', 'pytest',
            os.path.join(self.test_dir, 'unit'),
            '-m', 'unit',
            '--tb=short'
        ]

        if verbose:
            cmd.append('-v')

        result = subprocess.run(cmd, cwd=self.project_root)
        return result.returncode, "Unit Tests"

    def run_integration_tests(self, verbose: bool = True) -> Tuple[int, str]:
        """Run all integration tests."""
        print("\n" + "="*70)
        print("[TEST] RUNNING INTEGRATION TESTS")
        print("="*70 + "\n")

        cmd = [
            sys.executable, '-m', 'pytest',
            os.path.join(self.test_dir, 'integration'),
            '-m', 'integration',
            '--tb=short'
        ]

        if verbose:
            cmd.append('-v')

        result = subprocess.run(cmd, cwd=self.project_root)
        return result.returncode, "Integration Tests"

    def run_all_tests(self, verbose: bool = True) -> Tuple[int, str]:
        """Run all tests."""
        print("\n" + "="*70)
        print("[TEST] RUNNING ALL TESTS")
        print("="*70 + "\n")

        cmd = [
            sys.executable, '-m', 'pytest',
            self.test_dir,
            '--tb=short'
        ]

        if verbose:
            cmd.append('-v')

        result = subprocess.run(cmd, cwd=self.project_root)
        return result.returncode, "All Tests"

    def run_with_coverage(self, verbose: bool = True) -> Tuple[int, str]:
        """Run tests with coverage reporting."""
        print("\n" + "="*70)
        print("[COVERAGE] RUNNING TESTS WITH COVERAGE ANALYSIS")
        print("="*70 + "\n")

        cmd = [
            sys.executable, '-m', 'pytest',
            self.test_dir,
            '--cov=apps',
            '--cov=core',
            f'--cov-report=term',
            '--tb=short'
        ]

        if verbose:
            cmd.append('-v')

        result = subprocess.run(cmd, cwd=self.project_root)
        return result.returncode, "Tests with Coverage"

    def run_smoke_tests(self) -> Tuple[int, str]:
        """Run smoke tests (quick sanity checks)."""
        print("\n" + "="*70)
        print("[SMOKE] RUNNING SMOKE TESTS")
        print("="*70 + "\n")

        cmd = [
            sys.executable, '-m', 'pytest',
            self.test_dir,
            '-m', 'smoke',
            '-v',
            '--tb=short'
        ]

        result = subprocess.run(cmd, cwd=self.project_root)
        return result.returncode, "Smoke Tests"

    def run_specific_test(self, test_file: str, verbose: bool = True) -> Tuple[int, str]:
        """Run a specific test file."""
        print(f"\n" + "="*70)
        print(f"[TEST] RUNNING SPECIFIC TEST: {test_file}")
        print("="*70 + "\n")

        test_path = os.path.join(self.test_dir, test_file)
        if not os.path.exists(test_path):
            print(f"[ERROR] Test file not found: {test_path}")
            return 1, f"Test not found: {test_file}"

        cmd = [sys.executable, '-m', 'pytest', test_path, '--tb=short']

        if verbose:
            cmd.append('-v')

        result = subprocess.run(cmd, cwd=self.project_root)
        return result.returncode, f"Test: {test_file}"

    def run_module_tests(self, module_name: str) -> Tuple[int, str]:
        """Run tests for a specific module."""
        print(f"\n" + "="*70)
        print(f"[TEST] RUNNING TESTS FOR MODULE: {module_name}")
        print("="*70 + "\n")

        cmd = [
            sys.executable, '-m', 'pytest',
            self.test_dir,
            '-k', module_name,
            '-v',
            '--tb=short'
        ]

        result = subprocess.run(cmd, cwd=self.project_root)
        return result.returncode, f"Tests for module: {module_name}"

    def print_summary(self, results: List[Tuple[int, str]]) -> None:
        """Print test execution summary."""
        print("\n" + "="*70)
        print("[SUMMARY] TEST EXECUTION SUMMARY")
        print("="*70 + "\n")

        passed = sum(1 for code, _ in results if code == 0)
        failed = len(results) - passed

        for returncode, test_name in results:
            status = "[PASS]" if returncode == 0 else "[FAIL]"
            print(f"{status}: {test_name}")

        print(f"\n{'─'*70}")
        print(f"Total: {len(results)} | Passed: {passed} | Failed: {failed}")
        print(f"{'─'*70}\n")

        if failed == 0:
            print("[OK] All tests passed!")
        else:
            print(f"[WARN] {failed} test suite(s) failed")

        print(f"\n[INFO] Reports available in: {self.reports_dir}")

    def display_help(self) -> None:
        """Display help message."""
        help_text = """
╔════════════════════════════════════════════════════════════════════╗
║                   NoteTracker Test Runner                          ║
╚════════════════════════════════════════════════════════════════════╝

USAGE:
    python run_tests.py [COMMAND] [OPTIONS]

COMMANDS:
    all          Run all tests (unit + integration)
    unit         Run only unit tests
    integration  Run only integration tests
    coverage     Run all tests with coverage analysis
    smoke        Run quick sanity check tests
    specific     Run a specific test file
    module       Run tests for a specific module
    help         Display this help message

EXAMPLES:
    python run_tests.py all                    # Run everything
    python run_tests.py unit -q                # Run unit tests quietly
    python run_tests.py coverage               # Generate coverage report
    python run_tests.py specific unit/test_db.py
    python run_tests.py module note_ops

OPTIONS:
    -q, --quiet  Suppress verbose output
    -h, --help   Display this help message

REPORTS:
    HTML reports are generated in: ./test_reports/
    Coverage reports: ./test_reports/coverage_html/
"""
        print(help_text)


def main():
    """Main entry point for test runner."""
    runner = TestRunner()
    results = []

    # Parse command line arguments
    args = sys.argv[1:] if len(sys.argv) > 1 else ['all']
    command = args[0].lower() if args else 'all'
    verbose = '-q' not in args and '--quiet' not in args

    try:
        if command == 'all':
            results.append(runner.run_unit_tests(verbose))
            results.append(runner.run_integration_tests(verbose))
        elif command == 'unit':
            results.append(runner.run_unit_tests(verbose))
        elif command == 'integration':
            results.append(runner.run_integration_tests(verbose))
        elif command == 'coverage':
            results.append(runner.run_with_coverage(verbose))
        elif command == 'smoke':
            results.append(runner.run_smoke_tests())
        elif command == 'specific':
            if len(args) < 2:
                print("[ERROR] Error: Please specify test file")
                print("Usage: python run_tests.py specific <test_file>")
                return 1
            results.append(runner.run_specific_test(args[1], verbose))
        elif command == 'module':
            if len(args) < 2:
                print("[ERROR] Error: Please specify module name")
                print("Usage: python run_tests.py module <module_name>")
                return 1
            results.append(runner.run_module_tests(args[1]))
        elif command in ['help', '-h', '--help', '?']:
            runner.display_help()
            return 0
        else:
            print(f"[ERROR] Unknown command: {command}")
            print("Use 'python run_tests.py help' for available commands")
            return 1

        # Print summary
        runner.print_summary(results)

        # Return exit code based on results
        return 0 if all(code == 0 for code, _ in results) else 1

    except KeyboardInterrupt:
        print("\n\n⚠️  Test execution interrupted by user")
        return 130
    except Exception as e:
        print(f"\n❌ Error running tests: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())

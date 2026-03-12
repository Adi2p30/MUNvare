#!/usr/bin/env python3
"""
Test Runner for MUNvare
Runs all tests with coverage reporting and detailed output
"""
import subprocess
import sys
import os

def run_tests():
    """Run all tests with pytest"""

    # Change to testcases directory
    testcases_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(testcases_dir)

    print("=" * 80)
    print("MUNvare Test Suite")
    print("=" * 80)
    print()

    # Install test requirements
    print("Installing test dependencies...")
    subprocess.run([
        sys.executable, '-m', 'pip', 'install', '-q', '-r', 'test_requirements.txt'
    ])
    print()

    # Run tests with coverage
    print("Running tests...")
    print("-" * 80)

    cmd = [
        'pytest',
        '-v',  # Verbose output
        '--tb=short',  # Short traceback format
        '--cov=../backend',  # Coverage for backend
        '--cov-report=term-missing',  # Show missing lines
        '--cov-report=html:coverage_html',  # HTML report
        '-x',  # Stop on first failure (remove for CI)
        '.'
    ]

    result = subprocess.run(cmd)

    print()
    print("=" * 80)

    if result.returncode == 0:
        print("✓ All tests passed!")
        print()
        print("Coverage report generated in: coverage_html/index.html")
    else:
        print("✗ Some tests failed")
        print()
        print("Review the output above for details")

    print("=" * 80)

    return result.returncode

if __name__ == '__main__':
    exit_code = run_tests()
    sys.exit(exit_code)

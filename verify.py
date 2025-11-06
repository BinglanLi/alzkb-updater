#!/usr/bin/env python3
"""
Verification script to check AlzKB Updater installation
"""
import sys
import os

def check_python_version():
    """Check Python version"""
    version = sys.version_info
    if version.major >= 3 and version.minor >= 10:
        print("✓ Python version:", f"{version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print("✗ Python version too old. Need 3.10+, have:", f"{version.major}.{version.minor}.{version.micro}")
        return False

def check_dependencies():
    """Check if dependencies are installed"""
    required = ['pandas', 'requests', 'numpy']
    missing = []
    
    for package in required:
        try:
            __import__(package)
            print(f"✓ {package} installed")
        except ImportError:
            print(f"✗ {package} not installed")
            missing.append(package)
    
    return len(missing) == 0

def check_structure():
    """Check project structure"""
    required_dirs = [
        'alzkb',
        'alzkb/sources',
        'data',
        'data/raw',
        'data/processed'
    ]
    
    required_files = [
        'alzkb/__init__.py',
        'alzkb/config.py',
        'alzkb/integrator.py',
        'alzkb/sources/base.py',
        'alzkb/sources/uniprot.py',
        'alzkb/sources/drugcentral.py',
        'main.py',
        'requirements.txt',
        'README.md'
    ]
    
    all_good = True
    
    for directory in required_dirs:
        if os.path.isdir(directory):
            print(f"✓ Directory exists: {directory}")
        else:
            print(f"✗ Directory missing: {directory}")
            all_good = False
    
    for file in required_files:
        if os.path.isfile(file):
            print(f"✓ File exists: {file}")
        else:
            print(f"✗ File missing: {file}")
            all_good = False
    
    return all_good

def main():
    """Run all checks"""
    print("="*60)
    print("AlzKB Updater Installation Verification")
    print("="*60)
    
    print("\n1. Checking Python version...")
    python_ok = check_python_version()
    
    print("\n2. Checking dependencies...")
    deps_ok = check_dependencies()
    
    print("\n3. Checking project structure...")
    structure_ok = check_structure()
    
    print("\n" + "="*60)
    if python_ok and deps_ok and structure_ok:
        print("✓ All checks passed! Ready to use AlzKB Updater.")
        print("\nRun 'python demo.py' to test the application.")
        return 0
    else:
        print("✗ Some checks failed. Please fix the issues above.")
        if not deps_ok:
            print("\nTo install dependencies, run:")
            print("  pip install -r requirements.txt")
        return 1

if __name__ == "__main__":
    exit(main())

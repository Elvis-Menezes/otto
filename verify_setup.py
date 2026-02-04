#!/usr/bin/env python3
"""
Verification script for Otto Bot Creator with MongoDB.
Run this before starting the server to check your configuration.
"""

import os
import sys
from pathlib import Path

# Add color output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def check(condition: bool, success_msg: str, fail_msg: str, required: bool = True) -> bool:
    if condition:
        print(f"{GREEN}✅ {success_msg}{RESET}")
        return True
    else:
        symbol = "❌" if required else "⚠️ "
        color = RED if required else YELLOW
        print(f"{color}{symbol} {fail_msg}{RESET}")
        return not required


def main():
    print(f"{BLUE}{'=' * 60}")
    print("Otto Bot Creator - Setup Verification")
    print(f"{'=' * 60}{RESET}\n")
    
    all_checks_passed = True
    
    # Check 1: Python version
    print(f"{BLUE}1. Python Version{RESET}")
    python_version = sys.version_info
    is_valid = python_version.major == 3 and python_version.minor >= 12
    all_checks_passed &= check(
        is_valid,
        f"Python {python_version.major}.{python_version.minor}.{python_version.micro}",
        f"Python 3.12+ required, found {python_version.major}.{python_version.minor}",
        required=True
    )
    print()
    
    # Check 2: Virtual environment
    print(f"{BLUE}2. Virtual Environment{RESET}")
    in_venv = hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix)
    all_checks_passed &= check(
        in_venv,
        "Virtual environment is active",
        "Virtual environment not detected (run: source .venv/bin/activate)",
        required=False
    )
    print()
    
    # Check 3: Dependencies
    print(f"{BLUE}3. Required Packages{RESET}")
    
    packages = {
        "parlant": "Parlant SDK",
        "httpx": "HTTP client for REST API",
        "dotenv": "Environment variable loading",
        "pymongo": "MongoDB driver",
        "motor": "Async MongoDB driver",
        "openai": "OpenAI integration",
    }
    
    for package, description in packages.items():
        try:
            __import__(package)
            check(True, f"{description} ({package})", "", required=True)
        except ImportError:
            all_checks_passed &= check(
                False,
                "",
                f"{description} not installed (pip install {package})",
                required=True
            )
    print()
    
    # Check 4: .env file
    print(f"{BLUE}4. Environment Configuration{RESET}")
    env_exists = Path(".env").exists()
    all_checks_passed &= check(
        env_exists,
        ".env file exists",
        ".env file missing (run: cp env.example .env)",
        required=True
    )
    
    if env_exists:
        from dotenv import load_dotenv
        load_dotenv()
        
        # Check OpenAI key
        openai_key = os.getenv("OPENAI_API_KEY")
        has_openai = openai_key and openai_key.startswith("sk-")
        all_checks_passed &= check(
            has_openai,
            "OPENAI_API_KEY is set",
            "OPENAI_API_KEY missing or invalid in .env",
            required=True
        )
        
        # Check MongoDB URI
        mongodb_uri = os.getenv("MONGODB_URI")
        has_mongodb = mongodb_uri and (
            mongodb_uri.startswith("mongodb://") or 
            mongodb_uri.startswith("mongodb+srv://")
        )
        check(
            has_mongodb,
            f"MONGODB_URI configured (persistent storage enabled)",
            "MONGODB_URI not set (will use in-memory storage)",
            required=False
        )
        
        if has_mongodb:
            print(f"   {YELLOW}Testing MongoDB connection...{RESET}")
            try:
                from pymongo import MongoClient
                client = MongoClient(mongodb_uri, serverSelectionTimeoutMS=5000)
                client.admin.command('ping')
                client.close()
                print(f"   {GREEN}✅ MongoDB connection successful!{RESET}")
            except Exception as e:
                print(f"   {RED}❌ MongoDB connection failed: {str(e)}{RESET}")
                all_checks_passed = False
    print()
    
    # Check 5: Project files
    print(f"{BLUE}5. Project Files{RESET}")
    files_to_check = [
        ("server.py", "Main server file", True),
        ("mongo_config.py", "MongoDB configuration", True),
        ("requirements.txt", "Dependencies list", True),
        ("README.md", "Documentation", False),
    ]
    
    for filename, description, required in files_to_check:
        exists = Path(filename).exists()
        all_checks_passed &= check(
            exists,
            f"{description} ({filename})",
            f"{description} missing ({filename})",
            required=required
        )
    print()
    
    # Check 6: Ports
    print(f"{BLUE}6. Port Availability{RESET}")
    try:
        import socket
        
        for port in [8800, 8818]:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            
            if result != 0:
                check(True, f"Port {port} is available", "", required=False)
            else:
                print(f"   {YELLOW}⚠️  Port {port} is in use (may need to kill: lsof -i :{port}){RESET}")
    except Exception as e:
        print(f"   {YELLOW}⚠️  Could not check ports: {e}{RESET}")
    print()
    
    # Summary
    print(f"{BLUE}{'=' * 60}")
    print("Verification Summary")
    print(f"{'=' * 60}{RESET}\n")
    
    if all_checks_passed:
        print(f"{GREEN}✅ All required checks passed!{RESET}")
        print(f"{GREEN}You're ready to run: python server.py{RESET}\n")
        return 0
    else:
        print(f"{RED}❌ Some checks failed. Please fix the issues above.{RESET}\n")
        return 1


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{YELLOW}Verification cancelled.{RESET}")
        sys.exit(1)
    except Exception as e:
        print(f"\n{RED}Error during verification: {e}{RESET}")
        sys.exit(1)

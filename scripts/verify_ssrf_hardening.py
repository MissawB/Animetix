import sys
import os
from pathlib import Path

# Add project root to sys.path
sys.path.append(str(Path(__file__).resolve().parent.parent / "backend" / "core"))
sys.path.append(str(Path(__file__).resolve().parent.parent / "backend"))

from utils.security import is_safe_url

def test_url(url, allow_internal, expected):
    result = is_safe_url(url, allow_internal=allow_internal)
    status = "PASS" if result == expected else "FAIL"
    print(f"[{status}] URL: {url:30} | allow_internal: {str(allow_internal):5} | Expected: {str(expected):5} | Result: {str(result):5}")
    return result == expected

if __name__ == "__main__":
    print("--- Testing SSRF Hardening ---")
    tests = [
        # Public URLs
        ("http://google.com", False, True),
        ("https://github.com", True, True),
        
        # Whitelisted Internal Hostnames
        ("http://brain/generate", True, True),
        ("http://brain/generate", False, False),
        ("http://localhost:8000", True, True),
        ("http://127.0.0.1:5432", True, True),
        ("http://db:5432", True, True),
        
        # Non-whitelisted Internal/Private IPs (should be BLOCKED)
        ("http://192.168.1.1", True, False),
        ("http://10.0.0.1", True, False),
        ("http://169.254.169.254", True, False), # Cloud Metadata
        ("http://172.16.0.1", True, False),
        
        # Malicious Hostnames resolving to private IPs (if possible to test without real DNS)
        # Note: socket.getaddrinfo will be used.
    ]
    
    all_passed = True
    for url, allow, expected in tests:
        if not test_url(url, allow, expected):
            all_passed = False
            
    if all_passed:
        print("\n✅ All SSRF hardening tests PASSED.")
    else:
        print("\n❌ Some SSRF hardening tests FAILED.")
        sys.exit(1)

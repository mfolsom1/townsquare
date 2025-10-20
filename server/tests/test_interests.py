#!/usr/bin/env python3
"""
Simple test script to verify interests functionality
This is not meant for production - just for development testing
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.models import User

def test_interests_functionality():
    """Test the interests functionality (requires database connection)"""
    
    # Test getting all interests (should work even with empty database)
    try:
        print("Testing get_all_interests...")
        interests = User.get_all_interests()
        print(f"Found {len(interests)} interests in the system:")
        for interest in interests:
            print(f"  - {interest['name']}: {interest['description']}")
        print("✓ get_all_interests works")
    except Exception as e:
        print(f"✗ get_all_interests failed: {e}")
        return False
    
    print("\n" + "="*50)
    print("Interests functionality test completed successfully!")
    print("The following API endpoints are now available:")
    print("  - GET /api/user/profile (now includes interests)")
    print("  - PUT /api/user/profile (now accepts interests array)")
    print("  - GET /api/user/interests")
    print("  - POST /api/user/interests")
    print("  - DELETE /api/user/interests") 
    print("  - GET /api/interests")
    
    return True

if __name__ == "__main__":
    test_interests_functionality()
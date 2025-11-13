#!/usr/bin/env python3
"""
Test script for organization functionality
Run this after applying the database migration to test the new features
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'server'))

from app.models import Organization, User, Event

def test_organization_crud():
    """Test basic organization CRUD operations"""
    print("Testing Organization CRUD...")
    
    try:
        # Create organization
        org = Organization.create_organization("Tech Meetup", "A community for tech enthusiasts")
        print(f"✓ Created organization: {org.name} (ID: {org.org_id})")
        
        # Get organization by ID
        retrieved_org = Organization.get_organization_by_id(org.org_id)
        assert retrieved_org.name == org.name
        print(f"✓ Retrieved organization by ID: {retrieved_org.name}")
        
        # Get organization by name
        org_by_name = Organization.get_organization_by_name("Tech Meetup")
        assert org_by_name.org_id == org.org_id
        print(f"✓ Retrieved organization by name: {org_by_name.name}")
        
        # Update organization
        Organization.update_organization(org.org_id, description="Updated description for tech community")
        updated_org = Organization.get_organization_by_id(org.org_id)
        assert "Updated description" in updated_org.description
        print(f"✓ Updated organization description")
        
        # List all organizations
        all_orgs = Organization.get_all_organizations()
        assert len(all_orgs) >= 1
        print(f"✓ Listed all organizations: {len(all_orgs)} found")
        
        return org.org_id
        
    except Exception as e:
        print(f"✗ Organization CRUD test failed: {e}")
        return None

def test_user_organization_interactions(org_id, firebase_uid="test_user_123"):
    """Test user-organization interactions"""
    print("\nTesting User-Organization interactions...")
    
    try:
        # Test joining organization
        success = User.join_organization(firebase_uid, org_id)
        if success:
            print(f"✓ User joined organization")
        else:
            print(f"- User already a member of organization")
        
        # Test checking membership
        is_member = User.is_organization_member(firebase_uid, org_id)
        assert is_member
        print(f"✓ Confirmed user membership")
        
        # Test getting user organizations
        user_orgs = User.get_user_organizations(firebase_uid)
        org_found = any(org['org_id'] == org_id for org in user_orgs)
        assert org_found
        print(f"✓ Retrieved user organizations: {len(user_orgs)} found")
        
        # Test following organization
        success = User.follow_organization(firebase_uid, org_id)
        if success:
            print(f"✓ User followed organization")
        else:
            print(f"- User already following organization")
        
        # Test checking following status
        is_following = User.is_following_organization(firebase_uid, org_id)
        assert is_following
        print(f"✓ Confirmed user is following organization")
        
        # Test getting followed organizations
        followed_orgs = User.get_followed_organizations(firebase_uid)
        org_found = any(org['org_id'] == org_id for org in followed_orgs)
        assert org_found
        print(f"✓ Retrieved followed organizations: {len(followed_orgs)} found")
        
        # Test unfollowing
        success = User.unfollow_organization(firebase_uid, org_id)
        assert success
        print(f"✓ User unfollowed organization")
        
        # Test leaving organization
        success = User.leave_organization(firebase_uid, org_id)
        assert success
        print(f"✓ User left organization")
        
    except Exception as e:
        print(f"✗ User-Organization interaction test failed: {e}")

def test_organization_events(org_id):
    """Test organization events functionality"""
    print("\nTesting Organization Events...")
    
    try:
        # Get events for organization (should be empty initially)
        org_events = Event.get_events_by_organization(org_id)
        print(f"✓ Retrieved organization events: {len(org_events)} found")
        
    except Exception as e:
        print(f"✗ Organization events test failed: {e}")

def cleanup_test_data():
    """Clean up test data (optional)"""
    print("\nCleaning up test data...")
    try:
        # Note: In a real environment, you might want to clean up test data
        # For now, we'll leave the test organization for further testing
        print("✓ Test data cleanup completed (test org left for further testing)")
    except Exception as e:
        print(f"✗ Cleanup failed: {e}")

def main():
    print("=== Organization Functionality Test ===\n")
    
    # Test basic CRUD operations
    org_id = test_organization_crud()
    
    if org_id:
        # Test user interactions
        test_user_organization_interactions(org_id)
        
        # Test events functionality
        test_organization_events(org_id)
        
        # Cleanup (optional)
        cleanup_test_data()
        
        print(f"\n=== All tests completed! ===")
        print(f"Test organization ID: {org_id}")
        print("You can now test the API endpoints with this organization.")
    else:
        print("\n=== Tests failed - could not create organization ===")

if __name__ == "__main__":
    main()
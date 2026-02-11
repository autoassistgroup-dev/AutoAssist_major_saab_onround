"""
Development Seed Script for Technicians

This script creates sample technicians for development/testing purposes.
Run this script ONLY in development environments.

Usage:
    python seed_technicians.py

WARNING: This script is for DEV-ONLY use. Do not run in production.
"""

import os
import sys
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
from dotenv import load_dotenv
load_dotenv()


def seed_technicians():
    """Insert sample technicians into the database."""
    
    from database import get_db
    
    print("\n" + "="*60)
    print("🔧 TECHNICIAN SEED SCRIPT")
    print("="*60)
    
    db = get_db()
    
    # Check existing technicians
    existing_count = db.technicians.count_documents({})
    active_count = db.technicians.count_documents({"is_active": True})
    
    print(f"\n📊 Current State:")
    print(f"   Total technicians: {existing_count}")
    print(f"   Active technicians: {active_count}")
    
    if active_count > 0:
        print(f"\n✅ Found {active_count} active technician(s). Seed not required.")
        print("   Use --force flag to add additional sample technicians.")
        
        # Show existing technicians
        print("\n📋 Existing Technicians:")
        for tech in db.technicians.find({"is_active": True}):
            print(f"   • {tech.get('name')} ({tech.get('role', 'Technician')}) - {tech.get('email', 'No email')}")
        
        if len(sys.argv) > 1 and sys.argv[1] == '--force':
            print("\n⚠️  Force flag detected. Adding additional technicians...")
        else:
            return
    
    # Sample technicians data
    sample_technicians = [
        {
            "name": "John Mitchell",
            "email": "john.mitchell@autoassistgroup.com",
            "role": "Senior Technician",
            "employee_id": "TECH001",
            "is_active": True,
            "created_at": datetime.now()
        },
        {
            "name": "Sarah Connor",
            "email": "sarah.connor@autoassistgroup.com",
            "role": "Lead Technician",
            "employee_id": "TECH002",
            "is_active": True,
            "created_at": datetime.now()
        },
        {
            "name": "Mike Rodriguez",
            "email": "mike.rodriguez@autoassistgroup.com",
            "role": "Technician",
            "employee_id": "TECH003",
            "is_active": True,
            "created_at": datetime.now()
        },
        {
            "name": "Emily Chen",
            "email": "emily.chen@autoassistgroup.com",
            "role": "Specialist",
            "employee_id": "TECH004",
            "is_active": True,
            "created_at": datetime.now()
        },
        {
            "name": "David Thompson",
            "email": "david.thompson@autoassistgroup.com",
            "role": "Technician",
            "employee_id": "TECH005",
            "is_active": True,
            "created_at": datetime.now()
        }
    ]
    
    print("\n🚀 Inserting sample technicians...")
    
    inserted_count = 0
    for tech in sample_technicians:
        # Check if technician with same email already exists
        existing = db.technicians.find_one({"email": tech["email"]})
        if existing:
            print(f"   ⏭️  Skipping {tech['name']} (email already exists)")
            continue
        
        result = db.technicians.insert_one(tech)
        if result.inserted_id:
            print(f"   ✅ Created: {tech['name']} ({tech['role']})")
            inserted_count += 1
        else:
            print(f"   ❌ Failed to create: {tech['name']}")
    
    print(f"\n📊 Summary:")
    print(f"   Technicians inserted: {inserted_count}")
    print(f"   Total active technicians: {db.technicians.count_documents({'is_active': True})}")
    
    print("\n" + "="*60)
    print("✅ SEED COMPLETE")
    print("="*60)
    print("\nNext steps:")
    print("   1. Refresh the ticket detail page")
    print("   2. The technician dropdown should now be populated")
    print("   3. You can also manage technicians at /admin/technicians")
    print("")


if __name__ == "__main__":
    seed_technicians()

#!/usr/bin/env python3
"""
Script to remove specific MC numbers from the database.
"""
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from api.db import SessionLocal
from api.models import Call, Load

def remove_mc_numbers(mc_list):
    """Remove calls and loads for specific MC numbers."""
    db = SessionLocal()
    
    try:
        total_calls_deleted = 0
        total_loads_deleted = 0
        
        for mc in mc_list:
            # Remove calls with this carrier_mc
            calls_deleted = db.query(Call).filter(Call.carrier_mc == mc).delete()
            print(f"Deleted {calls_deleted} calls for carrier MC {mc}")
            total_calls_deleted += calls_deleted
            
            # Remove loads with this broker_mc
            loads_deleted = db.query(Load).filter(Load.broker_mc == mc).delete()
            print(f"Deleted {loads_deleted} loads for broker MC {mc}")
            total_loads_deleted += loads_deleted
        
        db.commit()
        print(f"Total calls deleted: {total_calls_deleted}")
        print(f"Total loads deleted: {total_loads_deleted}")
        return True
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    # Add MC numbers you want to remove here
    mc_numbers_to_remove = [
        "123456",    # Test MC numbers from FMCSA stub
        "13456"
    ]
    
    print("Removing MC numbers from database...")
    success = remove_mc_numbers(mc_numbers_to_remove)
    
    if success:
        print("✅ Cleanup completed successfully!")
    else:
        print("❌ Cleanup failed!")
        sys.exit(1)
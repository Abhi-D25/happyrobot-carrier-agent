import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from api.db import SessionLocal, engine
from api.models import Load, Base

def generate_current_loads():
    
    # Start from tomorrow
    base_date = datetime.now() + timedelta(days=1)
    
    # Your existing loads + some additional ones with current dates
    loads_data = [
        {
            "load_id": "LOAD-001",
            "origin_city": "Los Angeles",
            "origin_state": "CA",
            "destination_city": "Phoenix",
            "destination_state": "AZ",
            "pickup_date": (base_date + timedelta(days=0)).isoformat() + "Z",
            "delivery_date": (base_date + timedelta(days=1)).isoformat() + "Z",
            "equipment_type": "Dry Van",
            "weight": 45000,
            "miles": 370,
            "rate_per_mile": 2.15,
            "total_rate": 795.50,
            "commodity": "Electronics",
            "special_requirements": "Temperature controlled",
            "broker_name": "ABC Logistics",
            "broker_mc": "123456",
            "is_active": True
        },
        {
            "load_id": "LOAD-002",
            "origin_city": "Chicago",
            "origin_state": "IL",
            "destination_city": "Atlanta",
            "destination_state": "GA",
            "pickup_date": (base_date + timedelta(days=1)).isoformat() + "Z",
            "delivery_date": (base_date + timedelta(days=2)).isoformat() + "Z",
            "equipment_type": "Refrigerated",
            "weight": 42000,
            "miles": 720,
            "rate_per_mile": 2.45,
            "total_rate": 1764.00,
            "commodity": "Food Products",
            "special_requirements": "Keep frozen",
            "broker_name": "XYZ Freight",
            "broker_mc": "789012",
            "is_active": True
        },
        {
            "load_id": "LOAD-003",
            "origin_city": "Houston",
            "origin_state": "TX",
            "destination_city": "Denver",
            "destination_state": "CO",
            "pickup_date": (base_date + timedelta(days=2)).isoformat() + "Z",
            "delivery_date": (base_date + timedelta(days=3)).isoformat() + "Z",
            "equipment_type": "Flatbed",
            "weight": 48000,
            "miles": 920,
            "rate_per_mile": 2.80,
            "total_rate": 2576.00,
            "commodity": "Construction Materials",
            "special_requirements": "Tarp required",
            "broker_name": "Southwest Transport",
            "broker_mc": "345678",
            "is_active": True
        },
        {
            "load_id": "LOAD-004",
            "origin_city": "Miami",
            "origin_state": "FL",
            "destination_city": "New York",
            "destination_state": "NY",
            "pickup_date": (base_date + timedelta(days=3)).isoformat() + "Z",
            "delivery_date": (base_date + timedelta(days=5)).isoformat() + "Z",
            "equipment_type": "Dry Van",
            "weight": 44000,
            "miles": 1280,
            "rate_per_mile": 1.95,
            "total_rate": 2496.00,
            "commodity": "Retail Goods",
            "special_requirements": "Appointment required",
            "broker_name": "East Coast Logistics",
            "broker_mc": "901234",
            "is_active": True
        },
        {
            "load_id": "LOAD-005",
            "origin_city": "Seattle",
            "origin_state": "WA",
            "destination_city": "Portland",
            "destination_state": "OR",
            "pickup_date": (base_date + timedelta(days=4)).isoformat() + "Z",
            "delivery_date": (base_date + timedelta(days=4, hours=6)).isoformat() + "Z",
            "equipment_type": "Dry Van",
            "weight": 38000,
            "miles": 175,
            "rate_per_mile": 2.25,
            "total_rate": 393.75,
            "commodity": "Consumer Electronics",
            "special_requirements": "Liftgate required",
            "broker_name": "Pacific Freight",
            "broker_mc": "567890",
            "is_active": True
        },
        # Additional loads for better coverage
        {
            "load_id": "LOAD-006",
            "origin_city": "Dallas",
            "origin_state": "TX",
            "destination_city": "Memphis",
            "destination_state": "TN",
            "pickup_date": (base_date + timedelta(days=5)).isoformat() + "Z",
            "delivery_date": (base_date + timedelta(days=6)).isoformat() + "Z",
            "equipment_type": "Dry Van",
            "weight": 41000,
            "miles": 470,
            "rate_per_mile": 2.10,
            "total_rate": 987.00,
            "commodity": "Auto Parts",
            "special_requirements": "No drop and hook",
            "broker_name": "Central Freight",
            "broker_mc": "111222",
            "is_active": True
        },
        {
            "load_id": "LOAD-007",
            "origin_city": "Phoenix",
            "origin_state": "AZ",
            "destination_city": "Las Vegas",
            "destination_state": "NV",
            "pickup_date": (base_date + timedelta(days=6)).isoformat() + "Z",
            "delivery_date": (base_date + timedelta(days=7)).isoformat() + "Z",
            "equipment_type": "Flatbed",
            "weight": 46000,
            "miles": 295,
            "rate_per_mile": 2.60,
            "total_rate": 767.00,
            "commodity": "Steel Beams",
            "special_requirements": "Tarps required",
            "broker_name": "Desert Transport",
            "broker_mc": "333444",
            "is_active": True
        },
        {
            "load_id": "LOAD-008",
            "origin_city": "Atlanta",
            "origin_state": "GA",
            "destination_city": "Jacksonville",
            "destination_state": "FL",
            "pickup_date": (base_date + timedelta(days=7)).isoformat() + "Z",
            "delivery_date": (base_date + timedelta(days=8)).isoformat() + "Z",
            "equipment_type": "Refrigerated",
            "weight": 39000,
            "miles": 350,
            "rate_per_mile": 2.75,
            "total_rate": 962.50,
            "commodity": "Fresh Produce",
            "special_requirements": "Temperature 35-38°F",
            "broker_name": "Southern Logistics",
            "broker_mc": "555666",
            "is_active": True
        },
        {
            "load_id": "LOAD-009",
            "origin_city": "San Francisco",
            "origin_state": "CA",
            "destination_city": "Sacramento",
            "destination_state": "CA",
            "pickup_date": (base_date + timedelta(days=8)).isoformat() + "Z",
            "delivery_date": (base_date + timedelta(days=8, hours=4)).isoformat() + "Z",
            "equipment_type": "Dry Van",
            "weight": 35000,
            "miles": 90,
            "rate_per_mile": 2.80,
            "total_rate": 252.00,
            "commodity": "Tech Equipment",
            "special_requirements": "White glove service",
            "broker_name": "Bay Area Logistics",
            "broker_mc": "777888",
            "is_active": True
        },
        {
            "load_id": "LOAD-010",
            "origin_city": "Denver",
            "origin_state": "CO",
            "destination_city": "Salt Lake City",
            "destination_state": "UT",
            "pickup_date": (base_date + timedelta(days=9)).isoformat() + "Z",
            "delivery_date": (base_date + timedelta(days=10)).isoformat() + "Z",
            "equipment_type": "Dry Van",
            "weight": 43000,
            "miles": 525,
            "rate_per_mile": 2.05,
            "total_rate": 1076.25,
            "commodity": "Sporting Goods",
            "special_requirements": "Appointment required",
            "broker_name": "Mountain Freight",
            "broker_mc": "999000",
            "is_active": True
        }
    ]
    
    return loads_data

def seed_loads():
    """Load sample data with current dates into the database."""
    
    print("🚛 Starting load seeding with current dates...")
    
    # Create tables if they don't exist
    print("📋 Creating database tables...")
    Base.metadata.create_all(bind=engine)
    
    # Generate loads with current dates
    print("📅 Generating loads with current dates...")
    loads_data = generate_current_loads()
    
    db = SessionLocal()
    
    try:
        # Clear existing loads
        print("🗑️  Clearing existing loads...")
        deleted_count = db.query(Load).delete()
        print(f"   Deleted {deleted_count} existing loads")
        
        # Insert new loads
        print("📦 Inserting new loads...")
        for load_data in loads_data:
            # Convert date strings to datetime objects
            load_data['pickup_date'] = datetime.fromisoformat(load_data['pickup_date'].replace('Z', '+00:00'))
            load_data['delivery_date'] = datetime.fromisoformat(load_data['delivery_date'].replace('Z', '+00:00'))
            
            load = Load(**load_data)
            db.add(load)
        
        db.commit()
        
        # Verify the loads were inserted
        total_loads = db.query(Load).count()
        print(f"✅ Successfully seeded {total_loads} loads!")
        
        # Show some statistics
        equipment_counts = {}
        for load in db.query(Load).all():
            equipment_counts[load.equipment_type] = equipment_counts.get(load.equipment_type, 0) + 1
        
        print("\n📊 Load distribution:")
        for equipment, count in sorted(equipment_counts.items()):
            print(f"   {equipment}: {count} loads")
        
        # Show sample loads
        print(f"\n🗺️  Sample loads:")
        for load in db.query(Load).limit(3).all():
            print(f"   {load.load_id}: {load.origin_city}, {load.origin_state} → {load.destination_city}, {load.destination_state}")
            print(f"      {load.equipment_type}, ${load.total_rate}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        db.rollback()
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("🚀 Enhanced Seeding for Current Setup")
    print("=" * 50)
    
    # Check database URL
    db_url = os.getenv("DATABASE_URL", "sqlite:///./carrier_agent.db")
    print(f"📍 Database URL: {db_url}")
    
    # Run seeding
    success = seed_loads()
    
    if success:
        print("\n🎉 Database successfully seeded!")
        print("\n💡 Your HappyRobot agent can now search for:")
        print("   • 'Dry van loads from California'")
        print("   • 'Refrigerated loads to Florida'") 
        print("   • 'Loads from Los Angeles to Phoenix'")
        print("   • 'Flatbed loads from Texas'")
    else:
        print("\n❌ Load seeding failed!")
        sys.exit(1)
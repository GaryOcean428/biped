#!/usr/bin/env python3
"""
Create notifications table for Biped Platform
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.main import app
from src.models.user import db
from src.routes.notifications import Notification

def create_notifications_table():
    """Create the notifications table"""
    with app.app_context():
        try:
            # Create the notifications table
            db.create_all()
            print("✅ Notifications table created successfully!")
            
            # Verify table creation
            inspector = db.inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'notifications' in tables:
                print("✅ Notifications table verified in database")
                
                # Show table structure
                columns = inspector.get_columns('notifications')
                print("\n📋 Notifications table structure:")
                for column in columns:
                    print(f"  - {column['name']}: {column['type']}")
            else:
                print("❌ Notifications table not found in database")
                
        except Exception as e:
            print(f"❌ Error creating notifications table: {e}")

if __name__ == "__main__":
    create_notifications_table()


#!/usr/bin/env python3
"""
Simple database creation script
"""
import sqlite3
import os

def create_database():
    """Create database with all required tables"""
    db_path = 'instance/database.db'
    
    # Ensure instance directory exists
    os.makedirs('instance', exist_ok=True)
    
    # Connect to database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create user table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            first_name VARCHAR(80) NOT NULL,
            last_name VARCHAR(80) NOT NULL,
            phone VARCHAR(20),
            user_type VARCHAR(20) NOT NULL DEFAULT 'customer',
            is_verified BOOLEAN DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            street_address TEXT,
            city VARCHAR(100),
            state VARCHAR(50),
            postcode VARCHAR(10),
            profile_image VARCHAR(255),
            bio TEXT,
            total_spent DECIMAL(10,2) DEFAULT 0.00,
            hourly_rate DECIMAL(8,2),
            total_earnings DECIMAL(10,2) DEFAULT 0.00
        )
    ''')
    
    # Create service_category table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS service_category (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) UNIQUE NOT NULL,
            description TEXT,
            icon VARCHAR(10),
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insert service categories
    categories = [
        ('Plumbing', 'Water, drainage, and pipe services', '🔧'),
        ('Electrical', 'Electrical installations and repairs', '⚡'),
        ('Carpentry', 'Wood work and furniture', '🔨'),
        ('Painting', 'Interior and exterior painting', '🎨'),
        ('Cleaning', 'Home and office cleaning services', '🧽'),
        ('Gardening', 'Landscaping and garden maintenance', '🌱'),
        ('Handyman', 'General repairs and maintenance', '🛠️'),
        ('Roofing', 'Roof repairs and installations', '🏠')
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO service_category (name, description, icon)
        VALUES (?, ?, ?)
    ''', categories)
    
    # Create other tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS service (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            typical_price_min DECIMAL(8,2),
            typical_price_max DECIMAL(8,2),
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES service_category (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS job (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            service_id INTEGER NOT NULL,
            title VARCHAR(200) NOT NULL,
            description TEXT NOT NULL,
            postcode VARCHAR(10) NOT NULL,
            budget_min DECIMAL(10,2),
            budget_max DECIMAL(10,2),
            status VARCHAR(20) DEFAULT 'open',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (customer_id) REFERENCES user (id),
            FOREIGN KEY (service_id) REFERENCES service (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS quote (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            provider_id INTEGER NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            description TEXT,
            status VARCHAR(20) DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES job (id),
            FOREIGN KEY (provider_id) REFERENCES user (id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS review (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            reviewer_id INTEGER NOT NULL,
            reviewed_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
            comment TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES job (id),
            FOREIGN KEY (reviewer_id) REFERENCES user (id),
            FOREIGN KEY (reviewed_id) REFERENCES user (id)
        )
    ''')
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print("Database created successfully!")
    print("Tables created:")
    
    # Verify tables
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    for table in tables:
        print(f"  - {table[0]}")
    conn.close()

if __name__ == "__main__":
    create_database()


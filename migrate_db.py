#!/usr/bin/env python3
"""
Database migration script to add new admin functionality columns
"""

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from src.models.user import db
from src.main import app
import sqlite3

def migrate_database():
    """Migrate the existing database to add new admin columns"""
    
    with app.app_context():
        db_path = os.path.join(os.path.dirname(__file__), 'src', 'database', 'app.db')
        
        print("=== Database Migration ===")
        print(f"Database path: {db_path}")
        print()
        
        # Connect to database directly
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Check if columns exist
            cursor.execute("PRAGMA table_info(user)")
            columns = [column[1] for column in cursor.fetchall()]
            
            print("Existing user table columns:")
            for col in columns:
                print(f"  - {col}")
            print()
            
            # Add missing columns to user table
            missing_columns = []
            
            if 'is_blocked' not in columns:
                missing_columns.append('is_blocked')
                cursor.execute("ALTER TABLE user ADD COLUMN is_blocked BOOLEAN DEFAULT 0")
                print("✅ Added is_blocked column to user table")
                
            if 'blocked_at' not in columns:
                missing_columns.append('blocked_at')
                cursor.execute("ALTER TABLE user ADD COLUMN blocked_at DATETIME")
                print("✅ Added blocked_at column to user table")
                
            if 'blocked_by' not in columns:
                missing_columns.append('blocked_by')
                cursor.execute("ALTER TABLE user ADD COLUMN blocked_by INTEGER")
                print("✅ Added blocked_by column to user table")
                
            if 'blocked_reason' not in columns:
                missing_columns.append('blocked_reason')
                cursor.execute("ALTER TABLE user ADD COLUMN blocked_reason TEXT")
                print("✅ Added blocked_reason column to user table")
            
            # Check if admin table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='admin'")
            admin_table_exists = cursor.fetchone() is not None
            
            if not admin_table_exists:
                # Create admin table
                cursor.execute("""
                    CREATE TABLE admin (
                        id INTEGER PRIMARY KEY,
                        username VARCHAR(80) UNIQUE NOT NULL,
                        email VARCHAR(120) UNIQUE NOT NULL,
                        password_hash VARCHAR(255) NOT NULL,
                        first_name VARCHAR(50),
                        last_name VARCHAR(50),
                        role VARCHAR(50) DEFAULT 'admin',
                        is_active BOOLEAN DEFAULT 1,
                        last_login DATETIME,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                print("✅ Created admin table")
            else:
                print("ℹ️  Admin table already exists")
            
            # Check if admin_action table exists
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='admin_action'")
            admin_action_table_exists = cursor.fetchone() is not None
            
            if not admin_action_table_exists:
                # Create admin_action table
                cursor.execute("""
                    CREATE TABLE admin_action (
                        id INTEGER PRIMARY KEY,
                        admin_id INTEGER NOT NULL,
                        action_type VARCHAR(50) NOT NULL,
                        target_user_id INTEGER,
                        action_details TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (admin_id) REFERENCES admin(id),
                        FOREIGN KEY (target_user_id) REFERENCES user(id)
                    )
                """)
                print("✅ Created admin_action table")
            else:
                print("ℹ️  Admin_action table already exists")
            
            # Commit changes
            conn.commit()
            print()
            
            if missing_columns:
                print(f"✅ Successfully added {len(missing_columns)} missing columns to user table")
            else:
                print("ℹ️  All user table columns already exist")
                
            print("✅ Database migration completed successfully!")
            
        except Exception as e:
            print(f"❌ Migration failed: {str(e)}")
            conn.rollback()
            
        finally:
            conn.close()
        
        print()
        print("You can now run the admin functionality tests.")

if __name__ == "__main__":
    migrate_database()
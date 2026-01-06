#!/usr/bin/env python
"""
Database initialization script for the consultancy booking system.
This script sets up the SQLite database with the required tables.
"""

import sqlite3
import os

# Database file path
DB_FILE = 'consultancy.db'

def init_database():
    """Initialize the SQLite database with required tables."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Create Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            phone TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create Services table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS services (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description TEXT NOT NULL,
            price INTEGER NOT NULL,
            duration INTEGER NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create TimeSlots table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS time_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date DATE NOT NULL,
            start_time TIME NOT NULL,
            end_time TIME NOT NULL,
            service_id INTEGER NOT NULL,
            is_booked BOOLEAN DEFAULT 0,
            FOREIGN KEY (service_id) REFERENCES services (id)
        )
    ''')
    
    # Create Bookings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS bookings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            service_id INTEGER NOT NULL,
            slot_id INTEGER NOT NULL,
            status TEXT DEFAULT 'PENDING',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (service_id) REFERENCES services (id),
            FOREIGN KEY (slot_id) REFERENCES time_slots (id)
        )
    ''')
    
    # Create Payments table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            booking_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            status TEXT DEFAULT 'PENDING',
            transaction_id TEXT,
            provider TEXT DEFAULT 'PayU',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (booking_id) REFERENCES bookings (id)
        )
    ''')
    
    # Insert sample services
    sample_services = [
        ("Business Strategy Consulting", "Expert guidance on business growth, market expansion, and strategic planning.", 5000, 60),
        ("Technology Implementation", "End-to-end technology solutions and digital transformation strategies.", 8000, 90),
        ("Marketing & Branding", "Comprehensive marketing strategies and brand development solutions.", 2000, 45),
        ("Website Audit Trial", "Basic website performance and SEO audit for new clients.", 1000, 30),
        ("Social Media Setup", "Complete social media profile setup and basic strategy guide.", 3000, 45),
        ("Content Marketing Plan", "Comprehensive content marketing strategy and implementation guide.", 4900, 60),
        ("E-commerce Optimization", "Complete optimization of your e-commerce platform for better conversions.", 4900, 90),
        ("Data Analytics Setup", "Professional setup of analytics tools and custom reporting dashboard.", 3000, 60)
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO services (name, description, price, duration)
        VALUES (?, ?, ?, ?)
    ''', sample_services)
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print(f"Database '{DB_FILE}' initialized successfully!")

if __name__ == '__main__':
    init_database()

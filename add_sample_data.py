#!/usr/bin/env python
"""
Script to add sample time slots to the database.
"""

import sqlite3
from datetime import datetime, timedelta

# Database file path
DB_FILE = 'consultancy.db'

def add_sample_time_slots():
    """Add sample time slots to the database."""
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    
    # Sample time slots for the next week
    sample_slots = [
        # Service 1 (Business Strategy Consulting)
        ("2023-12-15", "09:00", "10:00", 1, 0),
        ("2023-12-15", "11:00", "12:00", 1, 0),
        ("2023-12-15", "14:00", "15:00", 1, 1),  # Booked
        ("2023-12-16", "10:00", "11:00", 1, 0),
        ("2023-12-16", "13:00", "14:00", 1, 0),
        
        # Service 2 (Technology Implementation)
        ("2023-12-16", "10:00", "11:30", 2, 0),
        ("2023-12-16", "13:00", "14:30", 2, 0),
        ("2023-12-17", "11:00", "12:30", 2, 0),
        ("2023-12-17", "15:00", "16:30", 2, 0),
        
        # Service 3 (Marketing & Branding)
        ("2023-12-17", "09:00", "09:45", 3, 0),
        ("2023-12-17", "11:00", "11:45", 3, 0),
        ("2023-12-18", "10:00", "10:45", 3, 0),
        ("2023-12-18", "14:00", "14:45", 3, 0),
        
        # Service 4 (Website Audit Trial - ₹1000)
        ("2023-12-19", "09:00", "09:30", 4, 0),
        ("2023-12-19", "10:00", "10:30", 4, 0),
        ("2023-12-20", "11:00", "11:30", 4, 0),
        
        # Service 5 (Social Media Setup - ₹3000)
        ("2023-12-19", "14:00", "14:45", 5, 0),
        ("2023-12-20", "10:00", "10:45", 5, 0),
        ("2023-12-20", "15:00", "15:45", 5, 0),
        
        # Service 6 (Content Marketing Plan - ₹4000)
        ("2023-12-20", "09:00", "10:00", 6, 0),
        ("2023-12-21", "11:00", "12:00", 6, 0),
        ("2023-12-21", "14:00", "15:00", 6, 0),
        
        # Service 7 (E-commerce Optimization - ₹4900)
        ("2023-12-21", "10:00", "11:30", 7, 0),
        ("2023-12-22", "13:00", "14:30", 7, 0),
        ("2023-12-22", "15:00", "16:30", 7, 0),
        
        # Service 8 (Data Analytics Setup - ₹3000)
        ("2023-12-22", "09:00", "10:00", 8, 0),
        ("2023-12-22", "11:00", "12:00", 8, 0),
    ]
    
    cursor.executemany('''
        INSERT OR IGNORE INTO time_slots (date, start_time, end_time, service_id, is_booked)
        VALUES (?, ?, ?, ?, ?)
    ''', sample_slots)
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print("Sample time slots added successfully!")

if __name__ == '__main__':
    add_sample_time_slots()

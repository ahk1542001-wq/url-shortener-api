import os
import sys
import argparse
import secrets

# Add the parent directory to sys.path to import src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src import database, config

def add_user(username: str, passcode: str = None, bio: str = None):
    db_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')), config.DB_NAME)
    
    if not passcode:
        passcode = secrets.token_hex(8)
        
    try:
        with database.get_db(db_path) as conn:
            if database.USE_POSTGRES:
                cur = conn.cursor()
                cur.execute(
                    "INSERT INTO users (username, passcode, bio) VALUES (%s, %s, %s) RETURNING id",
                    (username, passcode, bio)
                )
                user_id = cur.fetchone()[0]
            else:
                cursor = conn.execute(
                    "INSERT INTO users (username, passcode, bio) VALUES (?, ?, ?)",
                    (username, passcode, bio)
                )
                user_id = cursor.lastrowid
                
        print(f"✅ User '{username}' created successfully!")
        print(f"ID: {user_id}")
        print(f"Passcode: {passcode}")
        if bio:
            print(f"Bio: {bio}")
            
    except Exception as e:
        print(f"❌ Error creating user: {e}")
        if "UNIQUE constraint failed" in str(e) or "duplicate key" in str(e):
            print("This username is already taken.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add a new user to the Swoosh URL Shortener")
    parser.add_argument("username", help="The username for the new user")
    parser.add_argument("--passcode", help="Optional: A specific passcode (generates a random one if omitted)")
    parser.add_argument("--bio", help="Optional: A short bio for the Link Tree")
    
    args = parser.parse_args()
    add_user(args.username, args.passcode, args.bio)

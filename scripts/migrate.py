import os
import sys
import secrets

# Add the parent directory to sys.path to import src
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src import database, config

def migrate():
    # Force sqlite path if running locally and no Postgres
    db_path = os.path.join(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')), config.DB_NAME)
    print(f"Connecting to DB... (Postgres: {database.USE_POSTGRES})")
    
    with database.get_db(db_path) as conn:
        print("Creating users table if it doesn't exist...")
        if database.USE_POSTGRES:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    passcode TEXT UNIQUE NOT NULL,
                    bio TEXT,
                    tree_views INTEGER DEFAULT 0,
                    social_links TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
        else:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT UNIQUE NOT NULL,
                    passcode TEXT UNIQUE NOT NULL,
                    bio TEXT,
                    tree_views INTEGER DEFAULT 0,
                    social_links TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
        print("Checking if admin user exists...")
        if database.USE_POSTGRES:
            cur.execute("SELECT id FROM users WHERE username = 'admin'")
            admin_user = cur.fetchone()
        else:
            admin_user = conn.execute("SELECT id FROM users WHERE username = 'admin'").fetchone()
            
        if not admin_user:
            # Get existing password from config for the admin user
            # If not using ACCESS_PASSWORD, we'll generate a random one and print it
            passcode = config.ACCESS_PASSWORD or secrets.token_hex(8)
            print(f"Creating admin user with passcode: {passcode}")
            
            if database.USE_POSTGRES:
                cur.execute(
                    "INSERT INTO users (username, passcode, bio) VALUES (%s, %s, %s) RETURNING id",
                    ('admin', passcode, 'Digital Creator')
                )
                admin_id = cur.fetchone()[0]
            else:
                cursor = conn.execute(
                    "INSERT INTO users (username, passcode, bio) VALUES (?, ?, ?)",
                    ('admin', passcode, 'Digital Creator')
                )
                admin_id = cursor.lastrowid
        else:
            admin_id = admin_user[0]
            print(f"Admin user found with ID: {admin_id}")
            
    # For sqlite/postgres alter table, we should do it cautiously
    columns = [
        ("user_id", "INTEGER"),
        ("title", "TEXT"),
        ("show_on_tree", "BOOLEAN DEFAULT FALSE" if database.USE_POSTGRES else "BOOLEAN DEFAULT 0")
    ]
    
    for col_name, col_type in columns:
        try:
            with database.get_db(db_path) as conn:
                if database.USE_POSTGRES:
                    cur = conn.cursor()
                    cur.execute(f"ALTER TABLE urls ADD COLUMN {col_name} {col_type}")
                else:
                    conn.execute(f"ALTER TABLE urls ADD COLUMN {col_name} {col_type}")
            print(f"Added column {col_name}")
        except Exception as e:
            print(f"Column {col_name} likely already exists (or error): {e}")
            
    # Reopen to update existing URLs
    with database.get_db(db_path) as conn:
        print(f"Assigning existing URLs to admin user (ID: {admin_id})...")
        if database.USE_POSTGRES:
            cur = conn.cursor()
            cur.execute("UPDATE urls SET user_id = %s WHERE user_id IS NULL", (admin_id,))
        else:
            conn.execute("UPDATE urls SET user_id = ? WHERE user_id IS NULL", (admin_id,))
            
    print("Migration complete!")

if __name__ == "__main__":
    migrate()

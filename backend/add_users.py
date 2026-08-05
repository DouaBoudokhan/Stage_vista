"""Update existing doua user to use doua@stockit.local"""
from app.database import engine
from sqlalchemy import text
from app.utils.security import get_password_hash

print("Updating doua user email and password...")

with engine.connect() as conn:
    # Update the existing doua user
    hashed_doua_password = get_password_hash("0000")
    conn.execute(text("""
        UPDATE users 
        SET email = 'doua@stockit.local',
            password_hash = :password_hash,
            name = 'Doua User',
            role = 'admin',
            is_active = true
        WHERE username = 'doua';
    """), {"password_hash": hashed_doua_password})
    
    conn.commit()
    print("✅ User updated successfully!")
    print("   - doua@stockit.local (password: 0000)")

print("\nVerifying users...")
with engine.connect() as conn:
    result = conn.execute(text("SELECT username, email, name, role FROM users"))
    print("\nUsers in database:")
    for row in result:
        print(f"  - {row.username} | {row.email} | {row.name or '(no name)'} | {row.role}")




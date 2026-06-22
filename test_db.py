import psycopg2

try:
    conn = psycopg2.connect(
        host="localhost",
        database="chatbot",
        user="chatbot_user",
        password="Password@123"
    )

    print("✓ Database connection successful!")
    conn.close()

except Exception as e:
    print(f"✗ Connection failed: {e}")
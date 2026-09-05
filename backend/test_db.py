from database import get_connection


try:
    db = get_connection()

    print("✅ MySQL connection successful!")

    cursor = db.cursor()

    cursor.execute("SELECT DATABASE();")

    result = cursor.fetchone()

    print("Connected database:", result[0])

    cursor.close()
    db.close()

except Exception as e:

    print("❌ Database connection failed!")
    print(e)
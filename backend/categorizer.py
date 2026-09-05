import pandas as pd


def categorize_transaction(description):

    description = description.upper()

    if "SALARY" in description:
        return "Income"

    elif "ZOMATO" in description:
        return "Food"

    elif "SWIGGY" in description:
        return "Food"

    elif "AMAZON" in description:
        return "Shopping"

    elif "FLIPKART" in description:
        return "Shopping"

    elif "NETFLIX" in description:
        return "Entertainment"

    elif "BOOK MY SHOW" in description:
        return "Entertainment"

    elif "RENT" in description:
        return "Rent"

    elif "ELECTRICITY" in description:
        return "Utilities"

    elif "OLA" in description:
        return "Transport"

    elif "UBER" in description:
        return "Transport"

    elif "MEDICAL" in description:
        return "Healthcare"

    else:
        return "Other"


# ==========================
# DATABASE CATEGORIZATION
# ==========================

from database import get_connection


db = get_connection()
cursor = db.cursor(dictionary=True)

cursor.execute("""
    SELECT transaction_id, description
    FROM transactions
""")

transactions = cursor.fetchall()


for transaction in transactions:

    category = categorize_transaction(
        transaction["description"]
    )

    cursor.execute("""
        UPDATE transactions
        SET category = %s
        WHERE transaction_id = %s
    """, (
        category,
        transaction["transaction_id"]
    ))


db.commit()

print("\n===== CATEGORIZATION COMPLETED =====")
print(f"Total transactions categorized: {len(transactions)}")


cursor.close()
db.close()
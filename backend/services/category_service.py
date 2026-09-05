def detect_category(description):

    if not description:
        return "Other"

    text = description.lower()

    category_keywords = {

        "Food & Dining": [
            "restaurant",
            "hotel",
            "food",
            "swiggy",
            "zomato",
            "canteen",
            "cafe",
            "coffee",
            "bakery",
            "pizza",
            "dining"
        ],

        "Shopping": [
            "amazon",
            "flipkart",
            "myntra",
            "shopping",
            "mart",
            "store",
            "retail",
            "mall"
        ],

        "Travel": [
            "uber",
            "ola",
            "taxi",
            "cab",
            "flight",
            "airline",
            "irctc",
            "travel",
            "bus",
            "railway",
            "metro"
        ],

        "Bills & Utilities": [
            "electricity",
            "water",
            "gas",
            "recharge",
            "mobile",
            "internet",
            "broadband",
            "airtel",
            "jio",
            "vi",
            "bsnl"
        ],

        "Entertainment": [
            "netflix",
            "spotify",
            "movie",
            "cinema",
            "bookmyshow",
            "entertainment",
            "prime video"
        ],

        "Healthcare": [
            "hospital",
            "medical",
            "pharmacy",
            "doctor",
            "clinic",
            "health"
        ],

        "Education": [
            "college",
            "school",
            "university",
            "course",
            "education",
            "udemy",
            "coursera"
        ],

        "Fuel": [
            "petrol",
            "diesel",
            "fuel",
            "hpcl",
            "bpcl",
            "iocl"
        ],

        "Salary": [
            "salary",
            "payroll",
            "wages"
        ],

        "Transfer": [
            "transfer",
            "upi",
            "neft",
            "imps",
            "rtgs"
        ]
    }

    for category, keywords in category_keywords.items():

        for keyword in keywords:

            if keyword in text:
                return category

    return "Other"
import re
from datetime import datetime

from services.category_service import detect_category


# ============================================================
# DATE PARSER
# ============================================================

def parse_date(date_text):

    if not date_text:
        return None

    date_text = date_text.strip()

    formats = [
        "%d %B %Y",
        "%d %b %Y",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%d.%m.%Y",
        "%Y-%m-%d",
        "%d-%b-%Y",
        "%d-%B-%Y",
        "%d/%b/%Y",
        "%d/%B/%Y",
        "%d-%m-%y",
        "%d/%m/%y"
    ]

    for fmt in formats:

        try:
            return datetime.strptime(
                date_text,
                fmt
            ).date()

        except ValueError:
            continue

    return None


# ============================================================
# AMOUNT CLEANER
# ============================================================

def clean_amount(amount_text):

    if not amount_text:
        return None

    amount_text = str(amount_text)

    amount_text = (
        amount_text
        .replace(",", "")
        .replace("₹", "")
        .replace("Rs.", "")
        .replace("Rs", "")
        .replace("INR", "")
        .strip()
    )

    if (
        amount_text.startswith("(")
        and amount_text.endswith(")")
    ):

        amount_text = (
            "-"
            + amount_text[1:-1]
        )

    amount_text = amount_text.replace(
        " ",
        ""
    )

    try:

        return abs(
            float(amount_text)
        )

    except ValueError:

        return None


# ============================================================
# TRANSACTION PARSER
# ============================================================

def parse_transactions(text):

    transactions = []

    if not text:
        return transactions

    lines = text.splitlines()

    # Continue your existing pattern_1,
    # pattern_2, pattern_3 and parsing logic here.


    # ========================================================
    # FORMAT 1
    #
    # NAME Union 1321 -60.00 26 July 2026 SUCCESS
    # ========================================================

    pattern_1 = re.compile(
        r"^(.*?)\s+"
        r"(?:Union\s+)?"
        r"(?:XXXX)?\d*\s+"
        r"([+-]?\s*[\d,]+(?:\.\d+)?)\s+"
        r"(\d{1,2}\s+[A-Za-z]+\s+\d{4})\s+"
        r"(SUCCESS|COMPLETED|SUCCESSFUL)\s*$",
        re.IGNORECASE
    )


    # ========================================================
    # FORMAT 2
    #
    # 26/07/2026 AMAZON 500.00
    # ========================================================

    pattern_2 = re.compile(
        r"^(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\s+"
        r"(.+?)\s+"
        r"([+-]?[\d,]+(?:\.\d+)?)$",
        re.IGNORECASE
    )


    # ========================================================
    # FORMAT 3
    #
    # AMAZON 26 July 2026 -500.00
    # ========================================================

    pattern_3 = re.compile(
        r"^(.+?)\s+"
        r"(\d{1,2}\s+[A-Za-z]+\s+\d{4})\s+"
        r"([+-]?[\d,]+(?:\.\d+)?)$",
        re.IGNORECASE
    )


    for line in lines:

        line = line.strip()

        if not line:

            continue


        # ====================================================
        # FORMAT 1
        # ====================================================

        match = pattern_1.match(line)

        if match:

            description = (
                match.group(1)
                .strip()
            )

            amount_text = (
                match.group(2)
                .replace(" ", "")
                .strip()
            )

            date_text = (
                match.group(3)
                .strip()
            )

            amount = clean_amount(
                amount_text
            )

            if amount is None:

                continue

            transaction_type = (

                "CREDIT"

                if amount_text.startswith("+")
                else "DEBIT"
            )

            transaction_date = parse_date(
                date_text
            )

            if transaction_date is None:

                continue

            transactions.append({

                "transaction_date":
                    transaction_date,

                "description":
                    description,

                "amount":
                    amount,

                "transaction_type":
                    transaction_type,

                "category":
                    detect_category(
                        description
                    )
            })

            continue


        # ====================================================
        # FORMAT 2
        # ====================================================

        match = pattern_2.match(line)

        if match:

            date_text = (
                match.group(1)
                .strip()
            )

            description = (
                match.group(2)
                .strip()
            )

            amount_text = (
                match.group(3)
                .strip()
            )

            transaction_date = parse_date(
                date_text
            )

            amount = clean_amount(
                amount_text
            )

            if (
                transaction_date
                and amount is not None
            ):

                transaction_type = (

                    "CREDIT"

                    if amount_text.startswith("+")
                    else "DEBIT"
                )

                transactions.append({

                    "transaction_date":
                        transaction_date,

                    "description":
                        description,

                    "amount":
                        amount,

                    "transaction_type":
                        transaction_type,

                    "category":
                        detect_category(
                            description
                        )
                })

                continue


        # ====================================================
        # FORMAT 3
        # ====================================================

        match = pattern_3.match(line)

        if match:

            description = (
                match.group(1)
                .strip()
            )

            date_text = (
                match.group(2)
                .strip()
            )

            amount_text = (
                match.group(3)
                .strip()
            )

            transaction_date = parse_date(
                date_text
            )

            amount = clean_amount(
                amount_text
            )

            if (
                transaction_date
                and amount is not None
            ):

                transaction_type = (

                    "CREDIT"

                    if amount_text.startswith("+")
                    else "DEBIT"
                )

                transactions.append({

                    "transaction_date":
                        transaction_date,

                    "description":
                        description,

                    "amount":
                        amount,

                    "transaction_type":
                        transaction_type,

                    "category":
                        detect_category(
                            description
                        )
                })

                continue

    return transactions


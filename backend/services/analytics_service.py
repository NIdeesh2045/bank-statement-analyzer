# ============================================================
# ANALYTICS SERVICE
# ============================================================


def get_balance_data(
    cursor,
    statement_id,
    default_user_id
):
    """
    Calculate total income, total expense,
    and balance for a statement or user.
    """

    # ========================================================
    # STATEMENT-SPECIFIC BALANCE
    # ========================================================

    if statement_id is not None:

        cursor.execute(
            """
            SELECT

                COALESCE(
                    SUM(
                        CASE
                            WHEN transaction_type = 'CREDIT'
                            THEN amount
                            ELSE 0
                        END
                    ),
                    0
                ) AS total_income,

                COALESCE(
                    SUM(
                        CASE
                            WHEN transaction_type = 'DEBIT'
                            THEN amount
                            ELSE 0
                        END
                    ),
                    0
                ) AS total_expense

            FROM transactions

            WHERE statement_id = %s
            """,
            (
                statement_id,
            )
        )

    # ========================================================
    # ALL USER STATEMENTS
    # ========================================================

    else:

        cursor.execute(
            """
            SELECT

                COALESCE(
                    SUM(
                        CASE
                            WHEN transactions.transaction_type = 'CREDIT'
                            THEN transactions.amount
                            ELSE 0
                        END
                    ),
                    0
                ) AS total_income,

                COALESCE(
                    SUM(
                        CASE
                            WHEN transactions.transaction_type = 'DEBIT'
                            THEN transactions.amount
                            ELSE 0
                        END
                    ),
                    0
                ) AS total_expense

            FROM transactions

            INNER JOIN statements
                ON transactions.statement_id =
                   statements.statement_id

            WHERE statements.user_id = %s
            """,
            (
                default_user_id,
            )
        )

    # ========================================================
    # GET RESULT
    # ========================================================

    result = cursor.fetchone()

    income = float(
        result["total_income"] or 0
    )

    expense = float(
        result["total_expense"] or 0
    )

    balance = income - expense

    return {
        "total_income": income,
        "total_expense": expense,
        "balance": balance
    }
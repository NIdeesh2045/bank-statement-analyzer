from fastapi import APIRouter, UploadFile, File

import os
import shutil

from services.pdf_service import extract_text_from_pdf
from services.transaction_parser import parse_transactions

from database import get_connection


router = APIRouter()


# ============================================================
# CONFIGURATION
# ============================================================

UPLOAD_DIR = "uploads"
DEFAULT_USER_ID = 1

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)


# ============================================================
# UPLOAD STATEMENT
# ============================================================

@router.post("/upload-statement")
async def upload_statement(
    file: UploadFile = File(...)
):

    # ========================================================
    # CHECK FILE
    # ========================================================

    if not file.filename:

        return {
            "success": False,
            "message": "No file selected."
        }


    if not file.filename.lower().endswith(".pdf"):

        return {
            "success": False,
            "message": "Only PDF files are allowed."
        }


    # ========================================================
    # SAFE FILE NAME
    # ========================================================

    safe_filename = os.path.basename(
        file.filename
    )

    file_path = os.path.join(
        UPLOAD_DIR,
        safe_filename
    )


    # ========================================================
    # SAVE PDF
    # ========================================================

    try:

        with open(
            file_path,
            "wb"
        ) as buffer:

            shutil.copyfileobj(
                file.file,
                buffer
            )

    except Exception as e:

        return {
            "success": False,
            "message": "Unable to save PDF.",
            "error": str(e)
        }


    # ========================================================
    # READ PDF
    # ========================================================

    try:

        extracted_text = extract_text_from_pdf(
            file_path
        )

    except Exception as e:

        return {
            "success": False,
            "message": "Unable to read PDF.",
            "error": str(e)
        }


    # ========================================================
    # PARSE TRANSACTIONS
    # ========================================================

    parsed_transactions = parse_transactions(
        extracted_text
    )


    # ========================================================
    # DATABASE
    # ========================================================

    db = None
    cursor = None

    try:

        db = get_connection()

        cursor = db.cursor(
            dictionary=True
        )


        # ====================================================
        # CREATE STATEMENT
        # ====================================================

        cursor.execute(
            """
            INSERT INTO statements
            (
                user_id,
                file_name
            )
            VALUES
            (
                %s,
                %s
            )
            """,
            (
                DEFAULT_USER_ID,
                safe_filename
            )
        )

        statement_id = cursor.lastrowid


        # ====================================================
        # INSERT TRANSACTIONS
        # ====================================================

        inserted_count = 0

        for transaction in parsed_transactions:

            cursor.execute(
                """
                INSERT INTO transactions
                (
                    statement_id,
                    transaction_date,
                    description,
                    amount,
                    transaction_type,
                    category
                )
                VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                (
                    statement_id,

                    transaction[
                        "transaction_date"
                    ],

                    transaction[
                        "description"
                    ],

                    transaction[
                        "amount"
                    ],

                    transaction[
                        "transaction_type"
                    ],

                    transaction[
                        "category"
                    ]
                )
            )

            inserted_count += 1


        db.commit()


        # ====================================================
        # RESPONSE
        # ====================================================

        return {

            "success": True,

            "message":
                "Statement uploaded and transactions imported successfully.",

            "filename":
                safe_filename,

            "statement_id":
                statement_id,

            "user_id":
                DEFAULT_USER_ID,

            "text_length":
                len(extracted_text),

            "transactions_found":
                len(parsed_transactions),

            "transactions_inserted":
                inserted_count
        }


    except Exception as e:

        if db:
            db.rollback()

        return {

            "success": False,

            "message":
                "Database import failed.",

            "error":
                str(e)
        }


    finally:

        if cursor:
            cursor.close()

        if db:
            db.close()
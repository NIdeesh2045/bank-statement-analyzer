# ============================================================
# AI BANK STATEMENT ANALYZER
# MAIN FASTAPI APPLICATION
# ============================================================

from pydantic import BaseModel

from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user
)

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Query,
    HTTPException,
    Depends
)

from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

import os
import shutil
import uuid
import csv
import io

from services.transaction_parser import parse_transactions
from services.pdf_service import extract_text_from_pdf

from database import get_connection
from config import UPLOAD_DIR
from services.analytics_service import get_balance_data


# ============================================================
# AUTHENTICATION MODELS
# ============================================================

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class ResetPasswordRequest(BaseModel):
    email: str
    new_password: str


# ============================================================
# FASTAPI APP
# ============================================================

app = FastAPI(
    title="AI Bank Statement Analyzer",
    description="API for analyzing bank statements",
    version="2.0"
)


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ============================================================
# CONFIGURATION
# ============================================================

os.makedirs(
    UPLOAD_DIR,
    exist_ok=True
)


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():

    return {
        "project": "AI Bank Statement Analyzer",
        "status": "Running",
        "version": "2.0"
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "healthy",
        "api": "running"
    }


# ============================================================
# REGISTER USER
# ============================================================

@app.post("/register")
def register_user(
    request: RegisterRequest
):

    db = get_connection()

    cursor = db.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT
                user_id,
                name,
                email
            FROM users
            WHERE email = %s
            """,
            (
                request.email,
            )
        )

        existing_user = cursor.fetchone()

        if existing_user:

            raise HTTPException(
                status_code=400,
                detail="Email already registered."
            )

        password_hash = hash_password(
            request.password
        )

        cursor.execute(
            """
            INSERT INTO users
            (
                name,
                email,
                password_hash
            )
            VALUES
            (
                %s,
                %s,
                %s
            )
            """,
            (
                request.name,
                request.email,
                password_hash
            )
        )

        db.commit()

        user_id = cursor.lastrowid

        return {
            "success": True,
            "message": "User registered successfully.",
            "user": {
                "user_id": user_id,
                "name": request.name,
                "email": request.email
            }
        }

    except HTTPException:

        db.rollback()
        raise

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to register user: " + str(e)
        )

    finally:

        cursor.close()
        db.close()


# ============================================================
# LOGIN USER
# ============================================================

@app.post("/login")
def login_user(
    request: LoginRequest
):

    db = get_connection()

    cursor = db.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT
                user_id,
                name,
                email,
                password_hash
            FROM users
            WHERE email = %s
            """,
            (
                request.email,
            )
        )

        user = cursor.fetchone()

        if not user:

            raise HTTPException(
                status_code=401,
                detail="Invalid email or password."
            )

        password_valid = verify_password(
            request.password,
            user["password_hash"]
        )

        if not password_valid:

            raise HTTPException(
                status_code=401,
                detail="Invalid email or password."
            )

        access_token = create_access_token(
            user["user_id"]
        )

        return {
            "success": True,
            "message": "Login successful.",
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "user_id": user["user_id"],
                "name": user["name"],
                "email": user["email"]
            }
        }

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail="Unable to login: " + str(e)
        )

    finally:

        cursor.close()
        db.close()


# ============================================================
# OAUTH2 TOKEN LOGIN
# ============================================================

@app.post("/token")
def login_for_swagger(
    form_data: OAuth2PasswordRequestForm = Depends()
):

    db = get_connection()

    cursor = db.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT
                user_id,
                name,
                email,
                password_hash
            FROM users
            WHERE email = %s
            """,
            (
                form_data.username,
            )
        )

        user = cursor.fetchone()

        if not user:

            raise HTTPException(
                status_code=401,
                detail="Invalid email or password."
            )

        password_valid = verify_password(
            form_data.password,
            user["password_hash"]
        )

        if not password_valid:

            raise HTTPException(
                status_code=401,
                detail="Invalid email or password."
            )

        access_token = create_access_token(
            user["user_id"]
        )

        return {
            "access_token": access_token,
            "token_type": "bearer"
        }

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail="Unable to login: " + str(e)
        )

    finally:

        cursor.close()
        db.close()


# ============================================================
# RESET PASSWORD
# ============================================================

@app.post("/reset-password")
def reset_password(
    request: ResetPasswordRequest
):

    db = get_connection()

    cursor = db.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT
                user_id,
                email
            FROM users
            WHERE email = %s
            """,
            (
                request.email,
            )
        )

        user = cursor.fetchone()

        if not user:

            raise HTTPException(
                status_code=404,
                detail="User with this email does not exist."
            )

        new_password_hash = hash_password(
            request.new_password
        )

        cursor.execute(
            """
            UPDATE users
            SET password_hash = %s
            WHERE user_id = %s
            """,
            (
                new_password_hash,
                user["user_id"]
            )
        )

        db.commit()

        return {
            "success": True,
            "message": "Password reset successfully."
        }

    except HTTPException:

        db.rollback()
        raise

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail="Unable to reset password: " + str(e)
        )

    finally:

        cursor.close()
        db.close()


# ============================================================
# VERIFY STATEMENT OWNERSHIP
# ============================================================

def verify_statement(
    cursor,
    statement_id: int,
    current_user_id: int
):

    cursor.execute(
        """
        SELECT
            statement_id,
            user_id,
            file_name,
            upload_date
        FROM statements
        WHERE statement_id = %s
        AND user_id = %s
        """,
        (
            statement_id,
            current_user_id
        )
    )

    return cursor.fetchone()


# ============================================================
# UPLOAD BANK STATEMENT
# ============================================================

@app.post("/upload-statement")
def upload_statement(
    file: UploadFile = File(...),
    current_user_id: int = Depends(get_current_user)
):

    # ========================================================
    # SECURE FILE VALIDATION
    # ========================================================

    if not file.filename:

        return {
            "success": False,
            "message": "No file selected."
        }

    safe_filename = os.path.basename(
        file.filename
    )

    if not safe_filename.lower().endswith(".pdf"):

        return {
            "success": False,
            "message": "Only PDF files are allowed."
        }

    # ========================================================
    # CHECK ACTUAL PDF SIGNATURE
    # ========================================================

    try:

        file.file.seek(0)

        file_header = file.file.read(5)

        file.file.seek(0)

        if file_header != b"%PDF-":

            return {
                "success": False,
                "message": "Invalid PDF file."
            }

    except Exception as e:

        return {
            "success": False,
            "message": "Unable to validate the uploaded file.",
            "error": str(e)
        }

    # ========================================================
    # FILE SIZE LIMIT
    # MAXIMUM 10 MB
    # ========================================================

    MAX_FILE_SIZE = 10 * 1024 * 1024

    file_size = 0

    try:

        while True:

            chunk = file.file.read(
                1024 * 1024
            )

            if not chunk:
                break

            file_size += len(chunk)

            if file_size > MAX_FILE_SIZE:

                file.file.seek(0)

                return {
                    "success": False,
                    "message":
                        "PDF file is too large. "
                        "Maximum size is 10 MB."
                }

        file.file.seek(0)

    except Exception as e:

        file.file.seek(0)

        return {
            "success": False,
            "message": "Unable to validate file size.",
            "error": str(e)
        }

    # ========================================================
    # UNIQUE SERVER FILE NAME
    # ========================================================

    stored_filename = (
        f"{uuid.uuid4().hex}.pdf"
    )

    file_path = os.path.join(
        UPLOAD_DIR,
        stored_filename
    )

    # ========================================================
    # SAVE UPLOADED PDF
    # ========================================================

    try:

        file.file.seek(0)

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
    # EXTRACT TEXT FROM PDF
    # ========================================================

    try:

        extracted_text = extract_text_from_pdf(
            file_path
        )

    except Exception as e:

        try:

            if os.path.exists(file_path):
                os.remove(file_path)

        except Exception:
            pass

        return {
            "success": False,
            "message": "Unable to extract text from PDF.",
            "error": str(e)
        }

    # ========================================================
    # CHECK EXTRACTED TEXT
    # ========================================================

    if not extracted_text:

        try:

            if os.path.exists(file_path):
                os.remove(file_path)

        except Exception:
            pass

        return {
            "success": False,
            "message": "No readable text found in the PDF."
        }

    # ========================================================
    # CONVERT EXTRACTED RESULT TO TEXT
    # ========================================================

    if isinstance(extracted_text, tuple):

        extracted_text = extracted_text[0]

    # ========================================================
    # PARSE TRANSACTIONS
    # ========================================================

    try:

        transactions = parse_transactions(
            extracted_text
        )

    except Exception as e:

        try:

            if os.path.exists(file_path):
                os.remove(file_path)

        except Exception:
            pass

        return {
            "success": False,
            "message": "Unable to parse transactions.",
            "error": str(e)
        }

    # ========================================================
    # CHECK TRANSACTIONS
    # ========================================================

    if not transactions:

        try:

            if os.path.exists(file_path):
                os.remove(file_path)

        except Exception:
            pass

        return {
            "success": False,
            "message":
                "No transactions were found in the PDF."
        }

    # ========================================================
    # DATABASE
    # ========================================================

    db = get_connection()

    cursor = db.cursor(
        dictionary=True
    )

    try:

        # ====================================================
        # INSERT STATEMENT
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
                current_user_id,
                safe_filename
            )
        )

        statement_id = cursor.lastrowid

        # ====================================================
        # INSERT TRANSACTIONS
        # ====================================================

        inserted_transactions = 0

        for transaction in transactions:

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
                    transaction.get(
                        "transaction_date"
                    ),
                    transaction.get(
                        "description"
                    ),
                    transaction.get(
                        "amount"
                    ),
                    transaction.get(
                        "transaction_type"
                    ),
                    transaction.get(
                        "category"
                    )
                )
            )

            inserted_transactions += 1

        # ====================================================
        # COMMIT
        # ====================================================

        db.commit()

        # ====================================================
        # RESPONSE
        # ====================================================

        return {

            "success": True,

            "message":
                "Bank statement uploaded successfully.",

            "statement_id":
                statement_id,

            "file_name":
                safe_filename,

            "transaction_count":
                inserted_transactions
        }

    except Exception as e:

        db.rollback()

        try:

            if os.path.exists(file_path):
                os.remove(file_path)

        except Exception:
            pass

        raise HTTPException(
            status_code=500,
            detail=
                "Unable to process bank statement: "
                + str(e)
        )

    finally:

        cursor.close()
        db.close()


# ============================================================
# LATEST STATEMENT
# ============================================================

@app.get("/latest-statement")
def latest_statement(
    current_user_id: int = Depends(get_current_user)
):

    db = get_connection()

    cursor = db.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT
                statement_id,
                user_id,
                file_name,
                upload_date
            FROM statements
            WHERE user_id = %s
            ORDER BY statement_id DESC
            LIMIT 1
            """,
            (
                current_user_id,
            )
        )

        result = cursor.fetchone()

        if not result:

            return {
                "success": False,
                "message": "No statement found."
            }

        return {
            "success": True,
            "statement": result
        }

    finally:

        cursor.close()
        db.close()


# ============================================================
# GET ALL STATEMENTS
# ============================================================

@app.get("/statements")
def get_statements(
    current_user_id: int = Depends(get_current_user)
):

    db = get_connection()

    cursor = db.cursor(
        dictionary=True
    )

    try:

        cursor.execute(
            """
            SELECT
                statement_id,
                user_id,
                file_name,
                upload_date
            FROM statements
            WHERE user_id = %s
            ORDER BY statement_id DESC
            """,
            (
                current_user_id,
            )
        )

        statements = cursor.fetchall()

        return {
            "success": True,
            "total_statements": len(statements),
            "statements": statements
        }

    finally:

        cursor.close()
        db.close()


# ============================================================
# DELETE STATEMENT
# ============================================================

@app.delete("/statements/{statement_id}")
def delete_statement(
    statement_id: int,
    current_user_id: int = Depends(get_current_user)
):

    db = get_connection()

    cursor = db.cursor(
        dictionary=True
    )

    try:

        statement = verify_statement(
            cursor,
            statement_id,
            current_user_id
        )

        if not statement:

            raise HTTPException(
                status_code=404,
                detail="Statement not found."
            )

        cursor.execute(
            """
            DELETE FROM statements
            WHERE statement_id = %s
            AND user_id = %s
            """,
            (
                statement_id,
                current_user_id
            )
        )

        db.commit()

        return {

            "success": True,

            "message":
                "Statement deleted successfully.",

            "statement_id":
                statement_id,

            "file_name":
                statement["file_name"],

            "transactions_deleted":
                "All transactions linked to this statement were deleted automatically."
        }

    except HTTPException:

        db.rollback()
        raise

    except Exception as e:

        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=
                "Unable to delete statement: "
                + str(e)
        )

    finally:

        cursor.close()
        db.close()


# ============================================================
# GET TRANSACTIONS
# ============================================================

@app.get("/transactions")
def get_transactions(
    statement_id: int | None = Query(default=None),
    search: str | None = Query(default=None),
    transaction_type: str | None = Query(default=None),
    category: str | None = Query(default=None),
    start_date: str | None = Query(default=None),
    end_date: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20000, ge=1, le=20000),
    current_user_id: int = Depends(get_current_user)
):

    db = get_connection()

    cursor = db.cursor(
        dictionary=True
    )

    try:

        if statement_id is not None:

            statement = verify_statement(
                cursor,
                statement_id,
                current_user_id
            )

            if not statement:

                raise HTTPException(
                    status_code=404,
                    detail="Statement not found."
                )

        query = """
            FROM transactions t
            INNER JOIN statements s
                ON t.statement_id = s.statement_id
            WHERE s.user_id = %s
        """

        parameters = [
            current_user_id
        ]

        if statement_id is not None:

            query += """
                AND t.statement_id = %s
            """

            parameters.append(
                statement_id
            )

        if search:

            query += """
                AND (
                    t.description LIKE %s
                    OR t.category LIKE %s
                )
            """

            search_value = f"%{search}%"

            parameters.extend([
                search_value,
                search_value
            ])

        if transaction_type:

            transaction_type = (
                transaction_type.upper()
            )

            if transaction_type not in [
                "CREDIT",
                "DEBIT"
            ]:

                raise HTTPException(
                    status_code=400,
                    detail=
                        "transaction_type must be CREDIT or DEBIT."
                )

            query += """
                AND t.transaction_type = %s
            """

            parameters.append(
                transaction_type
            )

        if category:

            query += """
                AND t.category = %s
            """

            parameters.append(
                category
            )

        if start_date:

            query += """
                AND t.transaction_date >= %s
            """

            parameters.append(
                start_date
            )

        if end_date:

            query += """
                AND t.transaction_date <= %s
            """

            parameters.append(
                end_date
            )

        # ====================================================
        # COUNT
        # ====================================================

        count_query = """
            SELECT COUNT(*) AS total
        """ + query

        cursor.execute(
            count_query,
            tuple(parameters)
        )

        total_transactions = cursor.fetchone()["total"]

        # ====================================================
        # PAGINATION
        # ====================================================

        offset = (
            page - 1
        ) * limit

        total_pages = (
            (
                total_transactions
                + limit
                - 1
            ) // limit
            if total_transactions > 0
            else 0
        )

        # ====================================================
        # GET TRANSACTIONS
        # ====================================================

        transaction_query = """
            SELECT
                t.transaction_id,
                t.statement_id,
                t.transaction_date,
                t.description,
                t.amount,
                t.transaction_type,
                t.category
        """ + query + """

            ORDER BY
                t.transaction_date DESC,
                t.transaction_id DESC

            LIMIT %s OFFSET %s
        """

        transaction_parameters = (
            parameters
            + [
                limit,
                offset
            ]
        )

        cursor.execute(
            transaction_query,
            tuple(transaction_parameters)
        )

        transactions = cursor.fetchall()

        # ====================================================
        # FORMAT DATA
        # ====================================================

        for transaction in transactions:

            transaction["amount"] = float(
                transaction["amount"] or 0
            )

            if transaction["transaction_date"]:

                transaction["transaction_date"] = (
                    transaction[
                        "transaction_date"
                    ].isoformat()
                )

        return {

            "success": True,

            "pagination": {
                "page": page,
                "limit": limit,
                "total_transactions":
                    total_transactions,
                "total_pages":
                    total_pages,
                "has_next":
                    page < total_pages,
                "has_previous":
                    page > 1
            },

            "filters": {
                "statement_id":
                    statement_id,
                "search":
                    search,
                "transaction_type":
                    transaction_type,
                "category":
                    category,
                "start_date":
                    start_date,
                "end_date":
                    end_date
            },

            "transactions":
                transactions
        }

    finally:

        cursor.close()
        db.close()


# ============================================================
# EXPORT TRANSACTIONS TO CSV
# ============================================================

@app.get("/export-transactions")
def export_transactions(
    statement_id: int | None = Query(default=None),
    current_user_id: int = Depends(get_current_user)
):

    db = get_connection()

    cursor = db.cursor(
        dictionary=True
    )

    try:

        if statement_id is not None:

            statement = verify_statement(
                cursor,
                statement_id,
                current_user_id
            )

            if not statement:

                raise HTTPException(
                    status_code=404,
                    detail="Statement not found."
                )

        query = """
            SELECT
                t.transaction_id,
                t.statement_id,
                t.transaction_date,
                t.description,
                t.amount,
                t.transaction_type,
                t.category
            FROM transactions t
            INNER JOIN statements s
                ON t.statement_id = s.statement_id
            WHERE s.user_id = %s
        """

        parameters = [
            current_user_id
        ]

        if statement_id is not None:

            query += """
                AND t.statement_id = %s
            """

            parameters.append(
                statement_id
            )

        query += """
            ORDER BY
                t.transaction_date DESC,
                t.transaction_id DESC
        """

        cursor.execute(
            query,
            tuple(parameters)
        )

        transactions = cursor.fetchall()

        output = io.StringIO()

        writer = csv.writer(
            output
        )

        writer.writerow([
            "Transaction ID",
            "Statement ID",
            "Date",
            "Description",
            "Amount",
            "Transaction Type",
            "Category"
        ])

        for transaction in transactions:

            writer.writerow([
                transaction["transaction_id"],
                transaction["statement_id"],
                transaction["transaction_date"],
                transaction["description"],
                transaction["amount"],
                transaction["transaction_type"],
                transaction["category"]
            ])

        output.seek(0)

        return StreamingResponse(
            iter([
                output.getvalue()
            ]),
            media_type="text/csv",
            headers={
                "Content-Disposition":
                    "attachment; filename=transactions.csv"
            }
        )

    finally:

        cursor.close()
        db.close()


# ============================================================
# CATEGORY SUMMARY
# ============================================================

@app.get("/category-summary")
def category_summary(
    statement_id: int | None = Query(default=None),
    current_user_id: int = Depends(get_current_user)
):

    db = get_connection()

    cursor = db.cursor(
        dictionary=True
    )

    try:

        if statement_id is not None:

            statement = verify_statement(
                cursor,
                statement_id,
                current_user_id
            )

            if not statement:

                raise HTTPException(
                    status_code=404,
                    detail="Statement not found."
                )

            cursor.execute(
                """
                SELECT
                    category,
                    SUM(amount) AS total_amount,
                    COUNT(*) AS transaction_count
                FROM transactions
                WHERE transaction_type = 'DEBIT'
                AND statement_id = %s
                GROUP BY category
                ORDER BY total_amount DESC
                """,
                (
                    statement_id,
                )
            )

        else:

            cursor.execute(
                """
                SELECT
                    category,
                    SUM(amount) AS total_amount,
                    COUNT(*) AS transaction_count
                FROM transactions
                WHERE transaction_type = 'DEBIT'
                AND statement_id IN (
                    SELECT statement_id
                    FROM statements
                    WHERE user_id = %s
                )
                GROUP BY category
                ORDER BY total_amount DESC
                """,
                (
                    current_user_id,
                )
            )

        result = cursor.fetchall()

        for item in result:

            item["total_amount"] = float(
                item["total_amount"] or 0
            )

            item["transaction_count"] = int(
                item["transaction_count"] or 0
            )

        return {
            "success": True,
            "category_summary": result
        }

    finally:

        cursor.close()
        db.close()


# ============================================================
# BALANCE
# ============================================================

@app.get("/balance")
def get_balance(
    statement_id: int | None = Query(default=None),
    current_user_id: int = Depends(get_current_user)
):

    db = get_connection()

    cursor = db.cursor(
        dictionary=True
    )

    try:

        if statement_id is not None:

            statement = verify_statement(
                cursor,
                statement_id,
                current_user_id
            )

            if not statement:

                raise HTTPException(
                    status_code=404,
                    detail="Statement not found."
                )

        result = get_balance_data(
            cursor,
            statement_id,
            current_user_id
        )

        return {

            "success": True,

            "total_income":
                result["total_income"],

            "total_expense":
                result["total_expense"],

            "balance":
                result["balance"]
        }

    finally:

        cursor.close()
        db.close()


# ============================================================
# HIGHEST EXPENSE
# ============================================================

@app.get("/highest-expense")
def highest_expense(
    statement_id: int | None = Query(default=None),
    current_user_id: int = Depends(get_current_user)
):

    db = get_connection()

    cursor = db.cursor(
        dictionary=True
    )

    try:

        if statement_id is not None:

            statement = verify_statement(
                cursor,
                statement_id,
                current_user_id
            )

            if not statement:

                raise HTTPException(
                    status_code=404,
                    detail="Statement not found."
                )

            cursor.execute(
                """
                SELECT
                    description,
                    amount,
                    category,
                    transaction_date
                FROM transactions
                WHERE transaction_type = 'DEBIT'
                AND statement_id = %s
                ORDER BY amount DESC
                LIMIT 1
                """,
                (
                    statement_id,
                )
            )

        else:

            cursor.execute(
                """
                SELECT
                    t.description,
                    t.amount,
                    t.category,
                    t.transaction_date
                FROM transactions t
                INNER JOIN statements s
                    ON t.statement_id = s.statement_id
                WHERE t.transaction_type = 'DEBIT'
                AND s.user_id = %s
                ORDER BY t.amount DESC
                LIMIT 1
                """,
                (
                    current_user_id,
                )
            )

        result = cursor.fetchone()

        if not result:

            return {
                "success": True,
                "message": "No expense found."
            }

        result["amount"] = float(
            result["amount"] or 0
        )

        if result["transaction_date"]:

            result["transaction_date"] = (
                result[
                    "transaction_date"
                ].isoformat()
            )

        return {
            "success": True,
            "highest_expense": result
        }

    finally:

        cursor.close()
        db.close()


# ============================================================
# MONTHLY SPENDING
# ============================================================

@app.get("/monthly-spending")
def monthly_spending(
    statement_id: int | None = Query(default=None),
    current_user_id: int = Depends(get_current_user)
):

    db = get_connection()

    cursor = db.cursor(
        dictionary=True
    )

    try:

        if statement_id is not None:

            statement = verify_statement(
                cursor,
                statement_id,
                current_user_id
            )

            if not statement:

                raise HTTPException(
                    status_code=404,
                    detail="Statement not found."
                )

            cursor.execute(
                """
                SELECT
                    DATE_FORMAT(
                        transaction_date,
                        '%Y-%m'
                    ) AS month,
                    SUM(amount)
                    AS total_expense
                FROM transactions
                WHERE transaction_type = 'DEBIT'
                AND statement_id = %s
                GROUP BY
                    DATE_FORMAT(
                        transaction_date,
                        '%Y-%m'
                    )
                ORDER BY month
                """,
                (
                    statement_id,
                )
            )

        else:

            cursor.execute(
                """
                SELECT
                    DATE_FORMAT(
                        t.transaction_date,
                        '%Y-%m'
                    ) AS month,
                    SUM(t.amount)
                    AS total_expense
                FROM transactions t
                INNER JOIN statements s
                    ON t.statement_id = s.statement_id
                WHERE t.transaction_type = 'DEBIT'
                AND s.user_id = %s
                GROUP BY
                    DATE_FORMAT(
                        t.transaction_date,
                        '%Y-%m'
                    )
                ORDER BY month
                """,
                (
                    current_user_id,
                )
            )

        result = cursor.fetchall()

        for item in result:

            item["total_expense"] = float(
                item["total_expense"] or 0
            )

        return {
            "success": True,
            "monthly_spending": result
        }

    finally:

        cursor.close()
        db.close()


# ============================================================
# FINANCIAL INSIGHTS
# ============================================================

@app.get("/insights")
def get_insights(
    statement_id: int | None = Query(default=None),
    current_user_id: int = Depends(get_current_user)
):

    db = get_connection()

    cursor = db.cursor(
        dictionary=True
    )

    try:

        if statement_id is not None:

            statement = verify_statement(
                cursor,
                statement_id,
                current_user_id
            )

            if not statement:

                raise HTTPException(
                    status_code=404,
                    detail="Statement not found."
                )

        # ====================================================
        # TOTALS
        # ====================================================

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
                    ) AS income,

                    COALESCE(
                        SUM(
                            CASE
                                WHEN transaction_type = 'DEBIT'
                                THEN amount
                                ELSE 0
                            END
                        ),
                        0
                    ) AS expense

                FROM transactions

                WHERE statement_id = %s
                """,
                (
                    statement_id,
                )
            )

        else:

            cursor.execute(
                """
                SELECT

                    COALESCE(
                        SUM(
                            CASE
                                WHEN t.transaction_type = 'CREDIT'
                                THEN t.amount
                                ELSE 0
                            END
                        ),
                        0
                    ) AS income,

                    COALESCE(
                        SUM(
                            CASE
                                WHEN t.transaction_type = 'DEBIT'
                                THEN t.amount
                                ELSE 0
                            END
                        ),
                        0
                    ) AS expense

                FROM transactions t

                INNER JOIN statements s
                    ON t.statement_id = s.statement_id

                WHERE s.user_id = %s
                """,
                (
                    current_user_id,
                )
            )

        totals = cursor.fetchone()

        income = float(
            totals["income"] or 0
        )

        expense = float(
            totals["expense"] or 0
        )

        balance = income - expense

        # ====================================================
        # HIGHEST CATEGORY
        # ====================================================

        if statement_id is not None:

            cursor.execute(
                """
                SELECT
                    category,
                    SUM(amount) AS total_amount
                FROM transactions
                WHERE transaction_type = 'DEBIT'
                AND statement_id = %s
                GROUP BY category
                ORDER BY total_amount DESC
                LIMIT 1
                """,
                (
                    statement_id,
                )
            )

        else:

            cursor.execute(
                """
                SELECT
                    t.category,
                    SUM(t.amount) AS total_amount
                FROM transactions t
                INNER JOIN statements s
                    ON t.statement_id = s.statement_id
                WHERE t.transaction_type = 'DEBIT'
                AND s.user_id = %s
                GROUP BY t.category
                ORDER BY total_amount DESC
                LIMIT 1
                """,
                (
                    current_user_id,
                )
            )

        category = cursor.fetchone()

        # ====================================================
        # HIGHEST EXPENSE
        # ====================================================

        if statement_id is not None:

            cursor.execute(
                """
                SELECT
                    description,
                    amount,
                    category
                FROM transactions
                WHERE transaction_type = 'DEBIT'
                AND statement_id = %s
                ORDER BY amount DESC
                LIMIT 1
                """,
                (
                    statement_id,
                )
            )

        else:

            cursor.execute(
                """
                SELECT
                    t.description,
                    t.amount,
                    t.category
                FROM transactions t
                INNER JOIN statements s
                    ON t.statement_id = s.statement_id
                WHERE t.transaction_type = 'DEBIT'
                AND s.user_id = %s
                ORDER BY t.amount DESC
                LIMIT 1
                """,
                (
                    current_user_id,
                )
            )

        highest = cursor.fetchone()

        # ====================================================
        # EXPENSE PERCENTAGE
        # ====================================================

        if income > 0:

            expense_percentage = (
                expense / income
            ) * 100

        else:

            expense_percentage = 0

        return {

            "success": True,

            "income":
                round(income, 2),

            "expense":
                round(expense, 2),

            "balance":
                round(balance, 2),

            "expense_percentage":
                round(
                    expense_percentage,
                    2
                ),

            "highest_category":
                (
                    category["category"]
                    if category
                    else "N/A"
                ),

            "highest_category_amount":
                (
                    float(
                        category["total_amount"]
                    )
                    if category
                    else 0
                ),

            "highest_expense":
                (
                    highest["description"]
                    if highest
                    else "N/A"
                ),

            "highest_expense_amount":
                (
                    float(
                        highest["amount"]
                    )
                    if highest
                    else 0
                ),

            "highest_expense_category":
                (
                    highest["category"]
                    if highest
                    else "N/A"
                )
        }

    finally:

        cursor.close()
        db.close()


# ============================================================
# AI FINANCIAL ANALYTICS
# ============================================================

@app.get("/analytics")
def financial_analytics(
    statement_id: int | None = Query(default=None),
    current_user_id: int = Depends(get_current_user)
):

    db = get_connection()

    cursor = db.cursor(
        dictionary=True
    )

    try:

        if statement_id is not None:

            statement = verify_statement(
                cursor,
                statement_id,
                current_user_id
            )

            if not statement:

                raise HTTPException(
                    status_code=404,
                    detail="Statement not found."
                )

        # ====================================================
        # TOTALS
        # ====================================================

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
                    ) AS income,

                    COALESCE(
                        SUM(
                            CASE
                                WHEN transaction_type = 'DEBIT'
                                THEN amount
                                ELSE 0
                            END
                        ),
                        0
                    ) AS expense

                FROM transactions

                WHERE statement_id = %s
                """,
                (
                    statement_id,
                )
            )

        else:

            cursor.execute(
                """
                SELECT

                    COALESCE(
                        SUM(
                            CASE
                                WHEN t.transaction_type = 'CREDIT'
                                THEN t.amount
                                ELSE 0
                            END
                        ),
                        0
                    ) AS income,

                    COALESCE(
                        SUM(
                            CASE
                                WHEN t.transaction_type = 'DEBIT'
                                THEN t.amount
                                ELSE 0
                            END
                        ),
                        0
                    ) AS expense

                FROM transactions t

                INNER JOIN statements s
                    ON t.statement_id = s.statement_id

                WHERE s.user_id = %s
                """,
                (
                    current_user_id,
                )
            )

        totals = cursor.fetchone()

        income = float(
            totals["income"] or 0
        )

        expense = float(
            totals["expense"] or 0
        )

        # ====================================================
        # SAVINGS
        # ====================================================

        savings = income - expense

        if income > 0:

            savings_rate = (
                savings / income
            ) * 100

        else:

            savings_rate = 0

        # ====================================================
        # FINANCIAL HEALTH SCORE
        # ====================================================

        if income <= 0:

            health_score = 0

        elif savings_rate >= 30:

            health_score = 90

        elif savings_rate >= 20:

            health_score = 80

        elif savings_rate >= 10:

            health_score = 70

        elif savings_rate >= 0:

            health_score = 55

        elif savings_rate >= -10:

            health_score = 40

        else:

            health_score = 25

        # ====================================================
        # TOP CATEGORY
        # ====================================================

        if statement_id is not None:

            cursor.execute(
                """
                SELECT
                    category,
                    SUM(amount) AS total_amount
                FROM transactions
                WHERE transaction_type = 'DEBIT'
                AND statement_id = %s
                GROUP BY category
                ORDER BY total_amount DESC
                LIMIT 1
                """,
                (
                    statement_id,
                )
            )

        else:

            cursor.execute(
                """
                SELECT
                    t.category,
                    SUM(t.amount) AS total_amount
                FROM transactions t
                INNER JOIN statements s
                    ON t.statement_id = s.statement_id
                WHERE t.transaction_type = 'DEBIT'
                AND s.user_id = %s
                GROUP BY t.category
                ORDER BY total_amount DESC
                LIMIT 1
                """,
                (
                    current_user_id,
                )
            )

        top_category = cursor.fetchone()

        if top_category:

            top_category_name = (
                top_category["category"]
                or "Other"
            )

            top_category_amount = float(
                top_category["total_amount"]
                or 0
            )

        else:

            top_category_name = "N/A"
            top_category_amount = 0

        # ====================================================
        # TRANSACTION COUNT
        # ====================================================

        if statement_id is not None:

            cursor.execute(
                """
                SELECT COUNT(*) AS count
                FROM transactions
                WHERE statement_id = %s
                """,
                (
                    statement_id,
                )
            )

        else:

            cursor.execute(
                """
                SELECT COUNT(*) AS count
                FROM transactions t
                INNER JOIN statements s
                    ON t.statement_id = s.statement_id
                WHERE s.user_id = %s
                """,
                (
                    current_user_id,
                )
            )

        transaction_result = cursor.fetchone()

        transaction_count = int(
            transaction_result["count"] or 0
        )

        # ====================================================
        # AVERAGE TRANSACTION
        # ====================================================

        if transaction_count > 0:

            average_transaction = (
                expense / transaction_count
            )

        else:

            average_transaction = 0

        # ====================================================
        # SPENDING STATUS
        # ====================================================

        if income <= 0:

            spending_status = (
                "No income data available."
            )

        elif expense > income:

            spending_status = (
                "You are spending more than "
                "your recorded income."
            )

        elif savings_rate < 10:

            spending_status = (
                "Your savings rate is low. "
                "Consider reducing unnecessary expenses."
            )

        elif savings_rate < 20:

            spending_status = (
                "Your finances are stable, "
                "but there is room to improve savings."
            )

        else:

            spending_status = (
                "Your savings rate is healthy."
            )

        # ====================================================
        # RECOMMENDATION
        # ====================================================

        if expense > income:

            recommendation = (
                "Reduce discretionary spending "
                "and review your highest expense categories."
            )

        elif savings_rate < 10:

            recommendation = (
                "Try to save at least 10% of your income "
                "by controlling non-essential expenses."
            )

        elif savings_rate < 20:

            recommendation = (
                "Your finances are improving. "
                "Consider increasing your savings toward 20%."
            )

        else:

            recommendation = (
                "Good financial discipline. "
                "Continue maintaining your current savings habit."
            )

        return {

            "success": True,

            "income":
                round(income, 2),

            "expense":
                round(expense, 2),

            "savings":
                round(savings, 2),

            "savings_rate":
                round(savings_rate, 2),

            "health_score":
                health_score,

            "top_category":
                top_category_name,

            "top_category_amount":
                round(
                    top_category_amount,
                    2
                ),

            "transaction_count":
                transaction_count,

            "average_transaction":
                round(
                    average_transaction,
                    2
                ),

            "spending_status":
                spending_status,

            "recommendation":
                recommendation
        }

    finally:

        cursor.close()
        db.close()


# ============================================================
# ADVANCED FINANCIAL ANALYTICS
# ============================================================

@app.get("/advanced-analytics")
def advanced_analytics(
    statement_id: int | None = Query(default=None),
    current_user_id: int = Depends(get_current_user)
):

    db = get_connection()

    cursor = db.cursor(
        dictionary=True
    )

    try:

        if statement_id is not None:

            statement = verify_statement(
                cursor,
                statement_id,
                current_user_id
            )

            if not statement:

                raise HTTPException(
                    status_code=404,
                    detail="Statement not found."
                )

        # ====================================================
        # MONTHLY INCOME / EXPENSE
        # ====================================================

        if statement_id is not None:

            cursor.execute(
                """
                SELECT
                    DATE_FORMAT(
                        transaction_date,
                        '%Y-%m'
                    ) AS month,

                    COALESCE(
                        SUM(
                            CASE
                                WHEN transaction_type = 'CREDIT'
                                THEN amount
                                ELSE 0
                            END
                        ),
                        0
                    ) AS income,

                    COALESCE(
                        SUM(
                            CASE
                                WHEN transaction_type = 'DEBIT'
                                THEN amount
                                ELSE 0
                            END
                        ),
                        0
                    ) AS expense

                FROM transactions

                WHERE statement_id = %s

                GROUP BY
                    DATE_FORMAT(
                        transaction_date,
                        '%Y-%m'
                    )

                ORDER BY month
                """,
                (
                    statement_id,
                )
            )

        else:

            cursor.execute(
                """
                SELECT
                    DATE_FORMAT(
                        t.transaction_date,
                        '%Y-%m'
                    ) AS month,

                    COALESCE(
                        SUM(
                            CASE
                                WHEN t.transaction_type = 'CREDIT'
                                THEN t.amount
                                ELSE 0
                            END
                        ),
                        0
                    ) AS income,

                    COALESCE(
                        SUM(
                            CASE
                                WHEN t.transaction_type = 'DEBIT'
                                THEN t.amount
                                ELSE 0
                            END
                        ),
                        0
                    ) AS expense

                FROM transactions t

                INNER JOIN statements s
                    ON t.statement_id = s.statement_id

                WHERE s.user_id = %s

                GROUP BY
                    DATE_FORMAT(
                        t.transaction_date,
                        '%Y-%m'
                    )

                ORDER BY month
                """,
                (
                    current_user_id,
                )
            )

        monthly = cursor.fetchall()

        for item in monthly:

            item["income"] = float(
                item["income"] or 0
            )

            item["expense"] = float(
                item["expense"] or 0
            )

            item["savings"] = round(
                item["income"]
                - item["expense"],
                2
            )

        # ====================================================
        # TOP 5 EXPENSES
        # ====================================================

        if statement_id is not None:

            cursor.execute(
                """
                SELECT
                    description,
                    amount,
                    category,
                    transaction_date
                FROM transactions
                WHERE transaction_type = 'DEBIT'
                AND statement_id = %s
                ORDER BY amount DESC
                LIMIT 5
                """,
                (
                    statement_id,
                )
            )

        else:

            cursor.execute(
                """
                SELECT
                    t.description,
                    t.amount,
                    t.category,
                    t.transaction_date
                FROM transactions t
                INNER JOIN statements s
                    ON t.statement_id = s.statement_id
                WHERE t.transaction_type = 'DEBIT'
                AND s.user_id = %s
                ORDER BY t.amount DESC
                LIMIT 5
                """,
                (
                    current_user_id,
                )
            )

        top_expenses = cursor.fetchall()

        for item in top_expenses:

            item["amount"] = float(
                item["amount"] or 0
            )

            if item["transaction_date"]:

                item["transaction_date"] = (
                    item[
                        "transaction_date"
                    ].isoformat()
                )

        # ====================================================
        # TRANSACTION TYPES
        # ====================================================

        if statement_id is not None:

            cursor.execute(
                """
                SELECT
                    transaction_type,
                    COUNT(*) AS count,
                    SUM(amount) AS total
                FROM transactions
                WHERE statement_id = %s
                GROUP BY transaction_type
                """,
                (
                    statement_id,
                )
            )

        else:

            cursor.execute(
                """
                SELECT
                    t.transaction_type,
                    COUNT(*) AS count,
                    SUM(t.amount) AS total
                FROM transactions t
                INNER JOIN statements s
                    ON t.statement_id = s.statement_id
                WHERE s.user_id = %s
                GROUP BY t.transaction_type
                """,
                (
                    current_user_id,
                )
            )

        transaction_types = cursor.fetchall()

        for item in transaction_types:

            item["count"] = int(
                item["count"] or 0
            )

            item["total"] = float(
                item["total"] or 0
            )

        # ====================================================
        # CATEGORY PERCENTAGE
        # ====================================================

        if statement_id is not None:

            cursor.execute(
                """
                SELECT
                    category,
                    SUM(amount) AS total_amount
                FROM transactions
                WHERE transaction_type = 'DEBIT'
                AND statement_id = %s
                GROUP BY category
                ORDER BY total_amount DESC
                """,
                (
                    statement_id,
                )
            )

        else:

            cursor.execute(
                """
                SELECT
                    t.category,
                    SUM(t.amount) AS total_amount
                FROM transactions t
                INNER JOIN statements s
                    ON t.statement_id = s.statement_id
                WHERE t.transaction_type = 'DEBIT'
                AND s.user_id = %s
                GROUP BY t.category
                ORDER BY total_amount DESC
                """,
                (
                    current_user_id,
                )
            )

        categories = cursor.fetchall()

        total_expense = sum(
            float(
                item["total_amount"] or 0
            )
            for item in categories
        )

        for item in categories:

            amount = float(
                item["total_amount"] or 0
            )

            item["total_amount"] = amount

            item["percentage"] = round(
                (
                    amount /
                    total_expense *
                    100
                )
                if total_expense > 0
                else 0,
                2
            )

        # ====================================================
        # DAILY SPENDING
        # ====================================================

        if statement_id is not None:

            cursor.execute(
                """
                SELECT
                    DATE_FORMAT(
                        transaction_date,
                        '%Y-%m-%d'
                    ) AS date,

                    SUM(amount)
                    AS total_expense

                FROM transactions

                WHERE transaction_type = 'DEBIT'
                AND statement_id = %s

                GROUP BY transaction_date

                ORDER BY date
                """,
                (
                    statement_id,
                )
            )

        else:

            cursor.execute(
                """
                SELECT
                    DATE_FORMAT(
                        t.transaction_date,
                        '%Y-%m-%d'
                    ) AS date,

                    SUM(t.amount)
                    AS total_expense

                FROM transactions t

                INNER JOIN statements s
                    ON t.statement_id = s.statement_id

                WHERE t.transaction_type = 'DEBIT'
                AND s.user_id = %s

                GROUP BY t.transaction_date

                ORDER BY date
                """,
                (
                    current_user_id,
                )
            )

        daily_spending = cursor.fetchall()

        for item in daily_spending:

            item["total_expense"] = float(
                item["total_expense"] or 0
            )

        return {

            "success": True,

            "monthly":
                monthly,

            "top_expenses":
                top_expenses,

            "transaction_types":
                transaction_types,

            "categories":
                categories,

            "daily_spending":
                daily_spending
        }

    finally:

        cursor.close()
        db.close()


# ============================================================
# SPENDING TREND ANALYSIS
# ============================================================

@app.get("/spending-trends")
def spending_trends(
    statement_id: int | None = Query(default=None),
    current_user_id: int = Depends(get_current_user)
):

    db = get_connection()

    cursor = db.cursor(
        dictionary=True
    )

    try:

        if statement_id is not None:

            statement = verify_statement(
                cursor,
                statement_id,
                current_user_id
            )

            if not statement:

                raise HTTPException(
                    status_code=404,
                    detail="Statement not found."
                )

            cursor.execute(
                """
                SELECT
                    DATE_FORMAT(
                        transaction_date,
                        '%Y-%m'
                    ) AS month,

                    SUM(amount) AS spending

                FROM transactions

                WHERE transaction_type = 'DEBIT'
                AND statement_id = %s

                GROUP BY
                    DATE_FORMAT(
                        transaction_date,
                        '%Y-%m'
                    )

                ORDER BY month
                """,
                (
                    statement_id,
                )
            )

        else:

            cursor.execute(
                """
                SELECT
                    DATE_FORMAT(
                        t.transaction_date,
                        '%Y-%m'
                    ) AS month,

                    SUM(t.amount) AS spending

                FROM transactions t

                INNER JOIN statements s
                    ON t.statement_id = s.statement_id

                WHERE t.transaction_type = 'DEBIT'
                AND s.user_id = %s

                GROUP BY
                    DATE_FORMAT(
                        t.transaction_date,
                        '%Y-%m'
                    )

                ORDER BY month
                """,
                (
                    current_user_id,
                )
            )

        monthly_data = cursor.fetchall()

        for item in monthly_data:

            item["spending"] = float(
                item["spending"] or 0
            )

        # ====================================================
        # TREND
        # ====================================================

        if len(monthly_data) < 2:

            trend = "Insufficient data"

            percentage_change = 0

        else:

            previous = (
                monthly_data[-2]["spending"]
            )

            current = (
                monthly_data[-1]["spending"]
            )

            if previous > 0:

                percentage_change = (
                    (
                        current - previous
                    )
                    / previous
                ) * 100

            else:

                percentage_change = 0

            if percentage_change > 10:

                trend = "Increasing"

            elif percentage_change < -10:

                trend = "Decreasing"

            else:

                trend = "Stable"

        # ====================================================
        # AVERAGE
        # ====================================================

        if monthly_data:

            total_spending = sum(
                item["spending"]
                for item in monthly_data
            )

            average_monthly_spending = (
                total_spending
                / len(monthly_data)
            )

        else:

            average_monthly_spending = 0

        return {

            "success": True,

            "trend":
                trend,

            "percentage_change":
                round(
                    percentage_change,
                    2
                ),

            "average_monthly_spending":
                round(
                    average_monthly_spending,
                    2
                ),

            "monthly_data":
                monthly_data
        }

    finally:

        cursor.close()
        db.close()


# ============================================================
# UNUSUAL TRANSACTIONS
# ============================================================

@app.get("/unusual-transactions")
def unusual_transactions(
    statement_id: int | None = Query(default=None),
    current_user_id: int = Depends(get_current_user)
):

    db = get_connection()

    cursor = db.cursor(
        dictionary=True
    )

    try:

        if statement_id is not None:

            statement = verify_statement(
                cursor,
                statement_id,
                current_user_id
            )

            if not statement:

                raise HTTPException(
                    status_code=404,
                    detail="Statement not found."
                )

            cursor.execute(
                """
                SELECT
                    AVG(amount) AS average_expense
                FROM transactions
                WHERE transaction_type = 'DEBIT'
                AND statement_id = %s
                """,
                (
                    statement_id,
                )
            )

        else:

            cursor.execute(
                """
                SELECT
                    AVG(t.amount) AS average_expense
                FROM transactions t
                INNER JOIN statements s
                    ON t.statement_id = s.statement_id
                WHERE t.transaction_type = 'DEBIT'
                AND s.user_id = %s
                """,
                (
                    current_user_id,
                )
            )

        result = cursor.fetchone()

        average_expense = float(
            result["average_expense"] or 0
        )

        threshold = (
            average_expense * 2
        )

        # ====================================================
        # FIND UNUSUAL TRANSACTIONS
        # ====================================================

        if statement_id is not None:

            cursor.execute(
                """
                SELECT
                    transaction_id,
                    statement_id,
                    transaction_date,
                    description,
                    amount,
                    category
                FROM transactions
                WHERE transaction_type = 'DEBIT'
                AND statement_id = %s
                AND amount >= %s
                ORDER BY amount DESC
                """,
                (
                    statement_id,
                    threshold
                )
            )

        else:

            cursor.execute(
                """
                SELECT
                    t.transaction_id,
                    t.statement_id,
                    t.transaction_date,
                    t.description,
                    t.amount,
                    t.category
                FROM transactions t
                INNER JOIN statements s
                    ON t.statement_id = s.statement_id
                WHERE t.transaction_type = 'DEBIT'
                AND s.user_id = %s
                AND t.amount >= %s
                ORDER BY t.amount DESC
                """,
                (
                    current_user_id,
                    threshold
                )
            )

        transactions = cursor.fetchall()

        for transaction in transactions:

            transaction["amount"] = float(
                transaction["amount"] or 0
            )

            if transaction["transaction_date"]:

                transaction["transaction_date"] = (
                    transaction[
                        "transaction_date"
                    ].isoformat()
                )

        return {

            "success": True,

            "average_expense":
                round(
                    average_expense,
                    2
                ),

            "unusual_threshold":
                round(
                    threshold,
                    2
                ),

            "unusual_transaction_count":
                len(transactions),

            "transactions":
                transactions
        }

    finally:

        cursor.close()
        db.close()


# ============================================================
# CATEGORY ANALYSIS
# ============================================================

@app.get("/category-analysis")
def category_analysis(
    statement_id: int | None = Query(default=None),
    current_user_id: int = Depends(get_current_user)
):

    db = get_connection()

    cursor = db.cursor(
        dictionary=True
    )

    try:

        if statement_id is not None:

            statement = verify_statement(
                cursor,
                statement_id,
                current_user_id
            )

            if not statement:

                raise HTTPException(
                    status_code=404,
                    detail="Statement not found."
                )

            cursor.execute(
                """
                SELECT
                    category,
                    COUNT(*) AS transaction_count,
                    SUM(amount) AS total_amount,
                    AVG(amount) AS average_amount,
                    MAX(amount) AS highest_amount

                FROM transactions

                WHERE transaction_type = 'DEBIT'
                AND statement_id = %s

                GROUP BY category

                ORDER BY total_amount DESC
                """,
                (
                    statement_id,
                )
            )

        else:

            cursor.execute(
                """
                SELECT
                    t.category,
                    COUNT(*) AS transaction_count,
                    SUM(t.amount) AS total_amount,
                    AVG(t.amount) AS average_amount,
                    MAX(t.amount) AS highest_amount

                FROM transactions t

                INNER JOIN statements s
                    ON t.statement_id = s.statement_id

                WHERE t.transaction_type = 'DEBIT'
                AND s.user_id = %s

                GROUP BY t.category

                ORDER BY total_amount DESC
                """,
                (
                    current_user_id,
                )
            )

        categories = cursor.fetchall()

        # ====================================================
        # TOTAL EXPENSE
        # ====================================================

        total_expense = sum(
            float(
                item["total_amount"] or 0
            )
            for item in categories
        )

        # ====================================================
        # PROCESS
        # ====================================================

        for item in categories:

            total_amount = float(
                item["total_amount"] or 0
            )

            item["transaction_count"] = int(
                item["transaction_count"] or 0
            )

            item["total_amount"] = (
                total_amount
            )

            item["average_amount"] = float(
                item["average_amount"] or 0
            )

            item["highest_amount"] = float(
                item["highest_amount"] or 0
            )

            if total_expense > 0:

                item["percentage"] = round(
                    (
                        total_amount
                        / total_expense
                    ) * 100,
                    2
                )

            else:

                item["percentage"] = 0

        # ====================================================
        # TOP CATEGORY
        # ====================================================

        if categories:

            top_category = categories[0]

        else:

            top_category = None

        return {

            "success": True,

            "total_expense":
                round(
                    total_expense,
                    2
                ),

            "top_category":
                (
                    top_category["category"]
                    if top_category
                    else "N/A"
                ),

            "top_category_amount":
                (
                    top_category["total_amount"]
                    if top_category
                    else 0
                ),

            "categories":
                categories
        }

    finally:

        cursor.close()
        db.close()
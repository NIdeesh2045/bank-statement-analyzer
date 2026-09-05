# ============================================================
# AUTHENTICATION
# ============================================================
from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer


# ------------------------------------------------------------
# JWT CONFIGURATION
# ------------------------------------------------------------

SECRET_KEY = "CHANGE_THIS_TO_A_RANDOM_SECRET_KEY"

ALGORITHM = "HS256"

ACCESS_TOKEN_EXPIRE_MINUTES = 60

# ============================================================
# OAUTH2 CONFIGURATION
# ============================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="token"
)

# ------------------------------------------------------------
# PASSWORD HASHING
# ------------------------------------------------------------

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto"
)


def hash_password(password: str) -> str:
    """
    Hash a user's password.
    """

    return pwd_context.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    """
    Verify a plain password against its hashed version.
    """

    return pwd_context.verify(
        plain_password,
        hashed_password
    )


# ------------------------------------------------------------
# CREATE JWT TOKEN
# ------------------------------------------------------------

def create_access_token(
    user_id: int
) -> str:
    """
    Create JWT access token for a user.
    """

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "exp": expire
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


# ------------------------------------------------------------
# DECODE JWT TOKEN
# ------------------------------------------------------------

def decode_access_token(
    token: str
):
    """
    Decode JWT token and return user ID.
    """

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            return None

        return int(user_id)

    except (JWTError, ValueError):
        return None
    
# ============================================================
# GET CURRENT USER
# ============================================================

def get_current_user(
    token: str = Depends(oauth2_scheme)
):
    """
    Get user ID from JWT token.
    """

    user_id = decode_access_token(token)

    if user_id is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token."
        )

    return user_id
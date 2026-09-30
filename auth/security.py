import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from pwdlib import PasswordHash


# Load values from the .env file.
load_dotenv()


# Argon2 is used to securely hash passwords.
password_hasher = PasswordHash.recommended()


JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
JWT_ALGORITHM = os.getenv(
    "JWT_ALGORITHM",
    "HS256"
)

JWT_EXPIRE_MINUTES = int(
    os.getenv(
        "JWT_EXPIRE_MINUTES",
        "60"
    )
)


if not JWT_SECRET_KEY:
    raise RuntimeError(
        "JWT_SECRET_KEY is missing from .env"
    )


def hash_password(
    password: str
) -> str:
    """
    Convert a plain password into a secure hash.
    The plain password is never stored in the database.
    """

    return password_hasher.hash(
        password
    )


def verify_password(
    plain_password: str,
    password_hash: str
) -> bool:
    """
    Check whether the entered password matches
    the stored password hash.
    """

    return password_hasher.verify(
        plain_password,
        password_hash
    )


def create_access_token(
    user_id: int,
    email: str
) -> str:
    """
    Create a signed JWT for an authenticated user.
    """

    expire_time = (
        datetime.now(timezone.utc)
        + timedelta(
            minutes=JWT_EXPIRE_MINUTES
        )
    )

    payload = {
        "sub": str(user_id),
        "email": email,
        "exp": expire_time
    }

    return jwt.encode(
        payload,
        JWT_SECRET_KEY,
        algorithm=JWT_ALGORITHM
    )


def decode_access_token(
    token: str
):
    """
    Validate and decode a JWT.
    Returns None if the token is invalid or expired.
    """

    try:
        return jwt.decode(
            token,
            JWT_SECRET_KEY,
            algorithms=[
                JWT_ALGORITHM
            ]
        )

    except jwt.InvalidTokenError:
        return None
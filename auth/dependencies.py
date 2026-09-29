from fastapi import (
    HTTPException,
    Request,
    status
)

from auth.security import (
    decode_access_token
)

from database.user_repository import (
    UserRepository
)


user_repository = UserRepository()


def get_authenticated_user(
    request: Request
):
    """
    Read the JWT from the HttpOnly cookie,
    validate it, and return the authenticated user.
    """

    # ---------------------------------------------
    # Read JWT cookie
    # ---------------------------------------------

    token = request.cookies.get(
        "access_token"
    )

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated."
        )


    # ---------------------------------------------
    # Decode and verify JWT
    # ---------------------------------------------

    payload = decode_access_token(
        token
    )

    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Invalid or expired "
                "authentication token."
            )
        )


    # ---------------------------------------------
    # Read user ID from JWT
    # ---------------------------------------------

    try:
        user_id = int(
            payload["sub"]
        )

    except (
        KeyError,
        TypeError,
        ValueError
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token."
        )


    # ---------------------------------------------
    # Get actual user from SQL Server
    # ---------------------------------------------

    user = (
        user_repository.get_user_by_id(
            user_id
        )
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account not found."
        )


    return user
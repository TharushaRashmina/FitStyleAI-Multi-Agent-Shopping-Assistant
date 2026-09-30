from fastapi import (
    APIRouter,
    HTTPException,
    Request,
    Response,
    status
)

from pydantic import (
    BaseModel,
    EmailStr,
    Field
)

from auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    decode_access_token
)

from database.user_repository import (
    UserRepository
)


# -------------------------------------------------
# Authentication Router
# -------------------------------------------------

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


user_repository = UserRepository()


# -------------------------------------------------
# Register Request Model
# -------------------------------------------------

class RegisterRequest(BaseModel):

    name: str = Field(
        ...,
        min_length=2,
        max_length=100
    )

    email: EmailStr

    password: str = Field(
        ...,
        min_length=8,
        max_length=128
    )


# -------------------------------------------------
# Login Request Model
# -------------------------------------------------

class LoginRequest(BaseModel):

    email: EmailStr

    password: str = Field(
        ...,
        min_length=8,
        max_length=128
    )


# -------------------------------------------------
# Register Endpoint
# -------------------------------------------------

@router.post(
    "/register",
    status_code=status.HTTP_201_CREATED
)
def register_user(
    request: RegisterRequest
):

    name = request.name.strip()

    email = (
        str(request.email)
        .strip()
        .lower()
    )


    existing_user = (
        user_repository.get_user_by_email(
            email
        )
    )

    if existing_user:

        raise HTTPException(
            status_code=409,
            detail=(
                "An account with this email "
                "already exists."
            )
        )


    password_hash = hash_password(
        request.password
    )


    new_user = (
        user_repository.create_user(
            name=name,
            email=email,
            password_hash=password_hash
        )
    )


    return {
        "status": "success",

        "message":
            "Account created successfully.",

        "user": {
            "user_id":
                new_user["user_id"],

            "name":
                new_user["name"],

            "email":
                new_user["email"],

            "created_at":
                new_user["created_at"]
        }
    }


# -------------------------------------------------
# Login Endpoint
# -------------------------------------------------

@router.post(
    "/login"
)
def login_user(
    request: LoginRequest,
    response: Response
):

    email = (
        str(request.email)
        .strip()
        .lower()
    )


    user = (
        user_repository.get_user_by_email(
            email
        )
    )


    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password."
        )


    password_is_valid = verify_password(
        request.password,
        user["password_hash"]
    )


    if not password_is_valid:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password."
        )


    access_token = create_access_token(
        user_id=user["user_id"],
        email=user["email"]
    )


    # Store JWT in an HttpOnly cookie.
    response.set_cookie(
        key="access_token",
        value=access_token,

        httponly=True,

        # False is correct for localhost development.
        # Production HTTPS should use secure=True.
        secure=False,

        samesite="lax",

        max_age=60 * 60
    )


    return {
        "status": "success",

        "message":
            "Login successful.",

        "user": {
            "user_id":
                user["user_id"],

            "name":
                user["name"],

            "email":
                user["email"]
        }
    }


# -------------------------------------------------
# Get Current Logged-in User
# -------------------------------------------------

@router.get(
    "/me"
)
def get_current_user(
    request: Request
):

    # ---------------------------------------------
    # Read JWT from browser cookie
    # ---------------------------------------------

    token = request.cookies.get(
        "access_token"
    )


    if not token:

        raise HTTPException(
            status_code=401,
            detail="Not authenticated."
        )


    # ---------------------------------------------
    # Verify and decode JWT
    # ---------------------------------------------

    payload = decode_access_token(
        token
    )


    if not payload:

        raise HTTPException(
            status_code=401,
            detail=(
                "Invalid or expired "
                "authentication token."
            )
        )


    # ---------------------------------------------
    # Get user ID from JWT
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
            status_code=401,
            detail="Invalid authentication token."
        )


    # ---------------------------------------------
    # Find user in SQL Server
    # ---------------------------------------------

    user = (
        user_repository.get_user_by_id(
            user_id
        )
    )


    if not user:

        raise HTTPException(
            status_code=401,
            detail="User account not found."
        )


    # Never return password_hash.
    return {
        "status": "success",

        "user": {
            "user_id":
                user["user_id"],

            "name":
                user["name"],

            "email":
                user["email"],

            "created_at":
                user["created_at"]
        }
    }


# -------------------------------------------------
# Logout Endpoint
# -------------------------------------------------

@router.post(
    "/logout"
)
def logout_user(
    response: Response
):

    # Remove the JWT authentication cookie.
    response.delete_cookie(
        key="access_token",

        httponly=True,

        # Localhost development.
        secure=False,

        samesite="lax"
    )


    return {
        "status": "success",
        "message": "Logout successful."
    }
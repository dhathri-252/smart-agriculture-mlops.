"""Authentication endpoints: register, login, profile (stdlib-only security)."""

from fastapi import APIRouter, Depends, HTTPException

from api import db
from api.deps import required_user, optional_user
from api.schemas import (
    AuthResponse,
    LoginRequest,
    ProfileUpdateRequest,
    RegisterRequest,
    UserOut,
)
from api.security import create_token, hash_password, verify_password

router = APIRouter(prefix="/api/auth")


def _issue_token(user: dict) -> dict:
    token = create_token({"sub": user["id"], "username": user["username"]})
    return {
        "token": token,
        "token_type": "bearer",
        "user": {k: v for k, v in user.items() if k != "password_hash"},
    }


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=201,
    tags=["Auth"],
    summary="Register a farmer account",
    description=(
        "Creates an account with a PBKDF2-hashed password (plain-text passwords "
        "are never stored) and returns a signed session token."
    ),
)
def register(payload: RegisterRequest):
    if db.get_user_by_username(payload.username) is not None:
        raise HTTPException(status_code=409, detail="Username is already taken.")
    stored = hash_password(payload.password)
    user = db.create_user(payload.username, stored)
    if payload.farm_name or payload.location:
        user = db.update_profile(user["id"], payload.farm_name, payload.location)
    return _issue_token(user)


@router.post(
    "/login",
    response_model=AuthResponse,
    tags=["Auth"],
    summary="Log in",
    description="Verifies credentials and returns a signed session token.",
)
def login(payload: LoginRequest):
    user = db.get_user_by_username(payload.username)
    if user is None or not verify_password(payload.password, user["password_hash"]):
        # Same message for unknown user and wrong password (no user enumeration).
        raise HTTPException(status_code=401, detail="Invalid username or password.")
    return _issue_token(user)


@router.get(
    "/me",
    response_model=UserOut,
    tags=["Auth"],
    summary="Current user",
    description="Returns the profile of the authenticated user.",
)
def me(user=Depends(required_user)):
    return user


@router.put(
    "/profile",
    response_model=UserOut,
    tags=["Auth"],
    summary="Update farmer profile",
    description="Updates the basic farmer profile (farm name and location).",
)
def update_profile(payload: ProfileUpdateRequest, user=Depends(required_user)):
    updated = db.update_profile(user["id"], payload.farm_name, payload.location)
    if updated is None:
        raise HTTPException(status_code=404, detail="User not found.")
    return updated


@router.post(
    "/logout",
    tags=["Auth"],
    summary="Log out",
    description=(
        "Confirms logout. Tokens are stateless — the client discards the token. "
        "Tokens expire automatically after AUTH_TOKEN_TTL_SECONDS."
    ),
)
def logout(user=Depends(optional_user)):
    return {"detail": "Logged out."}

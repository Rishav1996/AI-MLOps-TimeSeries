"""Pydantic request models for the API."""
from pydantic import BaseModel
from typing import Optional


class UserTable(BaseModel):
    """Signup/login request body (id is populated server-side)."""
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    user_password: Optional[str] = None

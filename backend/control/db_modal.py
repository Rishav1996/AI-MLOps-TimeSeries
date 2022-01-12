from pydantic import BaseModel
from typing import Optional


class UserTable(BaseModel):
    user_id: Optional[int] = None
    user_name: Optional[str] = None
    user_password: Optional[str] = None

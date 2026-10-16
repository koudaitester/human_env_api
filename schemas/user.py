from pydantic import BaseModel

class UserCreate(BaseModel):
    username: str
    password: str
    nickname: str | None = None

class UserOut(BaseModel):
    id: int
    username: str
    nickname: str | None
    is_active: bool
    class Config:
        from_attributes = True

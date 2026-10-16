# routers/user_router.py
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from schemas.user import UserCreate, UserOut
from services.user_service import authenticate_user, create_user, get_user_by_username
from utils.security import create_access_token
from datetime import timedelta

ACCESS_TOKEN_EXPIRE_MINUTES = 120

router = APIRouter()

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="账号或密码错误")
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(data={"sub": user["username"]}, expires_delta=access_token_expires)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/register", response_model=UserOut)
async def register(user_in: UserCreate):
    exist = get_user_by_username(user_in.username)
    if exist:
        raise HTTPException(status_code=400, detail="用户名已存在")
    return create_user(user_in.username, user_in.password, user_in.nickname)

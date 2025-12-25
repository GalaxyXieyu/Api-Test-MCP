"""FastAPI 示例应用"""
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="计算器 API", docs_url="/docs", redoc_url="/redoc")


class CalcRequest(BaseModel):
    a: float
    b: float


class CalcResponse(BaseModel):
    result: float
    operation: str


class User(BaseModel):
    id: int
    name: str
    email: Optional[str] = None


# 内存数据库
users_db = [
    {"id": 1, "name": "张三", "email": "zhangsan@example.com"},
    {"id": 2, "name": "李四", "email": None},
]


@app.get("/")
async def root():
    return {"message": "欢迎使用计算器 API"}


@app.post("/add", response_model=CalcResponse)
async def add(request: CalcRequest):
    """加法运算"""
    return CalcResponse(result=request.a + request.b, operation="add")


@app.post("/subtract", response_model=CalcResponse)
async def subtract(request: CalcRequest):
    """减法运算"""
    return CalcResponse(result=request.a - request.b, operation="subtract")


@app.get("/users", response_model=List[User])
async def get_users():
    """获取用户列表"""
    return users_db


@app.get("/users/{user_id}", response_model=User)
async def get_user(user_id: int):
    """获取单个用户"""
    for user in users_db:
        if user["id"] == user_id:
            return user
    raise HTTPException(status_code=404, detail="User not found")


@app.get("/health")
async def health():
    """健康检查"""
    return {"status": "healthy"}

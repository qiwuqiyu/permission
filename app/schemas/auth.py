# 登录接口的请求体
from pydantic import BaseModel


# 前端登录页 POST 过来的 JSON：{ "username": "xxx", "password": "xxx" }
class LoginRequest(BaseModel):
    username: str
    password: str

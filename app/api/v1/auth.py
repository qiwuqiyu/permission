# ============================================================================
# 登录接口（原 main.py 第 6 节）
# 单独一个文件：它不属于任何一张表的 CRUD，语义上是「认证」，将来加注册/改密码都放这
# ============================================================================
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models import DBUser
from app.schemas.auth import LoginRequest

# 登录接口路径是 /login，不带资源前缀，所以这里不设 prefix
router = APIRouter(tags=["登录"])


# ---- 登录 POST /login ----
# 前端 axios: request.post('/login', { username, password })
# 类比前端：登录页点击“登录”按钮调用的接口
@router.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    # 用用户名 + 密码去数据库里找（demo 直接比对明文密码，真实项目要用哈希）
    db_user = (
        db.query(DBUser)
        .filter(DBUser.username == data.username, DBUser.password == data.password)
        .first()
    )
    if db_user is None:
        # 401 = 未认证：账号或密码不对，前端会走 catch，提示“用户名或密码错误”
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    # 登录成功：发一个令牌(token)给前端保存（demo 用简单字符串；真实项目用 JWT）
    # 前端拿到 token 存进 localStorage，之后的请求都带上它证明“我已登录”
    return {"token": f"token-{db_user.id}-{db_user.username}", "username": db_user.username}

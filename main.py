# ============================================================================
# 应用入口 —— 拆包之后 main.py 只干三件事：建 app、挂中间件、注册路由
# ----------------------------------------------------------------------------
# 启动命令完全没变：
#   uvicorn main:app --reload --host 127.0.0.1 --port 8000
#
# 原来这 599 行的内容都搬去哪了（按原来的顺序）：
#   第 1 节 数据库配置 / engine / SessionLocal  -> app/core/config.py + app/db/session.py
#   第 2 节 5 个表模型                          -> app/models/
#   第 1.5 节 建表 + 迁移 + 种子数据              -> app/db/init_db.py
#   第 3 节 Pydantic 出入参模型                  -> app/schemas/
#   第 4 节 app 实例 + CORS + get_db            -> 本文件 + app/core/deps.py
#   第 5~8 节 20 个接口                          -> app/api/v1/
#   中间那 5 个拼装/校验辅助函数                   -> app/services/
#
# ⚠️ 命名提醒：`app` 是包名（本文件顶部那些 import 用的），
#   `app = FastAPI()` 是实例名，两者同名。因为所有 from app.xxx import 都在这行
#   之前执行完，所以不会出错，但别在这行之后写 app.models.xxx —— 那时 app 已经是
#   FastAPI 实例了。嫌绕的话可以把包改名 backend/，代价是全部 import 要跟着改。
# ============================================================================
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.db.init_db import init_db


@asynccontextmanager
async def lifespan(application: FastAPI):
    # yield 之前 = 应用启动时执行；yield 之后 = 应用关闭时执行
    # 建库建表 + 灌种子数据放在这里，而不是写在模块顶层：
    # 写在顶层的话，任何人 import 一下（跑测试、跑脚本、代码提示工具扫描）都会触发建库
    init_db()
    yield


# app = 后端应用实例（类比：const app = createApp(App)）
app = FastAPI(title="用户CRUD接口", lifespan=lifespan)

# CORS 跨域中间件 —— 前端最常见的报错 "CORS policy" 就是它解决的
# 浏览器安全策略：默认禁止 localhost:5173 的页面请求 localhost:8000 的接口
# 这里相当于后端"主动放行"，告诉浏览器：这些来源/方法/请求头我都允许
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许任何前端地址访问（开发环境方便；上线必须改成具体域名，不能写*）
    allow_credentials=True,  # 允许携带 cookie 等凭证
    allow_methods=["*"],    # 允许所有 HTTP 方法（GET/POST/PUT/PATCH/DELETE...）
    allow_headers=["*"],     # 允许所有请求头（比如 axios 默认的 Content-Type 等）
)

# 注册路由：所有接口都在 app/api/ 下面，这里只挂一个汇总 router
# 类比：app.use(router)，路由表本身在别处定义
app.include_router(api_router)

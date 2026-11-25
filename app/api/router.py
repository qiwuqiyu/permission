# ============================================================================
# 路由汇总表 —— 把各资源的 router 装进一个 api_router
# ----------------------------------------------------------------------------
# 为什么多这一层：main.py 就只需要 include_router(api_router) 一行，
# 以后加 /depts、/logs 只改这个文件，main.py 再也不动。
# 将来要做接口版本管理（v1 稳定、v2 试验）也是在这里加前缀：
#   api_router.include_router(v2_router, prefix="/v2")
# ============================================================================
from fastapi import APIRouter

from app.api.v1 import auth, menus, roles, users

api_router = APIRouter()

# include_router 是「把别的 router 上的路由复制过来」，不是嵌套目录，
# 所以最终路径 = 各 router 自己的 prefix + 函数上的路径（/users、/roles/{id}/menus ...）
api_router.include_router(users.router)
api_router.include_router(menus.router)
api_router.include_router(roles.router)
api_router.include_router(auth.router)

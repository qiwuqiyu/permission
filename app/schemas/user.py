# 用户接口的"出入参类型定义"
# ----------------------------------------------------------------------------
# 类比 TypeScript 的 interface / type，但 Pydantic 会「运行时」真正校验：
# 前端传来的 JSON 如果缺字段或类型不对，框架自动返回 422 错误，不会进入函数体
# 注意这一层只描述数据形状，不 import 任何 ORM 模型（保持"接口契约"与"表结构"解耦）
from pydantic import BaseModel, ConfigDict


# 请求体模型：新增用户时前端要 POST 过来的 JSON 结构
# { "username": "xxx", "password": "xxx", "email": "xxx", "role_ids": [1] }
class UserCreate(BaseModel):
    username: str   # 必填，必须是字符串
    password: str   # 必填，必须是字符串
    email: str      # 必填，必须是字符串
    # 所属角色 id 列表（不是单个 role_id）：空数组 = 一个角色都没分配
    role_ids: list[int] = []


# 局部更新模型：PATCH 时允许只传想改的字段（其他字段不传就保持原样）
# `str | None = None` 相当于 TS 的 `username?: string`，不传就是 undefined
class UserUpdate(BaseModel):
    username: str | None = None
    password: str | None = None
    email: str | None = None
    # 这里用 `| None = None` 而不是直接给 []，是为了区分两种完全不同的意图：
    # None = 这次没动角色（保持原样）；[] = 明确要把角色全部清空
    role_ids: list[int] | None = None


# 响应模型：后端返回给前端的用户数据结构（在 UserCreate 基础上多了 id）
class User(UserCreate):
    id: int  # 数据库生成的自增ID
    # Pydantic v2 写法：允许直接从数据库对象(DBUser)上读取属性来组装 JSON
    # （v1 的旧写法叫 orm_mode=True，改名了而已，作用相同）
    # 注：role_ids 不存在 users 表上，要靠 services/user_role.py 手工从
    #     user_roles 查出来填，所以 from_attributes 只能自动带出 username/email 这几列
    model_config = ConfigDict(from_attributes=True)

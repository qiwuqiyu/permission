# 角色接口的出入参模型（第三遍写这个套路了：模型 -> 接口 -> 页面，已经完全流程化）
from pydantic import BaseModel, ConfigDict


# 新增角色时前端 POST 过来的 JSON：{ "name": "xx", "description": "xx" }
class RoleCreate(BaseModel):
    name: str             # 角色名，必填
    description: str = ""  # 角色描述，不传默认空字符串（相当于 TS 的 description?: string）


class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


# 角色响应模型（多了 id）
class Role(RoleCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)


# 给角色分配菜单的请求体：{ "menu_ids": [1, 3] }
# 语义是「全量覆盖」：传什么就是最终结果，传空数组 = 取消该角色全部菜单授权
class RoleMenuAssign(BaseModel):
    menu_ids: list[int] = []


# 角色列表的响应模型：在 Role 基础上带上已授权的菜单
# 这样前端拉一次 /roles 就能同时拿到表格展示 + 弹窗回显所需的数据，不用再单独查
class RoleWithMenus(Role):
    menu_ids: list[int] = []     # 已授权菜单 id，用于弹窗勾选回显
    menu_names: list[str] = []   # 已授权菜单名，用于表格直接展示

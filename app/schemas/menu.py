# 菜单接口的出入参模型（结构比用户简单，套路完全一样）
from pydantic import BaseModel, ConfigDict


# 新增菜单时前端 POST 过来的 JSON：{ "name": "xx", "path": "/xx", "sort": 1 }
class MenuCreate(BaseModel):
    name: str       # 菜单显示名，必填
    path: str       # 前端路由地址，必填（如 /users）
    sort: int = 0   # 排序号，不传默认为 0（相当于 TS 的 sort?: number）


class MenuUpdate(BaseModel):
    name: str | None = None
    path: str | None = None
    sort: int | None = None


# 菜单响应模型（多了 id，供前端表格渲染 :key 用）
class Menu(MenuCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)

# 角色表：RBAC 权限模型经典三件套（用户-角色-权限）里的“角色”这一环
# 类比：给用户打标签分组，比如“管理员”能看所有菜单，“普通用户”只能看一部分
from sqlalchemy import Column, Integer, String

from app.db.base import Base


class DBRole(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)     # 角色ID，自动编号
    name = Column(String(50), unique=True, index=True)     # 角色名，如“管理员”，不能重复
    description = Column(String(200))                      # 角色描述，备注用

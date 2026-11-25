# 两张「中间表」：多对多关系专用
# ----------------------------------------------------------------------------
# 多对多关系没法靠“在某一边加一列”解决，必须单独建一张表，里面只放两个外键。
# 两张表结构完全对称，放同一个文件里方便对照：
#   user_roles  决定「某个用户拥有哪些角色」
#   role_menus  决定「某个角色能访问哪些菜单」
# 至此就是教科书上的经典 RBAC 五表：users / roles / menus / user_roles / role_menus
#
# 为什么单独一个文件：如果 user.py 想引用 DBUserRole、association.py 又想引用 DBUser，
# 两边互相 import 就会形成循环导入。把中间表单独放一处，依赖方向永远是
# 「具体模型 -> 中间表」，不会绕回来。
from sqlalchemy import Column, ForeignKey, Integer

from app.db.base import Base


class DBUserRole(Base):
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True, index=True)             # 关联记录ID
    user_id = Column(Integer, ForeignKey("users.id"), index=True)  # 哪个用户
    role_id = Column(Integer, ForeignKey("roles.id"), index=True)  # 拥有哪个角色


class DBRoleMenu(Base):
    __tablename__ = "role_menus"

    id = Column(Integer, primary_key=True, index=True)             # 关联记录ID
    role_id = Column(Integer, ForeignKey("roles.id"), index=True)  # 哪个角色
    menu_id = Column(Integer, ForeignKey("menus.id"), index=True)  # 能访问哪个菜单

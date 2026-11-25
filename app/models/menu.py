# 菜单表：存左侧导航栏的菜单项 —— “菜单管理”页面增删改的就是这张表
# 类比：以前菜单是硬编码在 Layout.vue 里的数组，现在搬进数据库，改数据就能改导航
from sqlalchemy import Column, Integer, String

from app.db.base import Base


class DBMenu(Base):
    __tablename__ = "menus"

    id = Column(Integer, primary_key=True, index=True)      # 菜单ID，自动编号
    name = Column(String(50), index=True)                   # 菜单显示名，如“用户管理”
    path = Column(String(100), unique=True, index=True)     # 前端路由地址，如 /users
    sort = Column(Integer, default=0)                       # 排序号，越小越靠前

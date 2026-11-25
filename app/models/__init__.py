# 表模型「点名」入口
# ----------------------------------------------------------------------------
# ⚠️ 这个文件不只是方便，它是必需的：
# create_all() 只会创建「已经被 Python 加载过」的模型对应的表。
# 只要 import app.models，5 个模型就都注册进了 Base.metadata；
# 漏掉某一行，那张表就不会被自动建出来（拆包后第二大坑）。
# noqa: F401 是告诉代码检查工具「这些 import 看起来没用到，但是故意的」。
from app.models.association import DBRoleMenu, DBUserRole  # noqa: F401
from app.models.menu import DBMenu  # noqa: F401
from app.models.role import DBRole  # noqa: F401
from app.models.user import DBUser  # noqa: F401

__all__ = ["DBUser", "DBMenu", "DBRole", "DBUserRole", "DBRoleMenu"]

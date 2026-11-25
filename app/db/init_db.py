# 启动初始化：建库 -> 建表 -> 灌种子数据
# ----------------------------------------------------------------------------
# 这些操作以前散在 main.py 的模块顶层（一 import 就执行），
# 现在集中成一个函数，由 main.py 的 lifespan 在「应用真正启动时」调用一次。
# 好处：跑测试 / 写脚本 import 到模型时不会顺手把库建了。
import app.models  # noqa: F401  ← 必须！import 包才会把 5 个模型注册进 Base.metadata

from app.db.base import Base
from app.db.session import SessionLocal, create_database_if_not_exists, engine
from app.models import DBMenu, DBRole


def create_tables() -> None:
    """建库 + 建表

    启动时自动建表（类似前端项目初始化时创建本地存储结构）：
    create_all 只在「表不存在」时创建，已存在的表不会被改动，所以反复启动是安全的。
    """
    create_database_if_not_exists()
    Base.metadata.create_all(bind=engine)


def seed_default_data() -> None:
    """首次运行时给菜单表、角色表灌默认数据（表里没数据才插，防止重复）

    类比：前端 mock 数据兜底，保证页面第一次打开不至于空白。
    三段都写成幂等的：判断条件不同，但目的都是「跑 N 次结果一样」。
    """
    with SessionLocal() as db:
        if db.query(DBMenu).count() == 0:
            db.add(DBMenu(name="用户管理", path="/users", sort=1))
            db.add(DBMenu(name="菜单管理", path="/menus", sort=2))
            db.commit()

    # 单独补「角色管理」菜单：按 path 判重（上面的 count==0 只在空表时触发，
    # 老库里已有两条菜单，不会再进那个分支，所以新页面的入口要这样幂等补上）
    with SessionLocal() as db:
        if db.query(DBMenu).filter(DBMenu.path == "/roles").first() is None:
            db.add(DBMenu(name="角色管理", path="/roles", sort=3))
            db.commit()

    # 角色表同样种两条默认数据（表里没数据才插）
    with SessionLocal() as db:
        if db.query(DBRole).count() == 0:
            db.add(DBRole(name="管理员", description="拥有全部权限"))
            db.add(DBRole(name="普通用户", description="基础查看权限"))
            db.commit()


def init_db() -> None:
    """应用启动时的完整初始化流程"""
    create_tables()
    seed_default_data()


# ---------------------------------------------------------------------------
# 关于原来那段「users.role_id -> user_roles 中间表」的轻量迁移代码：已删除。
# 它是一次性的（把旧列数据搬进中间表后 DROP COLUMN），现在库里 users 表
# 只剩 id/username/password/email 四列，说明迁移已经执行完毕，留着只会每次启动多查几轮。
# 以后再改表结构，正确工具是 Alembic（版本化迁移），而不是在启动流程里手写 DDL：
#   pip install alembic && alembic init migrations
#   alembic revision --autogenerate -m "add xxx" && alembic upgrade head
# ---------------------------------------------------------------------------

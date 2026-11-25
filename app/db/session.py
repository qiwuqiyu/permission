# engine / SessionLocal —— 程序和数据库打交道的「大门」
# ----------------------------------------------------------------------------
# 这里只负责「造好」，不负责「连上」：SQLAlchemy 是懒连接，
# 模块被 import 时并不会真的去连数据库。所以本文件没有任何副作用，
# 跑测试、写脚本随便 import 都安全（对比以前：建库语句就写在模块顶层）。
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# engine = 数据库连接池（和数据库打交道的“大门”）
# pool_pre_ping：用连接前先“探活”，闲置久了断掉的连接会自动重连
engine = create_engine(settings.database_url, pool_pre_ping=True)

# SessionLocal = "数据库会话工厂"，每次请求需要一个会话(Session)来读写数据
# autocommit=False: 不自动保存，代码里要显式 db.commit()（类似手动点"保存"按钮）
# autoflush=False: 不自动同步缓存，避免意外把未确认的数据写进数据库
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_database_if_not_exists() -> None:
    """把库先建出来（MySQL 和 SQLite 的一个区别：必须先“建库”才能连，SQLite 是自动建文件）

    用不指定库名的临时连接执行 CREATE DATABASE，建完就断开。
    这是「有副作用的操作」，所以做成函数由启动流程显式调用，而不是写在模块顶层。
    IF NOT EXISTS 保证幂等：库已存在时什么都不做，不会报错也不会清空数据。
    """
    pre_engine = create_engine(settings.server_url)
    with pre_engine.connect() as conn:
        conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {settings.mysql_database} CHARACTER SET utf8mb4"))
        conn.commit()
    pre_engine.dispose()

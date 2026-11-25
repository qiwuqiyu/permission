# 依赖注入集合 —— 接口函数签名里 Depends(...) 要用的东西都放这
from typing import Iterator

from sqlalchemy.orm import Session

from app.db.session import SessionLocal


def get_db() -> Iterator[Session]:
    """获取数据库会话 —— 每次接口请求都会执行一次

    类比：每个请求进来先"打开数据库连接"，用完自动关闭，防止连接泄漏。
    这是个生成器（用了 yield），FastAPI 会把 yield 出来的值注入给接口函数，
    请求结束后再回来执行 finally。
    """
    db = SessionLocal()          # 打开一个数据库会话
    try:
        yield db                 # 把会话交给接口函数使用（yield = 暂停在这里，请求结束后回来继续）
    finally:
        db.close()               # 无论成功还是报错，最后都关闭会话（finally 保证一定执行）

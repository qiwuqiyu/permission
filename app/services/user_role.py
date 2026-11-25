# 用户 ↔ 角色 相关的业务函数（多对多关系的读写都集中在这里）
# ----------------------------------------------------------------------------
# 分层约定：service 层只用 ORM 查/写数据、拼装返回结构，
# 不 import FastAPI、不抛 HTTPException —— 状态码和提示语是接口层（api/v1）的事。
# 所以校验函数返回「有问题的 id 列表」，由接口层决定怎么报错。
# 这样同一个校验逻辑将来也能被脚本、定时任务复用，而不会被 HTTP 语义绑住。
from sqlalchemy.orm import Session

from app.models import DBUser, DBRole, DBUserRole
from app.schemas.user import User


def find_missing_role_ids(db: Session, role_ids: list[int] | None) -> list[int]:
    """挑出这批 role_ids 里不存在的角色 id，返回空列表表示全部有效

    不加这道检查的话，前端传个不存在的 role_id 也能写进中间表，
    列表里就会显示出“空角色”（关联指向一个已被删掉的角色）。
    """
    if not role_ids:      # 没传或空数组都是合法状态（等于不分配/全部取消）
        return []
    found = {r.id for r in db.query(DBRole).filter(DBRole.id.in_(role_ids)).all()}
    return [rid for rid in role_ids if rid not in found]


def sync_user_roles(db: Session, user_id: int, role_ids: list[int]) -> None:
    """全量重写某个用户的角色绑定（先删后插，和角色↔菜单那边同一套思路）

    调用前请自己保证已经 commit 过用户本体，且 role_ids 已过校验。
    这里不 commit，把事务边界留给调用方 —— 一次请求要么全成要么全不动。
    """
    db.query(DBUserRole).filter(DBUserRole.user_id == user_id).delete(synchronize_session=False)
    for rid in set(role_ids):   # set 去重，防止前端传 [1,1,2] 这种重复项
        db.add(DBUserRole(user_id=user_id, role_id=rid))


def build_users_with_roles(db: Session) -> list[User]:
    """把 user_roles 里的关联拼回用户对象上，得到前端要的 role_ids（列表页用）

    同样只查 2 次表（users + user_roles）再在 Python 里分组，避开 N+1。
    """
    users = db.query(DBUser).order_by(DBUser.id).all()
    links = db.query(DBUserRole).all()
    result = []
    for u in users:
        result.append(User(
            id=u.id, username=u.username, password=u.password, email=u.email,
            role_ids=sorted(link.role_id for link in links if link.user_id == u.id),
        ))
    return result


def build_user_with_roles(db: Session, db_user: DBUser) -> User:
    """单个用户版的拼装（给 POST/PUT/PATCH 返回用）

    不能直接拿上面那个函数取第一条：为了返一条记录把全表查一遍太浪费。
    """
    ids = sorted(
        link.role_id
        for link in db.query(DBUserRole).filter(DBUserRole.user_id == db_user.id).all()
    )
    return User(
        id=db_user.id, username=db_user.username,
        password=db_user.password, email=db_user.email, role_ids=ids,
    )

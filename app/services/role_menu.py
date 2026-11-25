# 角色 ↔ 菜单 相关的业务函数（授权关系读写）
# 分层约定同 services/user_role.py：只查数据、拼数据，不碰 HTTP 语义
from sqlalchemy.orm import Session

from app.models import DBMenu, DBRole, DBRoleMenu
from app.schemas.role import RoleWithMenus


def build_roles_with_menus(db: Session) -> list[RoleWithMenus]:
    """把“角色 + 已授权菜单”拼成前端要的结构（带 menu_ids / menu_names）

    故意只查 3 次表（roles / menus / role_menus）然后在 Python 里分组，
    而不是每个角色查一次关联——避免“10 个角色要查 11 次”的 N+1 问题。
    """
    roles = db.query(DBRole).order_by(DBRole.id).all()
    menu_names = {m.id: m.name for m in db.query(DBMenu).all()}
    links = db.query(DBRoleMenu).all()
    result = []
    for r in roles:
        ids = sorted(link.menu_id for link in links if link.role_id == r.id)
        result.append(RoleWithMenus(
            id=r.id, name=r.name, description=r.description,
            menu_ids=ids,
            # 过滤一下：万一菜单被删了但残留了关联，拼接时会拼不出名字
            menu_names=[menu_names[mid] for mid in ids if mid in menu_names],
        ))
    return result


def find_missing_menu_ids(db: Session, menu_ids: list[int]) -> list[int]:
    """挑出这批 menu_ids 里不存在的菜单 id（授权前的校验，返回空列表表示全部有效）"""
    if not menu_ids:
        return []
    valid_ids = {m.id for m in db.query(DBMenu).all()}
    return [mid for mid in menu_ids if mid not in valid_ids]


def sync_role_menus(db: Session, role_id: int, menu_ids: list[int]) -> None:
    """全量重写某个角色的菜单授权（先删后插，语义和 sync_user_roles 一致）

    采用「全量覆盖」：先全部删再按新列表插，比“算出哪些新增、哪些取消”简单得多，也不易错。
    """
    db.query(DBRoleMenu).filter(DBRoleMenu.role_id == role_id).delete(synchronize_session=False)
    for mid in set(menu_ids):   # set 去重，防止前端传重复 id
        db.add(DBRoleMenu(role_id=role_id, menu_id=mid))

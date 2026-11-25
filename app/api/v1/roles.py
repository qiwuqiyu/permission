# ============================================================================
# 角色管理接口（原 main.py 第 8 节）
# 套路同上，可以自己先遮住代码默写一遍，检验掌握程度
# 路由拼接规则见 users.py 顶部注释
# ============================================================================
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models import DBRole, DBRoleMenu, DBUserRole
from app.schemas.role import Role, RoleCreate, RoleMenuAssign, RoleWithMenus
from app.services.role_menu import (
    build_roles_with_menus,
    find_missing_menu_ids,
    sync_role_menus,
)

router = APIRouter(prefix="/roles", tags=["角色管理"])


# ---- 查询全部角色 GET /roles ----
# 前端 axios: request.get('/roles')
# 响应改用 RoleWithMenus：除了角色本身，还带上已授权的菜单，前端一次拿全
@router.get("", response_model=list[RoleWithMenus])
def get_all_roles(db: Session = Depends(get_db)):
    return build_roles_with_menus(db)


# ---- 新增角色 POST /roles ----
# 前端 axios: request.post('/roles', { name, description })
@router.post("", response_model=Role)
def create_role(role: RoleCreate, db: Session = Depends(get_db)):
    # 角色名不能重复（防止分配角色时混淆）
    if db.query(DBRole).filter(DBRole.name == role.name).first() is not None:
        raise HTTPException(status_code=400, detail="该角色名已存在")
    db_role = DBRole(name=role.name, description=role.description)
    db.add(db_role)
    db.commit()
    db.refresh(db_role)
    return db_role


# ---- 修改角色 PUT /roles/1 ----
# 前端 axios: request.put(`/roles/${id}`, { name, description })
@router.put("/{role_id}", response_model=Role)
def update_role(role_id: int, role: RoleCreate, db: Session = Depends(get_db)):
    db_role = db.query(DBRole).filter(DBRole.id == role_id).first()
    if db_role is None:
        raise HTTPException(status_code=404, detail="角色不存在")
    # 重复检查排除自己（改成原名字不会被误判）
    dup = db.query(DBRole).filter(DBRole.name == role.name, DBRole.id != role_id).first()
    if dup is not None:
        raise HTTPException(status_code=400, detail="该角色名已存在")
    db_role.name = role.name
    db_role.description = role.description
    db.commit()
    db.refresh(db_role)
    return db_role


# ---- 删除角色 DELETE /roles/1 ----
# 前端 axios: request.delete(`/roles/${id}`)
@router.delete("/{role_id}")
def delete_role(role_id: int, db: Session = Depends(get_db)):
    db_role = db.query(DBRole).filter(DBRole.id == role_id).first()
    if db_role is None:
        raise HTTPException(status_code=404, detail="角色不存在")
    # 删角色要同时处理两张中间表的关联，不然会留下“指向不存在角色”的脏引用：
    # 1) 该角色的菜单授权全部清掉
    db.query(DBRoleMenu).filter(DBRoleMenu.role_id == role_id).delete(synchronize_session=False)
    # 2) 用户↔角色关联也清掉：用户本身保留，只是不再拥有这个角色（可能还有其他角色）
    db.query(DBUserRole).filter(DBUserRole.role_id == role_id).delete(synchronize_session=False)
    db.delete(db_role)
    db.commit()
    return {"msg": "删除成功"}


# ---- 给角色分配可访问菜单 PUT /roles/1/menus ----
# 前端 axios: request.put(`/roles/${id}/menus`, { menu_ids: [1, 3] })
# 这就是【角色 ↔ 菜单】绑定的核心接口：写的是中间表 role_menus
# 路径写成 /{role_id}/menus，加上 prefix 后完整地址是 /roles/{role_id}/menus
@router.put("/{role_id}/menus", response_model=RoleWithMenus)
def assign_role_menus(role_id: int, data: RoleMenuAssign, db: Session = Depends(get_db)):
    db_role = db.query(DBRole).filter(DBRole.id == role_id).first()
    if db_role is None:
        raise HTTPException(status_code=404, detail="角色不存在")
    # 校验传入的菜单 id 都真实存在（弹窗开着时另一个页面把菜单删了，这种并发情况要接住）
    invalid = find_missing_menu_ids(db, data.menu_ids)
    if invalid:
        raise HTTPException(status_code=400, detail=f"菜单不存在：{invalid}")
    # 先清空这个角色的原有授权，再写入新的（「全量覆盖」语义，见 service 注释）
    sync_role_menus(db, role_id, data.menu_ids)
    db.commit()
    # 返回带最新授权信息的角色，前端直接用于刷新表格/关弹窗
    return next(r for r in build_roles_with_menus(db) if r.id == role_id)

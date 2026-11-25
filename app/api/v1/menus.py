# ============================================================================
# 菜单管理接口（原 main.py 第 7 节）
# 套路和用户管理完全一样：模型 + 增删改查，可以对照着感受“第二遍写就熟了”
# 路由拼接规则见 users.py 顶部注释
# ============================================================================
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models import DBMenu, DBRoleMenu
from app.schemas.menu import Menu, MenuCreate

router = APIRouter(prefix="/menus", tags=["菜单管理"])


# ---- 查询全部菜单 GET /menus（Layout 侧边栏加载时调用） ----
# 前端 axios: request.get('/menus')
# order_by(DBMenu.sort)：按排序号升序，数字小的排前面（类比 JS 的 sort((a,b)=>a-b)）
@router.get("", response_model=list[Menu])
def get_all_menus(db: Session = Depends(get_db)):
    return db.query(DBMenu).order_by(DBMenu.sort).all()


# ---- 新增菜单 POST /menus ----
# 前端 axios: request.post('/menus', { name, path, sort })
@router.post("", response_model=Menu)
def create_menu(menu: MenuCreate, db: Session = Depends(get_db)):
    # 路由地址必须以 / 开头，否则前端 el-menu 跳不过去（业务校验放接口里，不放模型里）
    if not menu.path.startswith("/"):
        raise HTTPException(status_code=400, detail="路由地址必须以 / 开头")
    # 同一个路径只能有一个菜单（防止侧边栏出现两个相同页面入口）
    if db.query(DBMenu).filter(DBMenu.path == menu.path).first() is not None:
        raise HTTPException(status_code=400, detail="该路由地址已存在")
    db_menu = DBMenu(name=menu.name, path=menu.path, sort=menu.sort)
    db.add(db_menu)
    db.commit()
    db.refresh(db_menu)
    return db_menu


# ---- 修改菜单 PUT /menus/1（全量更新） ----
# 前端 axios: request.put(`/menus/${id}`, { name, path, sort })
@router.put("/{menu_id}", response_model=Menu)
def update_menu(menu_id: int, menu: MenuCreate, db: Session = Depends(get_db)):
    if not menu.path.startswith("/"):
        raise HTTPException(status_code=400, detail="路由地址必须以 / 开头")
    db_menu = db.query(DBMenu).filter(DBMenu.id == menu_id).first()
    if db_menu is None:
        raise HTTPException(status_code=404, detail="菜单不存在")
    # 重复检查时排除自己（否则改成和原来一样的路径会被误判为重复）
    dup = db.query(DBMenu).filter(DBMenu.path == menu.path, DBMenu.id != menu_id).first()
    if dup is not None:
        raise HTTPException(status_code=400, detail="该路由地址已存在")
    db_menu.name = menu.name
    db_menu.path = menu.path
    db_menu.sort = menu.sort
    db.commit()
    db.refresh(db_menu)
    return db_menu


# ---- 删除菜单 DELETE /menus/1 ----
# 前端 axios: request.delete(`/menus/${id}`)
@router.delete("/{menu_id}")
def delete_menu(menu_id: int, db: Session = Depends(get_db)):
    db_menu = db.query(DBMenu).filter(DBMenu.id == menu_id).first()
    if db_menu is None:
        raise HTTPException(status_code=404, detail="菜单不存在")
    # 一并清掉角色对这条菜单的授权：否则 role_menus 里会残留“指向已删菜单”的脏关联
    db.query(DBRoleMenu).filter(DBRoleMenu.menu_id == menu_id).delete(synchronize_session=False)
    db.delete(db_menu)
    db.commit()
    return {"msg": "删除成功"}

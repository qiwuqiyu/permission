# ============================================================================
# 用户管理接口（原 main.py 第 5 节的 CRUD 部分）
# ----------------------------------------------------------------------------
# 拆包后接口不再写 @app.get，而是挂在 APIRouter 上，最后由 main.py 统一 include_router。
# 类比前端：这个文件 ≈ router/index.ts 里的一条路由记录，main.py ≈ 把路由表塞进 createApp。
#
# ⚠️ prefix 与路径的拼接关系（拆包最容易写错的地方）：
#   prefix="/users" + @router.get("")           -> /users          ✅
#   prefix="/users" + @router.get("/{user_id}") -> /users/{id}     ✅
#   prefix="/users" + @router.get("/users")     -> /users/users    ❌ 重复了
# 另外 "" 和 "/" 在 FastAPI 里是两个不同路径（后者会触发 307 重定向），
# 前端 request.js 调的是 /users，所以这里统一用空字符串。
# ============================================================================
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models import DBUser, DBUserRole
from app.schemas.user import User, UserCreate, UserUpdate
from app.services.user_role import (
    build_user_with_roles,
    build_users_with_roles,
    find_missing_role_ids,
    sync_user_roles,
)

# 一个资源一个 router，tags 决定 Swagger 页面上的分组名
router = APIRouter(prefix="/users", tags=["用户管理"])


# ---- 新增用户 POST /users ----
# 前端 axios: request.post('/users', { username, password, email, role_ids })
@router.post("", response_model=User)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # 业务校验：用户名不能是纯数字
    # 只在这里（新增入口）校验，不影响查询接口返回的历史数据
    if user.username.isdigit():
        # HTTPException 相当于前端的 throw new Error + HTTP 状态码
        # 400 = 客户端传的数据有问题；前端 axios 会走 catch 分支，message 在 error.response.data.detail
        raise HTTPException(status_code=400, detail="用户名不能是纯数字")
    # 选了角色就检查角色是否存在（防脏数据；传空数组就是不给角色，直接跳过）
    # service 只负责查出「哪些 id 不存在」，怎么提示由接口层决定
    missing = find_missing_role_ids(db, user.role_ids)
    if missing:
        raise HTTPException(status_code=400, detail=f"角色不存在：{missing}")

    # 把前端传来的数据组装成一个数据库对象（还没写入，只是内存里）
    # 注意 role_ids 不写在这里了 —— 它不是 users 表的列，属于中间表
    db_user = DBUser(username=user.username, password=user.password, email=user.email)
    db.add(db_user)     # 放进会话的"待写入"队列（还没真正存库）
    db.commit()         # 提交事务 —— 真正写进数据库（类似点了"保存"）
    db.refresh(db_user) # 重新读一次，拿到数据库生成的自增 id（写中间表要靠它）
    # 用户已经有 id 了，才能往 user_roles 里写关联（外键要指向真实存在的用户）
    sync_user_roles(db, db_user.id, user.role_ids)
    db.commit()
    return build_user_with_roles(db, db_user)   # 拼上 role_ids 再返回


# ---- 查询单个用户 GET /users/1 ----
# 前端 axios: request.get(`/users/${id}`)
# 路径参数 {user_id} 会自动转成 int（传非数字会自动返回 422）
@router.get("/{user_id}", response_model=User)
def get_user(user_id: int, db: Session = Depends(get_db)):
    # 按主键 id 过滤查询，.first() 取第一条（没有就是 None，类似数组的 find()）
    db_user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if db_user is None:
        # 404 = 资源不存在，类比前端接口返回的 "Not Found"
        raise HTTPException(status_code=404, detail="用户不存在")
    return build_user_with_roles(db, db_user)   # 手工拼 role_ids，否则返回的一直是空数组


# ---- 查询全部用户 GET /users ----
# 前端 axios: request.get('/users')  （列表页加载时调用）
@router.get("", response_model=list[User])
def get_all_users(db: Session = Depends(get_db)):
    # .all() 取出表里所有记录（类比数组的 map/filter 都不写条件 = 全量）
    # 因为 role_ids 在中间表里，不能直接 return 查询结果，得走拼装函数
    return build_users_with_roles(db)


# ---- 修改用户 PUT /users/1（全量更新）----
# 前端 axios: request.put(`/users/${id}`, { username, password, email, role_ids })
# 注意：PUT 是全量语义，role_ids 不传会走默认值 []，等于把该用户的角色全部取消
# （只想改局部请用 PATCH）
@router.put("/{user_id}", response_model=User)
def update_user(user_id: int, user: UserCreate, db: Session = Depends(get_db)):
    # 先找到这条记录，找不到返回 404
    db_user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    missing = find_missing_role_ids(db, user.role_ids)
    if missing:
        raise HTTPException(status_code=400, detail=f"角色不存在：{missing}")
    # 用前端传来的新值覆盖旧值（此刻只是内存里改了，数据库还没变）
    db_user.username = user.username
    db_user.password = user.password
    db_user.email = user.email
    # PUT 是全量语义：传什么就是最终结果，传 [] 就是把这个用户的角色全部取消
    sync_user_roles(db, user_id, user.role_ids)
    db.commit()         # 提交，真正写库
    db.refresh(db_user) # 拿最新数据
    return build_user_with_roles(db, db_user)


# ---- 局部更新 PATCH /users/1（只改传过来的字段）----
# 前端 axios: request.patch(`/users/${id}`, { email: 'new@qq.com' })
# 和 PUT 的区别：只传想改的字段，其他保持不变
@router.patch("/{user_id}", response_model=User)
def patch_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    # exclude_unset=True：只取"前端真正传了的字段"，没传的不动
    # 类比 TS 里判断 if (data.email !== undefined) 才更新
    update_data = user.model_dump(exclude_unset=True)
    # 坑：role_ids 不是 users 表的列，不能塞进下面那个 setattr 循环，
    # 否则 SQLAlchemy 对象上没这个属性，行为不可控。先单独摘出来处理
    role_ids = update_data.pop("role_ids", None)
    if role_ids is not None:      # 只有本次真传了才动关联（None = 没传 = 保持原样）
        missing = find_missing_role_ids(db, role_ids)
        if missing:
            raise HTTPException(status_code=400, detail=f"角色不存在：{missing}")
    for key, value in update_data.items():
        setattr(db_user, key, value)  # 动态赋值：db_user.email = 新值
    if role_ids is not None:
        sync_user_roles(db, user_id, role_ids)
    db.commit()
    db.refresh(db_user)
    # 同样不能直接 return db_user：它身上没有 role_ids，
    # Pydantic 会用默认值补个空数组回去，前端看到的就是“刚设置的角色不见了”
    return build_user_with_roles(db, db_user)


# ---- 删除用户 DELETE /users/1 ----
# 前端 axios: request.delete(`/users/${id}`)
@router.delete("/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    # 先清掉这个用户的角色关联，再删用户本体（顺序反了中间表就会残留脏行）
    db.query(DBUserRole).filter(DBUserRole.user_id == user_id).delete(synchronize_session=False)
    db.delete(db_user)  # 标记删除
    db.commit()         # 提交，真正从数据库移除
    # 没声明 response_model，直接返回一个字典，框架自动转成 JSON
    return {"msg": "删除成功"}

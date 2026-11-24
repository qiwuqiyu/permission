# ============================================================================
# 导入依赖 —— 相当于前端的 `npm install` + `import`
# ----------------------------------------------------------------------------
# fastapi : Python 的后端框架（对标前端的 Vue/React），用来定义接口(路由)
# pydantic: 数据校验库 —— 相当于「带运行时校验的 TypeScript 类型」
# sqlalchemy: ORM 库 —— 让你用 Python 对象操作数据库，不用手写 SQL
#   (类比：用 axios 调接口，而不是手动拼 HTTP 报文)
# ============================================================================
from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict
from sqlalchemy import create_engine, Column, Integer, String, text, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from fastapi.middleware.cors import CORSMiddleware

# ========== 1. 数据库配置（MySQL）==========
# 连接串格式：mysql+pymysql://用户名:密码@地址:端口/库名?charset=utf8mb4
# pymysql 是 Python 连 MySQL 的驱动（类比前端选 axios 还是 fetch，干活的是底层司机）
MYSQL_USER = "root"
MYSQL_PASSWORD = "123456"
MYSQL_HOST = "127.0.0.1"
MYSQL_PORT = 3306
MYSQL_DATABASE = "vue_user_manage"

# MySQL 和 SQLite 的一个区别：必须先“建库”才能连（SQLite 是自动建文件）
# 所以先用一个不指定库名的临时连接，把库建出来，再正式连接
pre_engine = create_engine(
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/?charset=utf8mb4"
)
with pre_engine.connect() as conn:
    conn.execute(text(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DATABASE} CHARACTER SET utf8mb4"))
    conn.commit()
pre_engine.dispose()

# 正式连接串
SQLALCHEMY_DATABASE_URL = (
    f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4"
)
# engine = 数据库连接池（和数据库打交道的“大门”）
# pool_pre_ping：用连接前先“探活”，闲置久了断掉的连接会自动重连
engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

# SessionLocal = "数据库会话工厂"，每次请求需要一个会话(Session)来读写数据
# autocommit=False: 不自动保存，代码里要显式 db.commit()（类似手动点"保存"按钮）
# autoflush=False: 不自动同步缓存，避免意外把未确认的数据写进数据库
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base = 所有数据库表模型的"父类"（类似 Vue 组件的公共基类）
Base = declarative_base()

# ========== 2. 数据库模型：用户表 users + 菜单表 menus ==========
# 定义数据库表结构 —— 类比 TypeScript 的 interface，但这个会真正生成一张表
# 类名 DBUser -> Python 里的对象；__tablename__ -> 数据库里的真实表名 "users"
class DBUser(Base):
    __tablename__ = "users"

    # MySQL 的 VARCHAR 必须指定长度（SQLite 不用，所以换库时这里要改）
    # primary_key: 主键，唯一标识一条记录（类似前端列表渲染时的 :key，但自增且不可重复）
    # index: 建索引，查询更快；unique: 不允许重复
    id = Column(Integer, primary_key=True, index=True)      # 用户ID，自动编号
    username = Column(String(50), unique=True, index=True)  # 用户名，最长50字符，不能重复
    password = Column(String(100))                         # 密码（明文存储，仅demo演示）
    email = Column(String(100), unique=True, index=True)    # 邮箱，最长100字符，不能重复
    # 注意：这里不再有 role_id 了！
    # 用户和角色的关系改由下面的 user_roles 中间表维护（多对多，一个用户可有多个角色）

# 菜单表：存左侧导航栏的菜单项 —— “菜单管理”页面增删改的就是这张表
# 类比：以前菜单是硬编码在 Layout.vue 里的数组，现在搬进数据库，改数据就能改导航
class DBMenu(Base):
    __tablename__ = "menus"

    id = Column(Integer, primary_key=True, index=True)          # 菜单ID，自动编号
    name = Column(String(50), index=True)                        # 菜单显示名，如“用户管理”
    path = Column(String(100), unique=True, index=True)          # 前端路由地址，如 /users
    sort = Column(Integer, default=0)                            # 排序号，越小越靠前

# 角色表：RBAC 权限模型经典三件套（用户-角色-权限）里的“角色”这一环
# 类比：给用户打标签分组，比如“管理员”能看所有菜单，“普通用户”只能看一部分
class DBRole(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)       # 角色ID，自动编号
    name = Column(String(50), unique=True, index=True)     # 角色名，如“管理员”，不能重复
    description = Column(String(200))                      # 角色描述，备注用

# 角色 ↔ 菜单 关联表（多对多）：一个角色能看多个菜单，一个菜单也能开放给多个角色
# 多对多关系没法靠“在某一侧加一列”解决，必须单独建一张「中间表」，里面只放两个外键
# （下面 user_roles 也是同一类中间表，两个多对多关系各一张，结构完全对称）
class DBRoleMenu(Base):
    __tablename__ = "role_menus"

    id = Column(Integer, primary_key=True, index=True)                      # 关联记录ID
    role_id = Column(Integer, ForeignKey("roles.id"), index=True)           # 哪个角色
    menu_id = Column(Integer, ForeignKey("menus.id"), index=True)           # 能访问哪个菜单

# 用户 ↔ 角色 关联表（多对多）：一个用户可以身兼多个角色（比如既是“运营”又是“客服”）
# 和上面 role_menus 是同一个套路，只要关系是多对多，就必须拆一张只放两个外键的中间表
# 至此就是教科书上的经典 RBAC 五表：users / roles / menus / user_roles / role_menus
class DBUserRole(Base):
    __tablename__ = "user_roles"

    id = Column(Integer, primary_key=True, index=True)                      # 关联记录ID
    user_id = Column(Integer, ForeignKey("users.id"), index=True)           # 哪个用户
    role_id = Column(Integer, ForeignKey("roles.id"), index=True)           # 拥有哪个角色

# 启动时自动建表（类似前端项目初始化时创建本地存储结构）
# 只有表不存在时才会创建，已存在的表不会被改动
Base.metadata.create_all(bind=engine)

# ========== 1.5 轻量迁移：把旧的 users.role_id 升级为 user_roles 中间表 ==========
# create_all() 只会「建新表」（user_roles 会自动建好），但它不会删旧列！
# 而且不能简单一删了之：如果老库里 users.role_id 已经有值，直接 DROP COLUMN 就把数据弄丢了
# 所以顺序必须是：先搬迁旧数据到中间表 -> 再删旧列（整段幂等，跑过一次就不会重复执行）
with engine.connect() as conn:
    has_role_id = conn.execute(
        text(
            "SELECT COUNT(*) FROM information_schema.columns "
            "WHERE table_schema = :db AND table_name = 'users' AND column_name = 'role_id'"
        ),
        {"db": MYSQL_DATABASE},
    ).scalar()
    if has_role_id:
        # 第 1 步：把已有绑定的用户挑出来，灌进 user_roles（跳过重复，避免重跑时插两条）
        legacy = conn.execute(
            text("SELECT id, role_id FROM users WHERE role_id IS NOT NULL")
        ).fetchall()
        moved = 0
        for uid, rid in legacy:
            exists = conn.execute(
                text("SELECT COUNT(*) FROM user_roles WHERE user_id = :u AND role_id = :r"),
                {"u": uid, "r": rid},
            ).scalar()
            if not exists:
                conn.execute(
                    text("INSERT INTO user_roles (user_id, role_id) VALUES (:u, :r)"),
                    {"u": uid, "r": rid},
                )
                moved += 1
        # 第 2 步：数据安全落进中间表了，才删掉旧列（MySQL 删列会自动去掉上面的外键约束）
        conn.execute(text("ALTER TABLE users DROP COLUMN role_id"))
        conn.commit()
        print(f"[迁移] 已将 users.role_id 迁入 user_roles（新增 {moved} 条）并删除旧列")

# 首次运行时给菜单表种两条默认数据（表里没数据才插，防止重复）
# 类比：前端 mock 数据兜底，保证页面第一次打开不至于空白
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

# ========== 3. Pydantic 模型：接口的"出入参类型定义" ==========
# 类比 TypeScript 的 interface / type，但 Pydantic 会「运行时」真正校验：
# 前端传来的 JSON 如果缺字段或类型不对，框架自动返回 422 错误，不会进入函数体

# 请求体模型：新增用户时前端要 POST 过来的 JSON 结构
# { "username": "xxx", "password": "xxx", "email": "xxx" }
class UserCreate(BaseModel):
    username: str   # 必填，必须是字符串
    password: str   # 必填，必须是字符串
    email: str      # 必填，必须是字符串
    # 所属角色 id 列表（不再是单个 role_id）：空数组 = 一个角色都没分配
    role_ids: list[int] = []

# 局部更新模型：PATCH 时允许只传想改的字段（其他字段不传就保持原样）
# `str | None = None` 相当于 TS 的 `username?: string`，不传就是 undefined
class UserUpdate(BaseModel):
    username: str | None = None
    password: str | None = None
    email: str | None = None
    # 这里用 `| None = None` 而不是直接给 []，是为了区分两种完全不同的意图：
    # None = 这次没动角色（保持原样）；[] = 明确要把角色全部清空
    role_ids: list[int] | None = None

# 响应模型：后端返回给前端的用户数据结构（在 UserCreate 基础上多了 id）
class User(UserCreate):
    id: int  # 数据库生成的自增ID
    # Pydantic v2 写法：允许直接从数据库对象(DBUser)上读取属性来组装 JSON
    # （v1 的旧写法叫 orm_mode=True，改名了而已，作用相同）
    # 注：role_ids 不存在 users 表上，要靠下面手工从 user_roles 查出来填，
    #     所以 from_attributes 只能自动带出 username/email 这几列
    model_config = ConfigDict(from_attributes=True)

# 菜单的出入参模型（结构比用户简单，套路完全一样）
# 新增菜单时前端 POST 过来的 JSON：{ "name": "xx", "path": "/xx", "sort": 1 }
class MenuCreate(BaseModel):
    name: str       # 菜单显示名，必填
    path: str       # 前端路由地址，必填（如 /users）
    sort: int = 0   # 排序号，不传默认为 0（相当于 TS 的 sort?: number）

class MenuUpdate(BaseModel):
    name: str | None = None
    path: str | None = None
    sort: int | None = None

# 菜单响应模型（多了 id，供前端表格渲染 :key 用）
class Menu(MenuCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)

# 角色的出入参模型（第三遍写这个套路了：模型 -> 接口 -> 页面，已经完全流程化）
# 新增角色时前端 POST 过来的 JSON：{ "name": "xx", "description": "xx" }
class RoleCreate(BaseModel):
    name: str            # 角色名，必填
    description: str = ""   # 角色描述，不传默认空字符串（相当于 TS 的 description?: string）

class RoleUpdate(BaseModel):
    name: str | None = None
    description: str | None = None

# 角色响应模型（多了 id）
class Role(RoleCreate):
    id: int
    model_config = ConfigDict(from_attributes=True)

# 给角色分配菜单的请求体：{ "menu_ids": [1, 3] }
# 语义是「全量覆盖」：传什么就是最终结果，传空数组 = 取消该角色全部菜单授权
class RoleMenuAssign(BaseModel):
    menu_ids: list[int] = []

# 角色列表的响应模型：在 Role 基础上带上已授权的菜单
# 这样前端拉一次 /roles 就能同时拿到表格展示 + 弹窗回显所需的数据，不用再单独查
class RoleWithMenus(Role):
    menu_ids: list[int] = []     # 已授权菜单 id，用于弹窗勾选回显
    menu_names: list[str] = []   # 已授权菜单名，用于表格直接展示

# ========== 4. FastAPI 实例 + 跨域配置 ==========
# app = 后端应用实例，之后所有的接口都"挂"在它上面
# （类比：const app = createApp(App)，或者 Vue Router 里的 router 实例）
app = FastAPI(title="用户CRUD接口")

# CORS 跨域中间件 —— 前端最常见的报错 "CORS policy" 就是它解决的
# 浏览器安全策略：默认禁止 localhost:5173 的页面请求 localhost:8000 的接口
# 这里相当于后端"主动放行"，告诉浏览器：这些来源/方法/请求头我都允许
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许任何前端地址访问（开发环境方便；上线必须改成具体域名，不能写*）
    allow_credentials=True,  # 允许携带 cookie 等凭证
    allow_methods=["*"],    # 允许所有 HTTP 方法（GET/POST/PUT/PATCH/DELETE...）
    allow_headers=["*"],     # 允许所有请求头（比如 axios 默认的 Content-Type 等）
)

# 获取数据库会话 —— 每次接口请求都会执行一次
# 类比：每个请求进来先"打开数据库连接"，用完自动关闭，防止连接泄漏
def get_db():
    db = SessionLocal()          # 打开一个数据库会话
    try:
        yield db                 # 把会话交给接口函数使用（yield = 暂停在这里，请求结束后回来继续）
    finally:
        db.close()               # 无论成功还是报错，最后都关闭会话（finally 保证一定执行）

# 校验“这一批角色都真实存在”——多个用户接口都要用，抽成小函数复用
# 不加这道检查的话，前端传个不存在的 role_id 也能写进中间表，列表里就会显示出“空角色”
def ensure_roles_exist(db: Session, role_ids: list[int] | None):
    if not role_ids:      # 没传或空数组都是合法状态（等于不分配/全部取消）
        return
    found = {r.id for r in db.query(DBRole).filter(DBRole.id.in_(role_ids)).all()}
    missing = [rid for rid in role_ids if rid not in found]
    if missing:
        raise HTTPException(status_code=400, detail=f"角色不存在：{missing}")

# 全量重写某个用户的角色绑定（先删后插，和角色↔菜单那边同一套思路）
# 调用前请自己保证已经 commit 过用户本体，且 role_ids 已过校验
def sync_user_roles(db: Session, user_id: int, role_ids: list[int]):
    db.query(DBUserRole).filter(DBUserRole.user_id == user_id).delete(synchronize_session=False)
    for rid in set(role_ids):   # set 去重，防止前端传 [1,1,2] 这种重复项
        db.add(DBUserRole(user_id=user_id, role_id=rid))

# 把 user_roles 里的关联拼回用户对象上，得到前端要的 role_ids
# 同样只查 2 次表（users + user_roles）再在 Python 里分组，避开 N+1
def build_users_with_roles(db: Session) -> list[User]:
    users = db.query(DBUser).order_by(DBUser.id).all()
    links = db.query(DBUserRole).all()
    result = []
    for u in users:
        result.append(User(
            id=u.id, username=u.username, password=u.password, email=u.email,
            role_ids=sorted(link.role_id for link in links if link.user_id == u.id),
        ))
    return result

# 单个用户版的拼装（给 POST/PUT/PATCH 返回用）
# 不能直接拿上面那个函数取第一条：为了返一条记录把全表查一遍太浪费
def build_user_with_roles(db: Session, db_user: DBUser) -> User:
    ids = sorted(
        link.role_id
        for link in db.query(DBUserRole).filter(DBUserRole.user_id == db_user.id).all()
    )
    return User(
        id=db_user.id, username=db_user.username,
        password=db_user.password, email=db_user.email, role_ids=ids,
    )

# 把“角色 + 已授权菜单”拼成前端要的结构（带 menu_ids / menu_names）
# 故意只查 3 次表（roles / menus / role_menus）然后在 Python 里分组，
# 而不是每个角色查一次关联——避免“10 个角色要查 11 次”的 N+1 问题
def build_roles_with_menus(db: Session) -> list[RoleWithMenus]:
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

# ========== 5. CRUD 接口 增删改查 ==========
# @app.post / @app.get ... 叫"装饰器"，作用是「注册路由」
# 类比 Vue Router 里的 { path: '/users', component: ... }
# 区别：前端路由对应页面，后端路由对应一个函数
# response_model=User：声明返回结构，框架会按 User 模型过滤/校验后再返回给前端
# Depends(get_db)：依赖注入 —— 每次请求自动调用 get_db() 拿到数据库会话
#   （类比：组件里的 props 自动注入，你不用手动传，框架帮你准备好）

# ---- 新增用户 POST /users ----
# 前端 axios: request.post('/users', { username, password, email })
@app.post("/users", response_model=User)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # 业务校验：用户名不能是纯数字
    # 只在这里（新增入口）校验，不影响查询接口返回的历史数据
    if user.username.isdigit():
        # HTTPException 相当于前端的 throw new Error + HTTP 状态码
        # 400 = 客户端传的数据有问题；前端 axios 会走 catch 分支，message 在 error.response.data.detail
        raise HTTPException(status_code=400, detail="用户名不能是纯数字")
    # 选了角色就检查角色是否存在（防脏数据；传空数组就是不给角色，直接跳过）
    ensure_roles_exist(db, user.role_ids)

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
@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int, db: Session = Depends(get_db)):
    # 按主键 id 过滤查询，.first() 取第一条（没有就是 None，类似数组的 find()）
    db_user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if db_user is None:
        # 404 = 资源不存在，类比前端接口返回的 "Not Found"
        raise HTTPException(status_code=404, detail="用户不存在")
    return build_user_with_roles(db, db_user)   # 手工拼 role_ids，否则返回的一直是空数组

# ---- 查询全部用户 GET /users ----
# 前端 axios: request.get('/users')  （列表页加载时调用）
@app.get("/users", response_model=list[User])
def get_all_users(db: Session = Depends(get_db)):
    # .all() 取出表里所有记录（类比数组的 map/filter 都不写条件 = 全量）
    # 因为 role_ids 在中间表里，不能直接 return 查询结果，得走拼装函数
    return build_users_with_roles(db)

# ---- 修改用户 PUT /users/1（全量更新）----
# 前端 axios: request.put(`/users/${id}`, { username, password, email, role_ids })
# 注意：PUT 是全量语义，role_ids 不传会走默认值 []，等于把该用户的角色全部取消
# （只想改局部请用 PATCH）
@app.put("/users/{user_id}", response_model=User)
def update_user(user_id: int, user: UserCreate, db: Session = Depends(get_db)):
    # 先找到这条记录，找不到返回 404
    db_user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    ensure_roles_exist(db, user.role_ids)
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
@app.patch("/users/{user_id}", response_model=User)
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
        ensure_roles_exist(db, role_ids)
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
@app.delete("/users/{user_id}")
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

# ========== 6. 登录接口 ==========
# 登录请求体：前端登录页 POST 过来的 JSON
# { "username": "xxx", "password": "xxx" }
class LoginRequest(BaseModel):
    username: str
    password: str

# ---- 登录 POST /login ----
# 前端 axios: request.post('/login', { username, password })
# 类比前端：登录页点击“登录”按钮调用的接口
@app.post("/login")
def login(data: LoginRequest, db: Session = Depends(get_db)):
    # 用用户名 + 密码去数据库里找（demo 直接比对明文密码，真实项目要用哈希）
    db_user = (
        db.query(DBUser)
        .filter(DBUser.username == data.username, DBUser.password == data.password)
        .first()
    )
    if db_user is None:
        # 401 = 未认证：账号或密码不对，前端会走 catch，提示“用户名或密码错误”
        raise HTTPException(status_code=401, detail="用户名或密码错误")
    # 登录成功：发一个令牌(token)给前端保存（demo 用简单字符串；真实项目用 JWT）
    # 前端拿到 token 存进 localStorage，之后的请求都带上它证明“我已登录”
    return {"token": f"token-{db_user.id}-{db_user.username}", "username": db_user.username}

# ========== 7. 菜单管理 CRUD 接口 ==========
# 套路和用户管理完全一样：模型 + 增删改查，可以对照着感受“第二遍写就熟了”

# ---- 查询全部菜单 GET /menus（Layout 侧边栏加载时调用） ----
# 前端 axios: request.get('/menus')
# order_by(DBMenu.sort)：按排序号升序，数字小的排前面（类比 JS 的 sort((a,b)=>a-b)）
@app.get("/menus", response_model=list[Menu])
def get_all_menus(db: Session = Depends(get_db)):
    return db.query(DBMenu).order_by(DBMenu.sort).all()

# ---- 新增菜单 POST /menus ----
# 前端 axios: request.post('/menus', { name, path, sort })
@app.post("/menus", response_model=Menu)
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
@app.put("/menus/{menu_id}", response_model=Menu)
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
@app.delete("/menus/{menu_id}")
def delete_menu(menu_id: int, db: Session = Depends(get_db)):
    db_menu = db.query(DBMenu).filter(DBMenu.id == menu_id).first()
    if db_menu is None:
        raise HTTPException(status_code=404, detail="菜单不存在")
    # 一并清掉角色对这条菜单的授权：否则 role_menus 里会残留“指向已删菜单”的脏关联
    db.query(DBRoleMenu).filter(DBRoleMenu.menu_id == menu_id).delete(synchronize_session=False)
    db.delete(db_menu)
    db.commit()
    return {"msg": "删除成功"}

# ========== 8. 角色管理 CRUD 接口 ==========
# 套路同上，可以自己先遮住代码默写一遍，检验掌握程度

# ---- 查询全部角色 GET /roles ----
# 前端 axios: request.get('/roles')
# 响应改用 RoleWithMenus：除了角色本身，还带上已授权的菜单，前端一次拿全
@app.get("/roles", response_model=list[RoleWithMenus])
def get_all_roles(db: Session = Depends(get_db)):
    return build_roles_with_menus(db)

# ---- 新增角色 POST /roles ----
# 前端 axios: request.post('/roles', { name, description })
@app.post("/roles", response_model=Role)
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
@app.put("/roles/{role_id}", response_model=Role)
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
@app.delete("/roles/{role_id}")
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
# 采用「全量覆盖」语义：先全部删再按新列表插，比“算出哪些新增、哪些取消”简单得多，也不易错
@app.put("/roles/{role_id}/menus", response_model=RoleWithMenus)
def assign_role_menus(role_id: int, data: RoleMenuAssign, db: Session = Depends(get_db)):
    db_role = db.query(DBRole).filter(DBRole.id == role_id).first()
    if db_role is None:
        raise HTTPException(status_code=404, detail="角色不存在")
    # 校验传入的菜单 id 都真实存在（弹窗开着时另一个页面把菜单删了，这种并发情况要接住）
    valid_ids = {m.id for m in db.query(DBMenu).all()}
    invalid = [mid for mid in data.menu_ids if mid not in valid_ids]
    if invalid:
        raise HTTPException(status_code=400, detail=f"菜单不存在：{invalid}")
    # 先清空这个角色的原有授权，再写入新的（set 去重，防止前端传重复 id）
    db.query(DBRoleMenu).filter(DBRoleMenu.role_id == role_id).delete(synchronize_session=False)
    for mid in set(data.menu_ids):
        db.add(DBRoleMenu(role_id=role_id, menu_id=mid))
    db.commit()
    # 返回带最新授权信息的角色，前端直接用于刷新表格/关弹窗
    return next(r for r in build_roles_with_menus(db) if r.id == role_id)

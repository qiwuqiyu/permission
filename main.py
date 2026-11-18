from fastapi import Depends, FastAPI, HTTPException
from pydantic import BaseModel, ConfigDict, field_validator
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from fastapi.middleware.cors import CORSMiddleware

# ========== 4. FastAPI实例 ==========

# ========== 1. 数据库配置 SQLite ==========
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ========== 2. 数据库模型：用户表 User ==========
class DBUser(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    email = Column(String, unique=True, index=True)

# 创建表（如果不存在）
Base.metadata.create_all(bind=engine)

# ========== 3. Pydantic 模型：接口接收/返回数据 ==========
class UserCreate(BaseModel):
    username: str
    password: str
    email: str

    # 用户名不能是纯数字
    @field_validator("username")
    @classmethod
    def username_not_digit(cls, v: str):
        if v.isdigit():
            raise ValueError("用户名不能是纯数字")
        return v

class UserUpdate(BaseModel):
    username: str | None = None
    password: str | None = None
    email: str | None = None

class User(UserCreate):
    id: int
    # Pydantic v2：允许从 SQLAlchemy 对象读取属性（替代 v1 的 orm_mode）
    model_config = ConfigDict(from_attributes=True)

# ========== 4. FastAPI实例 + 数据库会话依赖 ==========
app = FastAPI(title="用户CRUD接口")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 开发环境允许所有前端地址，上线不能写*
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# ========== 5. CRUD 接口 增删改查 ==========
# 新增用户 POST
@app.post("/users", response_model=User)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = DBUser(username=user.username, password=user.password, email=user.email)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# 查询单个用户 GET
@app.get("/users/{user_id}", response_model=User)
def get_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    return db_user

# 查询全部用户 GET
@app.get("/users", response_model=list[User])
def get_all_users(db: Session = Depends(get_db)):
    return db.query(DBUser).all()

# 修改用户 PUT（全量更新）
@app.put("/users/{user_id}", response_model=User)
def update_user(user_id: int, user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    db_user.username = user.username
    db_user.password = user.password
    db_user.email = user.email
    db.commit()
    db.refresh(db_user)
    return db_user

# 局部更新 PATCH（只改传过来的字段）
@app.patch("/users/{user_id}", response_model=User)
def patch_user(user_id: int, user: UserUpdate, db: Session = Depends(get_db)):
    db_user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    update_data = user.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_user, key, value)
    db.commit()
    db.refresh(db_user)
    return db_user

# 删除用户 DELETE
@app.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db)):
    db_user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    db.delete(db_user)
    db.commit()
    return {"msg": "删除成功"}

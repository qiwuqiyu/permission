# 用户表模型：数据库里真实的那张 users 表
# 类比 TypeScript 的 interface，但这个会真正生成一张表
# 类名 DBUser -> Python 里的对象；__tablename__ -> 数据库里的真实表名 "users"
# 加 DB 前缀是为了和 schemas/user.py 里的 User 区分开：
# 一个是「表里的一行」，一个是「接口传来/返回的一份数据」，不是一回事
from sqlalchemy import Column, Integer, String

from app.db.base import Base


class DBUser(Base):
    __tablename__ = "users"

    # MySQL 的 VARCHAR 必须指定长度（SQLite 不用，所以换库时这里要改）
    # primary_key: 主键，唯一标识一条记录（类似前端列表渲染时的 :key，但自增且不可重复）
    # index: 建索引，查询更快；unique: 不允许重复
    id = Column(Integer, primary_key=True, index=True)      # 用户ID，自动编号
    username = Column(String(50), unique=True, index=True)  # 用户名，最长50字符，不能重复
    password = Column(String(100))                          # 密码（明文存储，仅demo演示）
    email = Column(String(100), unique=True, index=True)    # 邮箱，最长100字符，不能重复
    # 注意：这里没有 role_id！
    # 用户和角色的关系由 user_roles 中间表维护（多对多，一个用户可有多个角色），
    # 见 app/models/association.py

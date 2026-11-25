# Base = 所有数据库表模型的"父类"（类似 Vue 组件的公共基类）
# ----------------------------------------------------------------------------
# ⚠️ 全项目只能有这一个 Base。
# 如果每个 model 文件各自 declarative_base()，就会各拿各的 metadata，
# create_all() 只认最后那一份，表现为「表莫名其妙没建出来」——
# 这是拆包之后最容易踩的第一个坑。
from sqlalchemy.orm import declarative_base

Base = declarative_base()

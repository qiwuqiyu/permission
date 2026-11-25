# ============================================================================
# 配置中心 —— 所有「会因环境不同而变」的值都收在这里
# ----------------------------------------------------------------------------
# 以前 MYSQL_PASSWORD = "123456" 硬写在 main.py 里，一换机器/上线就得改代码。
# 现在交给 pydantic-settings，按「代码默认值 < .env 文件 < 系统环境变量」三层优先级取值，
# 代码里只读 settings.mysql_password，不关心它从哪来。
# 类比前端：import.meta.env.VITE_XXX + .env.development / .env.production
# ============================================================================
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 字段名写小写，对应的环境变量名不区分大小写（MYSQL_USER / mysql_user 都能读到）
    mysql_user: str = "root"
    mysql_password: str = "123456"
    mysql_host: str = "127.0.0.1"
    mysql_port: int = 3306
    mysql_database: str = "vue_user_manage"

    # env_file=".env"：项目根目录的 .env 会被自动读取（文件不存在也不报错，
    #                  所以本机不建 .env 也能直接用上面的默认值跑起来）
    # extra="ignore"：.env 里多出来的键直接忽略，否则会抛「未知字段」错误
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def database_url(self) -> str:
        """正式连接串（连到指定库）
        连接串格式：mysql+pymysql://用户名:密码@地址:端口/库名?charset=utf8mb4
        pymysql 是 Python 连 MySQL 的驱动（类比前端选 axios 还是 fetch，干活的是底层司机）
        """
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/{self.mysql_database}?charset=utf8mb4"
        )

    @property
    def server_url(self) -> str:
        """不带库名的连接串 —— 建库那一步专用（MySQL 必须先建库才能连）"""
        return (
            f"mysql+pymysql://{self.mysql_user}:{self.mysql_password}"
            f"@{self.mysql_host}:{self.mysql_port}/?charset=utf8mb4"
        )


# 模块级单例：整个进程共用一份配置，别处 `from app.core.config import settings` 即可，
# 不需要把配置当参数一路传下去
settings = Settings()

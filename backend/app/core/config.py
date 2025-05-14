# backend/app/core/config.py
import os
from typing import List, Optional
from pydantic import BaseSettings, Field # 仍然使用 Pydantic 的 BaseSettings，但加载方式不同
from dotenv import load_dotenv

# 手动加载 .env 文件中的环境变量
# __file__ 指向当前文件 (config.py)
# os.path.dirname(__file__) 获取当前文件所在目录 (app/core/)
# os.path.join(..., '..', '..', '.env') 构造出 backend/.env 的路径
env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
if os.path.exists(env_path):
    print(f"Loading environment variables from: {env_path}")
    load_dotenv(dotenv_path=env_path)
else:
    print(f".env file not found at: {env_path}, relying on system environment variables.")


class Settings(BaseSettings):
    PROJECT_NAME: str = "三位一体量化助手 API"
    API_V1_STR: str = "/api/v1"
    # --- 关键检查点 ---
    BACKEND_CORS_ORIGINS_STR: Optional[str] = Field(default="http://localhost:5173,http://127.0.0.1:5173", env="BACKEND_CORS_ORIGINS")
    TUSHARE_TOKEN: Optional[str] = Field(default=None, env="TUSHARE_TOKEN")

    @property
    def BACKEND_CORS_ORIGINS(self) -> List[str]:
        if self.BACKEND_CORS_ORIGINS_STR:
            # 确保这里能正确解析，并且包含您的前端端口 5174
            print(f"Parsing BACKEND_CORS_ORIGINS_STR: '{self.BACKEND_CORS_ORIGINS_STR}'")
            origins = [origin.strip() for origin in self.BACKEND_CORS_ORIGINS_STR.split(",")]
            print(f"Parsed BACKEND_CORS_ORIGINS: {origins}")
            return origins
        return [] # 如果字符串为空，返回空列表

    # 数据库配置 (如果使用)
    # SQLALCHEMY_DATABASE_URL: Optional[str] = Field(default="sqlite:///./sql_app.db", env="SQLALCHEMY_DATABASE_URL")

    # Pydantic v1.x 的 BaseSettings 会自动从环境变量中读取与字段同名（大写）的值
    # 我们使用 Field(env="ENV_VAR_NAME") 来明确指定环境变量名称，如果它与字段名不同或为了更清晰
    class Config:
        # Pydantic v1.x 中，如果字段名与环境变量名完全一致（不区分大小写，但通常用大写环境变量），
        # 则不需要 env_prefix 或 case_sensitive。
        # 如果环境变量名与字段名不同，则需要使用 Field(env=...)
        # case_sensitive = True # Pydantic v1 默认为 False，可以不设置或按需设置
        env_file_encoding = 'utf-8' # 如果你的 .env 文件是 utf-8 编码

settings = Settings()

# 打印加载的设置以供调试 (正式发布时可以移除)
print(f"Loaded TUSHARE_TOKEN: {'SET' if settings.TUSHARE_TOKEN else 'NOT SET'}")
print(f"Loaded BACKEND_CORS_ORIGINS: {settings.BACKEND_CORS_ORIGINS}")  
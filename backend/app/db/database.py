# --- START OF FILE backend/app/db/database.py ---
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.core.config import settings # 假设数据库URL在配置中

# 使用 settings.SQLALCHEMY_DATABASE_URL
# 例如: "sqlite:///./quant_assistant.db"
SQLALCHEMY_DATABASE_URL = settings.SQLALCHEMY_DATABASE_URL 

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, 
    connect_args={"check_same_thread": False} # Needed only for SQLite
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# DB Utilities
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def create_db_and_tables():
    # 在应用启动时创建表（如果它们不存在）
    # 注意: 对于生产环境，通常使用 Alembic 进行数据库迁移管理
    Base.metadata.create_all(bind=engine)
    print("Database tables created (if they didn't exist).")

# --- END OF FILE backend/app/db/database.py ---
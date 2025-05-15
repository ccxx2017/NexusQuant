# --- START OF FILE backend/app/db/models.py ---
from sqlalchemy import Column, Integer, String, Float, Date, Text, DateTime, ForeignKey # Date -> Text for YYYY-MM-DD
from sqlalchemy.sql import func # for CURRENT_TIMESTAMP
from sqlalchemy.orm import relationship # if we have user table later
from app.db.database import Base # Base 会在 database.py 中定义

class Holding(Base):
    __tablename__ = "holdings"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ts_code = Column(String, nullable=False, index=True)
    cost_price = Column(Float, nullable=False)
    quantity = Column(Integer, nullable=False)
    open_date = Column(String, nullable=False) # Store date as 'YYYY-MM-DD' string
    notes = Column(Text, nullable=True)
    
    # 假设有一个 user_id，如果现在没有用户系统，可以先注释掉或允许为空
    # user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True) # 示例
    # owner = relationship("User", back_populates="holdings") # 示例

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 我们也可以在这里添加一些计算属性的逻辑，但通常Pydantic模型更适合做展示前的数据转换
# --- END OF FILE backend/app/db/models.py ---
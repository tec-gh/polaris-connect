from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# レコードを項目単位で検索しやすくするための分解テーブル。
# 検索条件は主にこのテーブル経由で評価する。
class TemplateRecordValue(Base):
    __tablename__ = "template_record_values"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    record_id: Mapped[int] = mapped_column(ForeignKey("template_records.id", ondelete="CASCADE"), nullable=False)
    field_key: Mapped[str] = mapped_column(Text, nullable=False)
    field_value: Mapped[str] = mapped_column(Text, nullable=False, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    record = relationship("TemplateRecord", back_populates="values")

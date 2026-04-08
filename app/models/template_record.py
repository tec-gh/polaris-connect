from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# テンプレートに紐づく1件分の受信レコード。
# 元 payload と正規化済み JSON の両方を保持する。
class TemplateRecord(Base):
    __tablename__ = "template_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("template_definitions.id", ondelete="CASCADE"), nullable=False)
    unique_key_value: Mapped[str] = mapped_column(Text, nullable=False, default="")
    payload_json: Mapped[str] = mapped_column(Text, nullable=False)
    normalized_data_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    received_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)
    external_api_last_status: Mapped[str] = mapped_column(Text, nullable=False, default="")
    external_api_last_response: Mapped[str] = mapped_column(Text, nullable=False, default="")
    external_api_last_executed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    template = relationship("TemplateDefinition", back_populates="records")
    values = relationship("TemplateRecordValue", back_populates="record", cascade="all, delete-orphan")

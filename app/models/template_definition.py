from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# テンプレート単位の設定本体を保持するテーブル。
# API 名、一意キー、外部 API 設定などの親情報を持つ。
class TemplateDefinition(Base):
    __tablename__ = "template_definitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    api_name: Mapped[str] = mapped_column(String(64), nullable=False, unique=True)
    unique_key_field: Mapped[str] = mapped_column(String(64), nullable=False, default="hostname")
    external_api_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    external_api_url: Mapped[str] = mapped_column(Text, nullable=False, default="")
    external_api_headers_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    external_api_body_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # テンプレート単位の設定本体を保持するテーブル。?????
    fields = relationship("TemplateField", back_populates="template", cascade="all, delete-orphan")
    records = relationship("TemplateRecord", back_populates="template", cascade="all, delete-orphan")

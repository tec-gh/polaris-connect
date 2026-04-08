from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# テンプレート内の各項目定義を保持するテーブル。
# JSON パスや検索可否など、UI と取込の両方で利用する。
class TemplateField(Base):
    __tablename__ = "template_fields"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    template_id: Mapped[int] = mapped_column(ForeignKey("template_definitions.id", ondelete="CASCADE"), nullable=False)
    field_key: Mapped[str] = mapped_column(String(64), nullable=False)
    display_name: Mapped[str] = mapped_column(String(128), nullable=False)
    json_path: Mapped[str] = mapped_column(String(255), nullable=False)
    is_visible: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_searchable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    is_exportable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    update_mode: Mapped[str] = mapped_column(String(32), nullable=False, default="overwrite")
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    template = relationship("TemplateDefinition", back_populates="fields")

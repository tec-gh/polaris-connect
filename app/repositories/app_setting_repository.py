from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.app_setting import AppSetting


def get_settings_map(session: Session) -> dict[str, str]:
    items = session.scalars(select(AppSetting)).all()
    return {item.setting_key: item.setting_value for item in items}


def upsert_settings(session: Session, values: dict[str, str]) -> None:
    existing = {item.setting_key: item for item in session.scalars(select(AppSetting)).all()}
    for key, value in values.items():
        item = existing.get(key)
        if item is None:
            session.add(AppSetting(setting_key=key, setting_value=value))
        else:
            item.setting_value = value
    session.flush()

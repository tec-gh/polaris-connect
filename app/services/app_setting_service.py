from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.core.config import settings
from app.repositories.app_setting_repository import get_settings_map, upsert_settings


SFTP_SETTING_KEYS = (
    "sftp_host",
    "sftp_username",
    "sftp_password",
    "sftp_frequency_minutes",
    "sftp_remote_path",
)


@dataclass
class SftpTransferSettings:
    sftp_host: str = ""
    sftp_username: str = ""
    sftp_password: str = ""
    sftp_frequency_minutes: int = 60
    sftp_remote_path: str = "records_export.json"

    @property
    def enabled(self) -> bool:
        return bool(
            self.sftp_host
            and self.sftp_username
            and self.sftp_password
            and self.sftp_frequency_minutes > 0
            and self.sftp_remote_path
        )


def get_sftp_settings(session: Session) -> SftpTransferSettings:
    stored = get_settings_map(session)
    frequency_raw = stored.get("sftp_frequency_minutes", str(settings.sftp_frequency_minutes))
    try:
        frequency = max(1, int(frequency_raw))
    except ValueError:
        frequency = settings.sftp_frequency_minutes
    return SftpTransferSettings(
        sftp_host=stored.get("sftp_host", settings.sftp_host),
        sftp_username=stored.get("sftp_username", settings.sftp_username),
        sftp_password=stored.get("sftp_password", settings.sftp_password),
        sftp_frequency_minutes=frequency,
        sftp_remote_path=stored.get("sftp_remote_path", settings.sftp_remote_path or settings.sftp_remote_filename),
    )


def save_sftp_settings(session: Session, values: dict[str, str]) -> None:
    upsert_settings(session, values)

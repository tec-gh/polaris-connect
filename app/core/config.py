from dataclasses import dataclass
import os


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Polaris Connect")
    app_env: str = os.getenv("APP_ENV", "development")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")
    page_size_default: int = int(os.getenv("PAGE_SIZE_DEFAULT", "20"))
    export_max_rows: int = int(os.getenv("EXPORT_MAX_ROWS", "10000"))
    admin_username: str = os.getenv("ADMIN_USERNAME", "admin")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "change_me")
    api_key: str = os.getenv("API_KEY", "")
    sftp_host: str = os.getenv("SFTP_HOST", "")
    sftp_username: str = os.getenv("SFTP_USERNAME", "")
    sftp_password: str = os.getenv("SFTP_PASSWORD", "")
    sftp_frequency_minutes: int = int(os.getenv("SFTP_FREQUENCY_MINUTES", "60"))
    sftp_remote_filename: str = os.getenv("SFTP_REMOTE_FILENAME", "records_export.json")
    sftp_remote_path: str = os.getenv("SFTP_REMOTE_PATH", "records_export.json")


settings = Settings()

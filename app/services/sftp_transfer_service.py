import asyncio
import logging
from posixpath import join as posix_join

from app.core.database import session_scope
from app.core.config import settings
from app.repositories.template_repository import list_templates
from app.services.app_setting_service import get_sftp_settings
from app.services.export_service import render_json
from app.services.record_service import export_records

logger = logging.getLogger(__name__)


def _remote_path_for_template(base_path: str, api_name: str, total_templates: int) -> str:
    normalized = (base_path or "").strip() or f"{api_name}.json"
    if total_templates == 1 and normalized.endswith(".json"):
        return normalized
    if normalized.endswith("/"):
        return posix_join(normalized.rstrip("/"), f"{api_name}.json")
    if "." not in normalized.rsplit("/", 1)[-1]:
        return posix_join(normalized, f"{api_name}.json")
    prefix, _ = normalized.rsplit(".", 1)
    return f"{prefix}_{api_name}.json"


def transfer_export_json() -> None:
    import paramiko

    with session_scope() as session:
        sftp_settings = get_sftp_settings(session)
        if not sftp_settings.enabled:
            return
        templates = list_templates(session)
        payloads: list[tuple[str, str]] = []
        for template in templates:
            records = list(export_records(session, template, {"keyword": None, "date_from": None, "date_to": None}, settings.export_max_rows))
            content = render_json(template, records)
            payloads.append((_remote_path_for_template(sftp_settings.sftp_remote_path, template.api_name, len(templates)), content))

    transport = paramiko.Transport((sftp_settings.sftp_host, 22))
    try:
        transport.connect(username=sftp_settings.sftp_username, password=sftp_settings.sftp_password)
        with paramiko.SFTPClient.from_transport(transport) as client:
            for remote_path, content in payloads:
                with client.file(remote_path, "w") as remote_file:
                    remote_file.write(content)
    finally:
        transport.close()


async def sftp_transfer_loop(stop_event: asyncio.Event) -> None:
    while not stop_event.is_set():
        wait_seconds = 60
        try:
            with session_scope() as session:
                sftp_settings = get_sftp_settings(session)
            wait_seconds = max(60, sftp_settings.sftp_frequency_minutes * 60)
            if sftp_settings.enabled:
                await asyncio.to_thread(transfer_export_json)
        except Exception as exc:
            logger.exception("SFTP transfer failed: %s", exc)

        try:
            await asyncio.wait_for(stop_event.wait(), timeout=wait_seconds)
        except asyncio.TimeoutError:
            continue

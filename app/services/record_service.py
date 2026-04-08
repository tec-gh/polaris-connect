import json
from datetime import datetime
from typing import Any, Optional
from urllib import request as urllib_request

from sqlalchemy.orm import Session

from app.models.template_record import TemplateRecord
from app.repositories.template_record_repository import (
    create_template_record,
    get_template_record_by_id,
    get_template_record_by_unique_key,
    list_template_records,
    list_template_records_for_export,
    resync_template_records,
    set_record_values,
)
from app.services.mapping_service import MappingExtractor, get_template_mapping_config

UPDATE_POLICY_OVERWRITE = "overwrite"
UPDATE_POLICY_SKIP = "skip"


# 項目キーから項目定義へ引けるようにして更新判定を高速化する。
def _build_field_config(template) -> dict[str, Any]:
    return {field.field_key: field for field in template.fields}


# レコードの正規化済み JSON から画面/API 用の値辞書を復元する。
def _value_map(record: TemplateRecord) -> dict[str, str]:
    if record.normalized_data_json:
        try:
            loaded = json.loads(record.normalized_data_json)
            if isinstance(loaded, dict):
                return {key: "" if value is None else str(value) for key, value in loaded.items()}
        except json.JSONDecodeError:
            pass
    return {item.field_key: item.field_value for item in record.values}


# None を空文字へ寄せて DB 保存時の扱いを単純化する。
def _normalize_values(extracted: dict[str, Optional[str]]) -> dict[str, str]:
    return {key: value or "" for key, value in extracted.items()}


# 項目ごとの更新方式をここで一元適用する。
def apply_field_update_policy(
    current_values: dict[str, str],
    extracted: dict[str, Optional[str]],
    present_fields: set[str],
    field_config: dict[str, Any],
) -> dict[str, str]:
    updated = dict(current_values)
    for field_name, new_value in extracted.items():
        # 今回の JSON に存在しない項目は更新しない。
        if field_name not in present_fields:
            continue
        config = field_config.get(field_name)
        policy = getattr(config, "update_mode", UPDATE_POLICY_OVERWRITE)
        if policy == UPDATE_POLICY_SKIP and field_name in current_values:
            continue
        updated[field_name] = new_value or ""
    return updated


# ORM レコードを画面/API で扱いやすい dict へ変換する。
def _record_to_view(record: TemplateRecord) -> dict[str, Any]:
    return {
        "id": record.id,
        "template_name": record.template.template_name,
        "unique_key_value": record.unique_key_value,
        "received_at": record.received_at,
        "values": _value_map(record),
        "payload": MappingExtractor.load_payload(record.payload_json),
        "external_api_last_status": record.external_api_last_status,
        "external_api_last_response": record.external_api_last_response,
        "external_api_last_executed_at": record.external_api_last_executed_at,
    }


# 受信 JSON をテンプレート定義に従って新規作成または更新する。
def create_record_from_payload(session: Session, template, payload: dict[str, Any]):
    fields, mapping_dict = get_template_mapping_config(template)
    extractor = MappingExtractor()
    extracted = extractor.extract(payload, mapping_dict)
    present_fields = extractor.extract_present_fields(payload, mapping_dict)
    field_config = _build_field_config(template)
    received_at = datetime.utcnow()
    unique_key_value = extracted.get(template.unique_key_field) or ""

    if unique_key_value:
        existing_record = get_template_record_by_unique_key(session, template.id, unique_key_value)
        if existing_record:
            current_values = _value_map(existing_record)
            updated_values = apply_field_update_policy(current_values, extracted, present_fields, field_config)
            existing_record.payload_json = json.dumps(payload, ensure_ascii=False)
            existing_record.normalized_data_json = json.dumps(updated_values, ensure_ascii=False)
            existing_record.received_at = received_at
            set_record_values(session, existing_record, updated_values)
            session.flush()
            return existing_record, False

    normalized_values = _normalize_values(extracted)
    record = TemplateRecord(
        template_id=template.id,
        unique_key_value=unique_key_value,
        payload_json=json.dumps(payload, ensure_ascii=False),
        normalized_data_json=json.dumps(normalized_values, ensure_ascii=False),
        received_at=received_at,
    )
    created = create_template_record(session, record)
    set_record_values(session, created, normalized_values)
    return created, True


# 詳細画面や詳細 API 用の単一取得。
def get_record_detail(session: Session, template, record_id: int):
    record = get_template_record_by_id(session, template.id, record_id)
    if not record:
        return None, None
    return record, _record_to_view(record)


# 一覧検索結果を画面/API 向けに返す。
def search_records(session: Session, template, filters: dict, page: int, page_size: int):
    records, total = list_template_records(session, template.id, filters, page, page_size)
    return [_record_to_view(record) for record in records], total


# エクスポート用に最大件数付きで取得する。
def export_records(session: Session, template, filters: dict, limit: int):
    return [_record_to_view(record) for record in list_template_records_for_export(session, template.id, filters, limit)]


# 保存済み payload を使って正規化内容を再生成する。
def resync_records(session: Session, template):
    _, mapping_dict = get_template_mapping_config(template)
    extractor = MappingExtractor()
    return resync_template_records(session, template.id, extractor, mapping_dict)


# 手動実行ボタンから外部 API を POST する。
def execute_external_api(session: Session, template, record_id: int) -> tuple[bool, str]:
    record = get_template_record_by_id(session, template.id, record_id)
    if not record:
        return False, "Record not found"
    if not template.external_api_enabled or not template.external_api_url:
        return False, "External API is not configured"

    values = _value_map(record)
    payload = json.loads(record.payload_json)
    template_body = json.loads(template.external_api_body_json or "{}")
    headers = json.loads(template.external_api_headers_json or "{}")

    body = _replace_placeholders(template_body, values, payload)
    req = urllib_request.Request(
        template.external_api_url,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    executed_at = datetime.utcnow()
    try:
        with urllib_request.urlopen(req, timeout=30) as response:
            response_body = response.read().decode("utf-8", errors="replace")
            record.external_api_last_status = f"success:{response.status}"
            record.external_api_last_response = response_body[:2000]
            record.external_api_last_executed_at = executed_at
            session.flush()
            return True, record.external_api_last_status
    except Exception as exc:  # pragma: no cover - network dependent
        record.external_api_last_status = "failed"
        record.external_api_last_response = str(exc)[:2000]
        record.external_api_last_executed_at = executed_at
        session.flush()
        return False, str(exc)


# body テンプレート中のプレースホルダを実レコード値へ展開する。
def _replace_placeholders(value: Any, values: dict[str, str], payload: dict[str, Any]):
    if isinstance(value, dict):
        return {key: _replace_placeholders(item, values, payload) for key, item in value.items()}
    if isinstance(value, list):
        return [_replace_placeholders(item, values, payload) for item in value]
    if isinstance(value, str):
        replaced = value
        for field_key, field_value in values.items():
            replaced = replaced.replace(f"{{{{{field_key}}}}}", field_value)
        replaced = replaced.replace("{{payload_json}}", json.dumps(payload, ensure_ascii=False))
        return replaced
    return value

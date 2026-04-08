import json
from collections.abc import Sequence
from typing import Optional

from sqlalchemy import String, cast, exists, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.template_record import TemplateRecord
from app.models.template_record_value import TemplateRecordValue


# 新規レコードを永続化し、採番済み ID を利用できる状態にする。
def create_template_record(session: Session, record: TemplateRecord) -> TemplateRecord:
    session.add(record)
    session.flush()
    return record


# テンプレート配下の単一レコードを詳細取得する。
def get_template_record_by_id(session: Session, template_id: int, record_id: int) -> Optional[TemplateRecord]:
    stmt = (
        select(TemplateRecord)
        .options(selectinload(TemplateRecord.values))
        .where(TemplateRecord.template_id == template_id, TemplateRecord.id == record_id)
    )
    return session.scalars(stmt).first()


# 一意キーで既存レコードを探し、アップサート判定に使う。
def get_template_record_by_unique_key(session: Session, template_id: int, unique_key_value: str) -> Optional[TemplateRecord]:
    stmt = (
        select(TemplateRecord)
        .options(selectinload(TemplateRecord.values))
        .where(TemplateRecord.template_id == template_id, TemplateRecord.unique_key_value == unique_key_value)
        .order_by(TemplateRecord.id.desc())
    )
    return session.scalars(stmt).first()


# 正規化済み項目値テーブルをレコード内容に合わせて更新する。
def set_record_values(session: Session, record: TemplateRecord, values: dict[str, str]) -> None:
    current = {item.field_key: item for item in record.values}
    for field_key, field_value in values.items():
        if field_key in current:
            current[field_key].field_value = field_value
        else:
            record.values.append(TemplateRecordValue(field_key=field_key, field_value=field_value))
    session.flush()


# 項目別検索を EXISTS で組み立てるための共通条件。
def _filter_exists(field_key: str, value: str):
    return exists(
        select(TemplateRecordValue.id).where(
            TemplateRecordValue.record_id == TemplateRecord.id,
            TemplateRecordValue.field_key == field_key,
            cast(TemplateRecordValue.field_value, String).ilike(f"%{value}%"),
        )
    )


# 一覧検索用の where 句をテンプレート共通ロジックとして生成する。
def build_record_filters(template_id: int, filters: dict) -> list:
    conditions = [TemplateRecord.template_id == template_id]
    for field_key, value in filters.items():
        if field_key in {"keyword", "date_from", "date_to", "template_name"}:
            continue
        if value:
            conditions.append(_filter_exists(field_key, value))
    if filters.get("keyword"):
        keyword = filters["keyword"]
        conditions.append(
            (TemplateRecord.payload_json.ilike(f"%{keyword}%"))
            | (TemplateRecord.normalized_data_json.ilike(f"%{keyword}%"))
            | (TemplateRecord.unique_key_value.ilike(f"%{keyword}%"))
        )
    if filters.get("date_from"):
        conditions.append(TemplateRecord.received_at >= filters["date_from"])
    if filters.get("date_to"):
        conditions.append(TemplateRecord.received_at <= filters["date_to"])
    return conditions


# 画面一覧向けのページング付き取得。
def list_template_records(session: Session, template_id: int, filters: dict, page: int, page_size: int) -> tuple[Sequence[TemplateRecord], int]:
    conditions = build_record_filters(template_id, filters)
    stmt = select(TemplateRecord).options(selectinload(TemplateRecord.values)).where(*conditions)
    count_stmt = select(func.count(TemplateRecord.id)).where(*conditions)
    stmt = stmt.order_by(TemplateRecord.received_at.desc(), TemplateRecord.id.desc())
    stmt = stmt.offset((page - 1) * page_size).limit(page_size)
    return list(session.scalars(stmt).all()), int(session.scalar(count_stmt) or 0)


# 出力用の最大件数付き取得。
def list_template_records_for_export(session: Session, template_id: int, filters: dict, limit: int) -> Sequence[TemplateRecord]:
    conditions = build_record_filters(template_id, filters)
    stmt = (
        select(TemplateRecord)
        .options(selectinload(TemplateRecord.values))
        .where(*conditions)
        .order_by(TemplateRecord.received_at.desc(), TemplateRecord.id.desc())
        .limit(limit)
    )
    return list(session.scalars(stmt).all())


# 保存済み payload から正規化データを再生成する保守用処理。
def resync_template_records(session: Session, template_id: int, extractor, mappings: dict[str, str]) -> int:
    stmt = select(TemplateRecord).options(selectinload(TemplateRecord.values)).where(TemplateRecord.template_id == template_id)
    records = list(session.scalars(stmt).all())
    for record in records:
        payload = extractor.load_payload(record.payload_json)
        extracted = extractor.extract(payload, mappings)
        normalized = {key: value or "" for key, value in extracted.items()}
        record.normalized_data_json = json.dumps(normalized, ensure_ascii=False)
        set_record_values(session, record, normalized)
    session.flush()
    return len(records)

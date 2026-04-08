from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.core.auth import verify_api_key
from app.core.config import settings
from app.core.database import get_db
from app.repositories.template_repository import (
    get_default_template,
    get_template_by_api_name,
    get_template_by_name,
    list_templates,
    upsert_template,
)
from app.services.export_service import render_csv, render_json
from app.services.mapping_service import dump_template_spec, get_template_mapping_config, load_template_spec
from app.services.record_service import create_record_from_payload, export_records, get_record_detail, search_records

router = APIRouter(prefix="/api/v1", tags=["api"])


# API 入力値からテンプレート名または API 名で対象テンプレートを解決する。
def resolve_template(db: Session, selector: Optional[str]):
    if selector:
        template = get_template_by_name(db, selector)
        if template:
            return template
        return get_template_by_api_name(db, selector)
    return get_default_template(db)


# 一覧 API / 出力 API で共通利用する検索条件組み立て。
def build_filters(request: Request, template) -> dict:
    filters = {"keyword": request.query_params.get("keyword") or None}
    for field in template.fields:
        filters[field.field_key] = request.query_params.get(field.field_key) or None
    for field in ["date_from", "date_to"]:
        raw = request.query_params.get(field)
        filters[field] = datetime.fromisoformat(raw) if raw else None
    return filters


# 利用可能なテンプレート一覧を返す。
@router.get("/templates")
def get_templates(db: Session = Depends(get_db)):
    return {
        "items": [
            {
                "template_name": template.template_name,
                "api_name": template.api_name,
                "unique_key_field": template.unique_key_field,
            }
            for template in list_templates(db)
        ]
    }


# テンプレート JSON をアップロードして登録または更新する。
@router.post("/templates/upload", dependencies=[Depends(verify_api_key)])
async def upload_template_json(file: UploadFile = File(...), db: Session = Depends(get_db)):
    spec = load_template_spec(await file.read())
    template = upsert_template(db, dump_template_spec(spec))
    db.commit()
    return {"message": "uploaded", "template_name": template.template_name, "api_name": template.api_name}


# テンプレートに応じて JSON レコードを受信する。
@router.post("/records/{template_name}", dependencies=[Depends(verify_api_key)])
def create_record(template_name: str, payload: dict[str, Any], response: Response, db: Session = Depends(get_db)):
    template = resolve_template(db, template_name)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    record, created = create_record_from_payload(db, template, payload)
    db.commit()
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return {
        "id": record.id,
        "message": "created" if created else "updated",
        "template_name": template.template_name,
        "api_name": template.api_name,
    }


# テンプレートに応じた一覧検索 API。
@router.get("/records")
def get_records(
    request: Request,
    template_name: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=settings.page_size_default, ge=1, le=200),
    db: Session = Depends(get_db),
):
    template = resolve_template(db, template_name)
    if template is None:
        return {"template_name": None, "fields": [], "items": [], "page": page, "page_size": page_size, "total": 0}
    fields, _ = get_template_mapping_config(template)
    records, total = search_records(db, template, build_filters(request, template), page, page_size)
    return {
        "template_name": template.template_name,
        "api_name": template.api_name,
        "fields": [{"field_key": field.field_key, "display_name": field.display_name} for field in fields],
        "items": records,
        "page": page,
        "page_size": page_size,
        "total": total,
    }


# CSV 形式でダウンロードさせる。
@router.get("/records/export.csv")
def export_csv(
    request: Request,
    template_name: Optional[str] = None,
    db: Session = Depends(get_db),
):
    template = resolve_template(db, template_name)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    content = render_csv(template, list(export_records(db, template, build_filters(request, template), settings.export_max_rows)))
    filename = f"{template.api_name}.csv"
    headers = {"Content-Disposition": f"attachment; filename={filename}", "Cache-Control": "no-store"}
    return Response(content=content.encode("utf-8"), media_type="application/octet-stream", headers=headers)


# JSON 形式でダウンロードさせる。
@router.get("/records/export.json")
def export_json_file(
    request: Request,
    template_name: Optional[str] = None,
    db: Session = Depends(get_db),
):
    template = resolve_template(db, template_name)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    content = render_json(template, list(export_records(db, template, build_filters(request, template), settings.export_max_rows)))
    filename = f"{template.api_name}.json"
    headers = {"Content-Disposition": f"attachment; filename={filename}", "Cache-Control": "no-store"}
    return Response(content=content.encode("utf-8"), media_type="application/octet-stream", headers=headers)


# 単一レコード詳細 API。
@router.get("/records/{template_name}/{record_id}")
def get_record(template_name: str, record_id: int, db: Session = Depends(get_db)):
    template = resolve_template(db, template_name)
    if template is None:
        raise HTTPException(status_code=404, detail="Template not found")
    record, payload = get_record_detail(db, template, record_id)
    if not record or payload is None:
        raise HTTPException(status_code=404, detail="Record not found")
    return payload

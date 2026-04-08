import json
from datetime import datetime
from typing import Optional
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.repositories.template_repository import get_template_by_name, list_templates
from app.services.mapping_service import get_selected_template, get_template_mapping_config
from app.services.record_service import execute_external_api, get_record_detail, search_records

router = APIRouter(tags=["web"])
templates = Jinja2Templates(directory="app/templates")


def build_filters(request: Request, template) -> dict:
    values = {"template_name": template.template_name, "keyword": request.query_params.get("keyword") or None}
    for field in template.fields:
        values[field.field_key] = request.query_params.get(field.field_key) or None
    for field in ["date_from", "date_to"]:
        raw = request.query_params.get(field)
        values[field] = datetime.fromisoformat(raw) if raw else None
    return values


def build_query_without_paging(request: Request) -> str:
    params = [(key, value) for key, value in request.query_params.multi_items() if key not in {"page", "page_size"}]
    return urlencode(params)


def build_current_url(request: Request) -> str:
    query = request.url.query
    return f"{request.url.path}?{query}" if query else request.url.path


@router.get("/")
def root():
    return RedirectResponse(url="/records")


@router.get("/records")
def records_page(
    request: Request,
    template_name: Optional[str] = None,
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=settings.page_size_default, ge=1, le=200),
    db: Session = Depends(get_db),
):
    available_templates = list_templates(db)
    selected_template = get_selected_template(db, template_name)
    if selected_template is None:
        return templates.TemplateResponse(request, "records.html", {"app_name": settings.app_name, "records": [], "available_templates": [], "selected_template": None, "fields": [], "filters": {}, "query_without_paging": "", "auto_refresh_url": "/records", "page": 1, "page_size": page_size, "total": 0, "has_prev": False, "has_next": False, "auto_refresh_seconds": 30, "external_api_enabled": False})
    fields, _ = get_template_mapping_config(selected_template)
    filters = build_filters(request, selected_template)
    records, total = search_records(db, selected_template, filters, page, page_size)
    display_filters = {}
    for key, value in filters.items():
        if isinstance(value, datetime):
            display_filters[key] = value.strftime("%Y-%m-%dT%H:%M")
        else:
            display_filters[key] = value or ""
    return templates.TemplateResponse(
        request,
        "records.html",
        {
            "app_name": settings.app_name,
            "records": records,
            "available_templates": available_templates,
            "selected_template": selected_template,
            "fields": fields,
            "filters": display_filters,
            "query_without_paging": build_query_without_paging(request),
            "auto_refresh_url": build_current_url(request),
            "page": page,
            "page_size": page_size,
            "total": total,
            "has_prev": page > 1,
            "has_next": page * page_size < total,
            "auto_refresh_seconds": 30,
            "external_api_enabled": selected_template.external_api_enabled and bool(selected_template.external_api_url),
        },
    )


@router.get("/records/{record_id}")
def record_detail_page(request: Request, record_id: int, template_name: Optional[str] = None, db: Session = Depends(get_db)):
    template = get_selected_template(db, template_name)
    if template is None:
        return templates.TemplateResponse(request, "record_detail.html", {"app_name": settings.app_name, "record": None, "record_view": None, "fields": [], "payload_pretty": "{}", "selected_template": None}, status_code=404)
    record, record_view = get_record_detail(db, template, record_id)
    return templates.TemplateResponse(
        request,
        "record_detail.html",
        {
            "app_name": settings.app_name,
            "record": record,
            "record_view": record_view,
            "fields": sorted(template.fields, key=lambda item: (item.sort_order, item.id)),
            "selected_template": template,
            "payload_pretty": json.dumps(record_view["payload"] if record_view else {}, ensure_ascii=False, indent=2),
        },
        status_code=404 if record is None else 200,
    )


@router.post("/records/{record_id}/execute-external")
async def execute_external(request: Request, record_id: int, db: Session = Depends(get_db)):
    form = await request.form()
    template_name = str(form.get("template_name") or "")
    redirect_query = str(form.get("return_query") or "")
    template = get_template_by_name(db, template_name)
    if template is not None:
        execute_external_api(db, template, record_id)
        db.commit()
    redirect_url = f"/records?{redirect_query}" if redirect_query else "/records"
    return RedirectResponse(url=redirect_url, status_code=303)

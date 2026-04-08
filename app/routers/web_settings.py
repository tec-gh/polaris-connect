import json
from json import JSONDecodeError
from typing import Optional

from fastapi import APIRouter, Depends, Request, UploadFile
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.auth import require_admin
from app.core.config import settings
from app.core.database import get_db
from app.models.app_setting import AppSetting
from app.repositories.template_repository import delete_template, get_selected_template, list_templates, upsert_template
from app.schemas.template import dump_template_spec, load_template_spec
from app.services.app_setting_service import get_sftp_settings, save_app_settings
from app.services.mapping_service import resync_template_records
from app.services.setting_history_service import record_setting_history

router = APIRouter(tags=["settings"])
templates = Jinja2Templates(directory="app/templates")


def render_mappings_page(
    request: Request,
    db: Session,
    template_name: Optional[str] = None,
    error_message: str = "",
    success_message: str = "",
):
    available_templates = list_templates(db)
    selected_template = get_selected_template(db, template_name)
    return templates.TemplateResponse(
        "settings_mappings.html",
        {
            "request": request,
            "app_name": settings.app_name,
            "available_templates": available_templates,
            "selected_template": selected_template,
            "fields": sorted(selected_template.fields, key=lambda item: (item.sort_order, item.id)) if selected_template else [],
            "sftp_settings": get_sftp_settings(db),
            "error_message": error_message,
            "success_message": success_message,
        },
        status_code=400 if error_message else 200,
    )


@router.get("/settings/mappings")
def mappings_page(request: Request, template_name: Optional[str] = None, db: Session = Depends(get_db), _: str = Depends(require_admin)):
    return render_mappings_page(request, db, template_name=template_name)


@router.post("/settings/templates/upload")
async def upload_template(request: Request, db: Session = Depends(get_db), _: str = Depends(require_admin)):
    form = await request.form()
    upload = form.get("template_file")
    current_template_name = str(form.get("template_name") or "").strip() or None
    if not isinstance(upload, UploadFile):
        return render_mappings_page(request, db, template_name=current_template_name, error_message="??????JSON??????????????")

    raw = await upload.read()
    if not raw:
        return render_mappings_page(request, db, template_name=current_template_name, error_message="??????JSON?????????????????????")

    try:
        spec = load_template_spec(raw)
        template = upsert_template(db, dump_template_spec(spec))
        db.commit()
        return RedirectResponse(url=f"/settings/mappings?template_name={template.template_name}", status_code=303)
    except JSONDecodeError as exc:
        db.rollback()
        return render_mappings_page(request, db, template_name=current_template_name, error_message=f"JSON??????????: {exc}")
    except ValidationError as exc:
        db.rollback()
        details = "; ".join(error.get("msg", "???????") for error in exc.errors())
        return render_mappings_page(request, db, template_name=current_template_name, error_message=f"?????????????: {details}")
    except Exception as exc:
        db.rollback()
        return render_mappings_page(request, db, template_name=current_template_name, error_message=f"???????????????: {exc}")


@router.post("/settings/mappings/save")
async def save_mappings(request: Request, db: Session = Depends(get_db), username: str = Depends(require_admin)):
    form = await request.form()
    template_name = str(form.get("template_name") or "").strip()
    selected_template = get_selected_template(db, template_name)
    if selected_template is None:
        return RedirectResponse(url="/settings/mappings", status_code=303)

    field_specs = []
    for field in sorted(selected_template.fields, key=lambda item: (item.sort_order, item.id)):
        field_specs.append(
            {
                "field_key": field.field_key,
                "display_name": str(form.get(f"display_name__{field.field_key}") or field.display_name).strip() or field.field_key,
                "json_path": str(form.get(f"json_path__{field.field_key}") or field.json_path).strip() or field.json_path,
                "is_visible": form.get(f"is_visible__{field.field_key}") == "on",
                "is_searchable": form.get(f"is_searchable__{field.field_key}") == "on",
                "is_exportable": form.get(f"is_exportable__{field.field_key}") == "on",
                "update_mode": "overwrite" if form.get(f"overwrite__{field.field_key}") == "on" else "skip",
                "sort_order": int(str(form.get(f"sort_order__{field.field_key}") or field.sort_order).strip() or field.sort_order),
            }
        )

    payload = {
        "template_name": str(form.get("template_name_value") or selected_template.template_name).strip() or selected_template.template_name,
        "api_name": str(form.get("api_name") or selected_template.api_name).strip() or selected_template.api_name,
        "unique_key_field": selected_template.unique_key_field,
        "external_api_enabled": form.get("external_api_enabled") == "on",
        "external_api_url": str(form.get("external_api_url") or "").strip(),
        "external_api_headers_json": str(form.get("external_api_headers_json") or "").strip(),
        "external_api_body_json": str(form.get("external_api_body_json") or "").strip(),
        "fields": field_specs,
    }

    before_state = selected_template.to_history_dict()
    updated = upsert_template(db, payload)
    db.commit()
    record_setting_history(
        db,
        username=username,
        event_type="template.update",
        target_type="template",
        target_key=updated.template_name,
        before_state=before_state,
        after_state=updated.to_history_dict(),
    )
    db.commit()
    return RedirectResponse(url=f"/settings/mappings?template_name={updated.template_name}", status_code=303)


@router.post("/settings/templates/delete")
async def delete_template_route(request: Request, db: Session = Depends(get_db), _: str = Depends(require_admin)):
    form = await request.form()
    template_name = str(form.get("template_name") or "").strip()
    selected_template = get_selected_template(db, template_name)
    if selected_template is not None:
        delete_template(db, selected_template)
        db.commit()
    remaining = list_templates(db)
    if remaining:
        return RedirectResponse(url=f"/settings/mappings?template_name={remaining[0].template_name}", status_code=303)
    return RedirectResponse(url="/settings/mappings", status_code=303)


@router.post("/settings/mappings/resync")
def run_resync(request: Request, db: Session = Depends(get_db), _: str = Depends(require_admin)):
    template_name = request.query_params.get("template_name")
    if not template_name:
        form_template_name = request.query_params.get("template_name")
        template_name = form_template_name or None
    if template_name:
        resync_template_records(db, template_name)
        db.commit()
    return RedirectResponse(url="/settings/mappings", status_code=303)


@router.post("/settings/sftp/save")
async def save_sftp_settings_route(request: Request, db: Session = Depends(get_db), _: str = Depends(require_admin)):
    form = await request.form()
    template_name = str(form.get("template_name") or "").strip() or None
    save_app_settings(
        db,
        {
            AppSetting.KEY_SFTP_HOST: str(form.get("sftp_host") or "").strip(),
            AppSetting.KEY_SFTP_USERNAME: str(form.get("sftp_username") or "").strip(),
            AppSetting.KEY_SFTP_PASSWORD: str(form.get("sftp_password") or "").strip(),
            AppSetting.KEY_SFTP_FREQUENCY_MINUTES: str(form.get("sftp_frequency_minutes") or "5").strip() or "5",
            AppSetting.KEY_SFTP_REMOTE_PATH: str(form.get("sftp_remote_path") or "").strip(),
        },
    )
    db.commit()
    redirect_url = "/settings/mappings"
    if template_name:
        redirect_url = f"/settings/mappings?template_name={template_name}"
    return RedirectResponse(url=redirect_url, status_code=303)

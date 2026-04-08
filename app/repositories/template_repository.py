import json
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.template_definition import TemplateDefinition
from app.models.template_field import TemplateField


DEFAULT_TEMPLATE_SPEC = {
    "template_name": "sample_legacy_records",
    "api_name": "sample_legacy_records",
    "unique_key_field": "hostname",
    "external_api": {
        "enabled": False,
        "url": "",
        "headers": {},
        "body": {},
    },
    "fields": [
        {"field_key": "hostname", "display_name": "Hostname", "json_path": "hostname", "is_visible": True, "is_searchable": True, "is_exportable": True, "update_mode": "skip", "sort_order": 1},
        {"field_key": "ipaddress", "display_name": "IP Address", "json_path": "ipaddress", "is_visible": True, "is_searchable": True, "is_exportable": True, "update_mode": "skip", "sort_order": 2},
        {"field_key": "area", "display_name": "Area", "json_path": "area", "is_visible": True, "is_searchable": True, "is_exportable": True, "update_mode": "skip", "sort_order": 3},
        {"field_key": "building", "display_name": "Building", "json_path": "building", "is_visible": True, "is_searchable": True, "is_exportable": True, "update_mode": "skip", "sort_order": 4},
        {"field_key": "category", "display_name": "Category", "json_path": "category", "is_visible": True, "is_searchable": True, "is_exportable": True, "update_mode": "skip", "sort_order": 5},
        {"field_key": "model", "display_name": "Model", "json_path": "model", "is_visible": True, "is_searchable": True, "is_exportable": True, "update_mode": "skip", "sort_order": 6},
        {"field_key": "ping_test_result", "display_name": "Ping Test Result", "json_path": "ping_test_result", "is_visible": True, "is_searchable": True, "is_exportable": True, "update_mode": "overwrite", "sort_order": 7},
        {"field_key": "exec_result", "display_name": "Exec Result", "json_path": "exec_result", "is_visible": True, "is_searchable": True, "is_exportable": True, "update_mode": "overwrite", "sort_order": 8},
    ],
}


def list_templates(session: Session) -> list[TemplateDefinition]:
    stmt = select(TemplateDefinition).options(selectinload(TemplateDefinition.fields)).order_by(TemplateDefinition.template_name.asc())
    return list(session.scalars(stmt).all())


def get_template_by_name(session: Session, template_name: str) -> Optional[TemplateDefinition]:
    stmt = select(TemplateDefinition).options(selectinload(TemplateDefinition.fields)).where(TemplateDefinition.template_name == template_name)
    return session.scalars(stmt).first()


def get_template_by_api_name(session: Session, api_name: str) -> Optional[TemplateDefinition]:
    stmt = select(TemplateDefinition).options(selectinload(TemplateDefinition.fields)).where(TemplateDefinition.api_name == api_name)
    return session.scalars(stmt).first()


def get_default_template(session: Session) -> Optional[TemplateDefinition]:
    templates = list_templates(session)
    return templates[0] if templates else None


def delete_template(session: Session, template: TemplateDefinition) -> None:
    session.delete(template)
    session.flush()


def upsert_template(session: Session, spec: dict) -> TemplateDefinition:
    existing = get_template_by_name(session, spec["template_name"])
    external_api = spec.get("external_api") or {}
    if existing is None:
        existing = TemplateDefinition(
            template_name=spec["template_name"],
            api_name=spec["api_name"],
            unique_key_field=spec.get("unique_key_field", "hostname") or "hostname",
            external_api_enabled=bool(external_api.get("enabled")),
            external_api_url=str(external_api.get("url") or ""),
            external_api_headers_json=json.dumps(external_api.get("headers") or {}, ensure_ascii=False),
            external_api_body_json=json.dumps(external_api.get("body") or {}, ensure_ascii=False),
        )
        session.add(existing)
        session.flush()
    else:
        existing.template_name = spec["template_name"]
        existing.api_name = spec["api_name"]
        existing.unique_key_field = spec.get("unique_key_field", "hostname") or "hostname"
        existing.external_api_enabled = bool(external_api.get("enabled"))
        existing.external_api_url = str(external_api.get("url") or "")
        existing.external_api_headers_json = json.dumps(external_api.get("headers") or {}, ensure_ascii=False)
        existing.external_api_body_json = json.dumps(external_api.get("body") or {}, ensure_ascii=False)

    existing.fields.clear()
    session.flush()
    for field in spec.get("fields", []):
        existing.fields.append(
            TemplateField(
                field_key=field["field_key"],
                display_name=field["display_name"],
                json_path=field["json_path"],
                is_visible=bool(field.get("is_visible", True)),
                is_searchable=bool(field.get("is_searchable", True)),
                is_exportable=bool(field.get("is_exportable", True)),
                update_mode=str(field.get("update_mode", "overwrite")),
                sort_order=int(field.get("sort_order", 0)),
            )
        )
    session.flush()
    return existing

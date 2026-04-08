import json
from typing import Any, Dict, Optional, Union

from sqlalchemy.orm import Session

from app.repositories.template_repository import DEFAULT_TEMPLATE_SPEC, get_default_template, get_template_by_name, list_templates, upsert_template
from app.schemas.template import TemplateSpec


# JSON payload からテンプレート定義に従って値を抜き出す責務を持つ。
class MappingExtractor:
    @staticmethod
    def load_payload(payload_json: str) -> dict[str, Any]:
        loaded = json.loads(payload_json)
        return loaded if isinstance(loaded, dict) else {"value": loaded}

    @staticmethod
    def has_path(payload: dict[str, Any], path: str) -> bool:
        current: Any = payload
        for part in path.split("."):
            if not isinstance(current, dict) or part not in current:
                return False
            current = current[part]
        return True

    @staticmethod
    def get_value_by_path(payload: dict[str, Any], path: str) -> Optional[str]:
        current: Any = payload
        for part in path.split("."):
            if not isinstance(current, dict) or part not in current:
                return None
            current = current[part]
        if current is None:
            return None
        # オブジェクトや配列は JSON 文字列として保存しておく。
        if isinstance(current, (dict, list)):
            return json.dumps(current, ensure_ascii=False)
        return str(current)

    def extract(self, payload: dict[str, Any], mappings: Dict[str, str]) -> Dict[str, Optional[str]]:
        return {field_key: self.get_value_by_path(payload, path) for field_key, path in mappings.items()}

    def extract_present_fields(self, payload: dict[str, Any], mappings: Dict[str, str]) -> set[str]:
        return {field_key for field_key, path in mappings.items() if self.has_path(payload, path)}


# 文字列、bytes、dict のいずれで受けてもテンプレート定義へ変換する。
def load_template_spec(data: Union[str, bytes, dict[str, Any]]) -> TemplateSpec:
    if isinstance(data, bytes):
        parsed = json.loads(data.decode("utf-8"))
    elif isinstance(data, str):
        parsed = json.loads(data)
    else:
        parsed = data
    if hasattr(TemplateSpec, "model_validate"):
        return TemplateSpec.model_validate(parsed)
    return TemplateSpec.parse_obj(parsed)


# Pydantic のバージョン差異を吸収しつつ dict 化する。
def dump_template_spec(spec: TemplateSpec) -> dict[str, Any]:
    if hasattr(spec, "model_dump"):
        return spec.model_dump()
    return spec.dict()


# テンプレート未登録時に既定テンプレートを投入する。
def ensure_default_template(session: Session) -> None:
    if list_templates(session):
        return
    upsert_template(session, DEFAULT_TEMPLATE_SPEC)


# 画面選択時に対象テンプレートを解決する。
def get_selected_template(session: Session, template_name: Optional[str]):
    if template_name:
        selected = get_template_by_name(session, template_name)
        if selected:
            return selected
    return get_default_template(session)


# 項目定義一覧と JSON パスマップをまとめて返す。
def get_template_mapping_config(template) -> tuple[list, dict[str, str]]:
    fields = sorted(template.fields, key=lambda item: (item.sort_order, item.id))
    return fields, {item.field_key: item.json_path for item in fields}

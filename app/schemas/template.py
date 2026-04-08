from typing import Any

from pydantic import BaseModel, Field


# テンプレート内の1項目分の定義を表す入力スキーマ。
class TemplateFieldItem(BaseModel):
    field_key: str = Field(min_length=1, max_length=64)
    display_name: str = Field(min_length=1, max_length=128)
    json_path: str = Field(min_length=1, max_length=255)
    is_visible: bool = True
    is_searchable: bool = True
    is_exportable: bool = True
    update_mode: str = "overwrite"
    sort_order: int = 0


# 手動実行する外部 API の接続情報と POST 本文定義。
class ExternalApiConfig(BaseModel):
    enabled: bool = False
    url: str = ""
    headers: dict[str, Any] = Field(default_factory=dict)
    body: dict[str, Any] = Field(default_factory=dict)


# ?????? JSON ?????????????????
class TemplateSpec(BaseModel):
    template_name: str = Field(min_length=1, max_length=64)
    api_name: str = Field(min_length=1, max_length=64)
    unique_key_field: str = Field(min_length=1, max_length=64)
    fields: list[TemplateFieldItem]
    external_api: ExternalApiConfig = Field(default_factory=ExternalApiConfig)

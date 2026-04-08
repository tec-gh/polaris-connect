import csv
import io
import json


def render_csv(template, records: list[dict]) -> str:
    field_order = [field for field in sorted(template.fields, key=lambda item: (item.sort_order, item.id)) if field.is_exportable]
    export_fields = [field.field_key for field in field_order]
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=["id", "received_at", *export_fields, "payload_json"])
    writer.writeheader()
    for record in records:
        row = {
            "id": record["id"],
            "received_at": record["received_at"],
            "payload_json": json.dumps(record["payload"], ensure_ascii=False),
        }
        for field in export_fields:
            row[field] = record["values"].get(field, "")
        writer.writerow(row)
    return output.getvalue()


def render_json(template, records: list[dict]) -> str:
    fields = [
        {
            "field_key": field.field_key,
            "display_name": field.display_name,
            "json_path": field.json_path,
            "is_visible": field.is_visible,
            "is_searchable": field.is_searchable,
            "is_exportable": field.is_exportable,
            "update_mode": field.update_mode,
            "sort_order": field.sort_order,
        }
        for field in sorted(template.fields, key=lambda item: (item.sort_order, item.id))
    ]
    payload = {
        "template_name": template.template_name,
        "api_name": template.api_name,
        "unique_key_field": template.unique_key_field,
        "fields": fields,
        "records": records,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2, default=str)

# Polaris Connect README

## 概要

`Polaris Connect` は、HTTP POST で受信した JSON を SQLite に保存し、ブラウザ上で一覧表示し、CSV / JSON 出力や SFTP 転送を行える FastAPI アプリケーションです。

本製品はテンプレート駆動方式です。テンプレート JSON により、次の内容を定義できます。

- テンプレート名
- 受信 API 名
- 一意キー項目
- 項目一覧
- 各項目の表示名
- 各項目の JSON パス
- 表示可否 / 検索可否 / 出力可否
- 更新方式 `overwrite` / `skip`
- 外部 API 実行設定

画面上ではテンプレートをドロップダウンで切り替えられ、レコード受信 API は `POST /api/v1/records/{template_name}` で利用します。

## 動作環境

- OS: RHEL 7.9
- Python: 3.9.10
- Web 実行環境: FastAPI + Uvicorn
- データベース: SQLite
- UI: Jinja2 テンプレート + ローカル Bootstrap 資材

依存パッケージは [requirements.txt](/d:/project/polaris_connect/requirements.txt) を参照してください。

## フォルダ構成

```text
polaris_connect/
  app/                 アプリケーション本体
  docs/                ドキュメント
  scripts/             補助スクリプト
  data/                SQLite DB 出力先
  requirements.txt     Python 依存関係
```

## 導入方法

### オンライン導入

```bash
cd /opt/polaris-connect
python3.9 -m pip install -r requirements.txt
```

### オフライン導入

インターネット接続可能な端末で wheel を取得します。

```bash
python3.9 -m pip download -r requirements.txt -d wheelhouse
```

取得した `wheelhouse/` を対象サーバへ持ち込み、次のように導入します。

```bash
cd /opt/polaris-connect
python3.9 -m pip install --no-index --find-links=wheelhouse -r requirements.txt
```

## 初期セットアップ

```bash
mkdir -p /opt/polaris-connect
cd /opt/polaris-connect
python3.9 scripts/init_db.py
```

必要に応じて環境変数を指定してください。

```bash
export APP_NAME="Polaris Connect"
export DATABASE_URL=sqlite:////opt/polaris-connect/data/app.db
export PAGE_SIZE_DEFAULT=20
export EXPORT_MAX_ROWS=10000
export ADMIN_USERNAME=admin
export ADMIN_PASSWORD=change_me
export API_KEY=changeme
export SFTP_HOST=
export SFTP_USERNAME=
export SFTP_PASSWORD=
export SFTP_FREQUENCY_MINUTES=60
export SFTP_REMOTE_PATH=records_export.json
```

## 起動方法

```bash
./scripts/start_app.sh
```

または直接起動します。

```bash
python3.9 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 主な URL

- `/health`: ヘルスチェック
- `/records`: レコード一覧画面
- `/records/{id}?template_name=<name>`: レコード詳細画面
- `/settings/mappings`: テンプレート / SFTP 設定画面
  - テンプレートの編集・再同期・削除を実行可能
- `/api/v1/templates`: テンプレート一覧 API
- `/api/v1/templates/upload`: テンプレートアップロード API
- `/api/v1/records/{template_name}`: レコード受信 API
- `/api/v1/records/export.csv?template_name=<name>`: CSV 出力
- `/api/v1/records/export.json?template_name=<name>`: JSON 出力

## 初期登録テンプレート

初期状態では、旧固定構造の `records` テーブル相当をテンプレート化した `sample_legacy_records` が登録されます。

- 一意キー: `hostname`
- 項目: `hostname`, `ipaddress`, `area`, `building`, `category`, `model`, `ping_test_result`, `exec_result`
- `ping_test_result` と `exec_result` は `overwrite`
- その他の項目は `skip`


## 外部からの JSON POST サンプル

`sample_legacy_records` へレコードを登録する例です。

```bash
curl -X POST \
  -H "Content-Type: application/json" \
  -H "X-API-Key: changeme" \
  -d '{
    "hostname": "sv-01",
    "ipaddress": "192.168.0.10",
    "area": "tokyo",
    "building": "dc-a",
    "category": "server",
    "model": "rx-1000",
    "ping_test_result": "success",
    "exec_result": "ok"
  }' \
  http://127.0.0.1:8000/api/v1/records/sample_legacy_records
```

API キーを無効にしている環境では `X-API-Key` ヘッダは不要です。

## `sample_legacy_records` のデータ構造

`sample_legacy_records` は、旧固定構造の `records` テーブルをテンプレート方式に置き換えたサンプルです。

### テンプレート定義の要点

- `template_name`: `sample_legacy_records`
- `api_name`: `sample_legacy_records`
- `unique_key_field`: `hostname`
- 項目数: 8

### 項目定義一覧

| field_key | display_name | json_path | update_mode |
| --- | --- | --- | --- |
| `hostname` | `Hostname` | `hostname` | `skip` |
| `ipaddress` | `IP Address` | `ipaddress` | `skip` |
| `area` | `Area` | `area` | `skip` |
| `building` | `Building` | `building` | `skip` |
| `category` | `Category` | `category` | `skip` |
| `model` | `Model` | `model` | `skip` |
| `ping_test_result` | `Ping Test Result` | `ping_test_result` | `overwrite` |
| `exec_result` | `Exec Result` | `exec_result` | `overwrite` |

### テンプレート JSON 例

```json
{
  "template_name": "sample_legacy_records",
  "api_name": "sample_legacy_records",
  "unique_key_field": "hostname",
  "external_api": {
    "enabled": false,
    "url": "",
    "headers": {},
    "body": {}
  },
  "fields": [
    {
      "field_key": "hostname",
      "display_name": "Hostname",
      "json_path": "hostname",
      "is_visible": true,
      "is_searchable": true,
      "is_exportable": true,
      "update_mode": "skip",
      "sort_order": 1
    },
    {
      "field_key": "ipaddress",
      "display_name": "IP Address",
      "json_path": "ipaddress",
      "is_visible": true,
      "is_searchable": true,
      "is_exportable": true,
      "update_mode": "skip",
      "sort_order": 2
    },
    {
      "field_key": "area",
      "display_name": "Area",
      "json_path": "area",
      "is_visible": true,
      "is_searchable": true,
      "is_exportable": true,
      "update_mode": "skip",
      "sort_order": 3
    },
    {
      "field_key": "building",
      "display_name": "Building",
      "json_path": "building",
      "is_visible": true,
      "is_searchable": true,
      "is_exportable": true,
      "update_mode": "skip",
      "sort_order": 4
    },
    {
      "field_key": "category",
      "display_name": "Category",
      "json_path": "category",
      "is_visible": true,
      "is_searchable": true,
      "is_exportable": true,
      "update_mode": "skip",
      "sort_order": 5
    },
    {
      "field_key": "model",
      "display_name": "Model",
      "json_path": "model",
      "is_visible": true,
      "is_searchable": true,
      "is_exportable": true,
      "update_mode": "skip",
      "sort_order": 6
    },
    {
      "field_key": "ping_test_result",
      "display_name": "Ping Test Result",
      "json_path": "ping_test_result",
      "is_visible": true,
      "is_searchable": true,
      "is_exportable": true,
      "update_mode": "overwrite",
      "sort_order": 7
    },
    {
      "field_key": "exec_result",
      "display_name": "Exec Result",
      "json_path": "exec_result",
      "is_visible": true,
      "is_searchable": true,
      "is_exportable": true,
      "update_mode": "overwrite",
      "sort_order": 8
    }
  ]
}
```

## テンプレート削除

設定画面 `/settings/mappings` では、選択中テンプレートを削除できます。

- 削除対象はテンプレート本体です
- 関連する項目定義と受信済みレコードも同時に削除されます
- 削除前には確認ダイアログが表示されます
- 削除後は、残っている別テンプレートへ切り替わるか、テンプレート未登録状態へ戻ります

## 補足

- SFTP 転送はテンプレートごとに JSON を出力して送信します。
- テンプレートが 1 件のみで、転送先パスが `.json` で終わる場合はそのパスをそのまま使います。
- テンプレートが複数ある場合はテンプレートごとにファイル名を自動生成します。

## 関連資料

- 詳細導入手順: [deployment.md](/d:/project/polaris_connect/docs/deployment.md)
- 設計書: [design.md](/d:/project/polaris_connect/docs/design.md)
- 構成情報: [current_structure.md](/d:/project/polaris_connect/docs/current_structure.md)

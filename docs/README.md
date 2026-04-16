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

## WSL2 での起動手順

Windows 端末上の WSL2 で `Polaris Connect` を動かす場合の手順です。

### 1. PowerShell を開く

- スタートメニューから `PowerShell` を起動します。
- `Windows PowerShell` / `PowerShell 7` のどちらでも構いません。

### 2. WSL2 を起動する

PowerShell で以下を実行します。

```powershell
wsl
```

### 3. プロジェクトフォルダへ移動する

WSL 上で以下を実行します。

```bash
cd /mnt/d/project/polaris_connect
```

### 4. Python 実行環境を確認する

```bash
python3 --version
```

### 5. 必要なパッケージを導入する

初回のみ実行します。

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip
```

### 6. 仮想環境を作成する

初回のみ実行します。

```bash
python3 -m venv .venv
```

### 7. 仮想環境を有効化する

```bash
source .venv/bin/activate
```

### 8. 依存ライブラリを導入する

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### 9. データベースを初期化する

```bash
python scripts/init_db.py
```

### 10. アプリケーションを起動する

```bash
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 11. Windows 側のブラウザでアクセスする

- `http://localhost:8000`
- `http://localhost:8000/records`
- `http://localhost:8000/settings/mappings`
- `http://localhost:8000/health`

### 12. 停止する

WSL 上で `Ctrl + C` を押します。

### 次回以降の起動手順

```powershell
wsl
```

```bash
cd /mnt/d/project/polaris_connect
source .venv/bin/activate
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 外部API連携のローカル確認

外部 API 連携を実サービスへ接続する前に、手元のモック API で安全に確認できます。

### 1. モック API を起動する

WSL 上で `Polaris Connect` の仮想環境を有効化し、次を実行します。

```bash
source .venv/bin/activate
python scripts/mock_external_api.py --host 127.0.0.1 --port 9000 --path /mock
```

このコマンドで、以下の URL へ POST を受け付けます。

```text
http://127.0.0.1:9000/mock
```

受信した内容は、次のファイルへ保存されます。

```text
data/mock_external_api_last_request.json
```

### 2. 設定画面で外部 API を設定する

管理画面 `/settings/mappings` で対象テンプレートを選択し、以下を設定します。

- `外部 API 有効化`: ON
- `外部 API URL`: `http://127.0.0.1:9000/mock`
- `外部 API ヘッダ JSON`: 必要に応じて設定
- `外部 API ボディ JSON`: 送信する JSON を設定

`外部 API ヘッダ JSON` の記入例:

```json
{
  "X-Test-Header": "polaris-connect",
  "X-Template-Name": "sample_api_test"
}
```

`外部 API ボディ JSON` の記入例:

```json
{
  "hostname": "{{hostname}}",
  "payload": "{{payload_json}}"
}
```

### 3. 一覧画面から実行する

`/records?template_name=<template_name>` を開き、対象レコードの `実行` ボタンを押します。

### 4. モック API の受信結果を確認する

モック API が受信に成功すると、`data/mock_external_api_last_request.json` に内容が保存されます。

確認ポイント:

- `hostname` が期待どおりに置換されているか
- `{{payload_json}}` に元の JSON が入っているか
- 設定したヘッダが送信されているか
- Polaris Connect 側の実行結果が成功になっているか

### 5. 失敗系も確認する

モック API を `500` 応答で起動すると、失敗時の動作も確認できます。

```bash
python scripts/mock_external_api.py --host 127.0.0.1 --port 9000 --path /mock --status 500
```
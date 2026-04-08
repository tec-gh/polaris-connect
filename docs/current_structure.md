# 現在の構成情報

## 概要

この文書は、`polaris_connect` の現在のディレクトリ構成と、各プログラムの役割を整理したものです。  
Polaris Connect はテンプレート駆動方式に統一されており、JSON テンプレート定義に基づいて受信・保存・検索・出力を行います。

## core

### 役割・概要

`core` は共通基盤層です。設定、DB 接続、認証などの横断処理を持ちます。

#### `app/core/config.py`
- 環境変数から Polaris Connect の設定を読み込みます。
- アプリ名、DB、認証、SFTP 設定の入口です。

#### `app/core/database.py`
- SQLAlchemy の `Base`、`engine`、`SessionLocal` を定義します。
- SQLite 用の保存先作成とセッション管理を担当します。

#### `app/core/auth.py`
- 管理画面向け Basic 認証と API Key 認証を提供します。

## models

### 役割・概要

`models` はテンプレート方式専用の ORM モデル群です。

#### `app/models/template_definition.py`
- テンプレート名、API 名、一意キー、外部 API 設定を保持します。

#### `app/models/template_field.py`
- 項目定義、JSON パス、表示設定、更新方式を保持します。

#### `app/models/template_record.py`
- 受信レコード本体、payload、正規化 JSON、外部 API 実行結果を保持します。

#### `app/models/template_record_value.py`
- 項目ごとの分解済み値を保持し、検索を支えます。

#### `app/models/app_setting.py`
- SFTP などのアプリ設定をキー・バリュー形式で保持します。

#### `app/models/__init__.py`
- 現行モデルの import 集約です。

## repositories

### 役割・概要

`repositories` は DB アクセス層です。

#### `app/repositories/template_repository.py`
- テンプレート定義の取得・登録・更新・削除を担当します。
- 旧 records 構造をサンプル化した初期テンプレート定義もここにあります。

#### `app/repositories/template_record_repository.py`
- テンプレートレコードの検索、一覧、出力、再同期を担当します。

#### `app/repositories/app_setting_repository.py`
- アプリ設定の取得と upsert を担当します。

## routers

### 役割・概要

`routers` は FastAPI のエンドポイント定義です。

#### `app/routers/api_records.py`
- テンプレート API、レコード受信 API、一覧 API、出力 API を提供します。

#### `app/routers/web_records.py`
- レコード一覧、検索、詳細、自動更新、外部 API 実行 UI を提供します。

#### `app/routers/web_settings.py`
- テンプレートアップロード、編集、削除、SFTP 設定、再同期 UI を提供します。

#### `app/routers/health.py`
- ヘルスチェックを提供します。

## schemas

### 役割・概要

`schemas` はテンプレート方式の入力バリデーション定義です。

#### `app/schemas/template.py`
- テンプレート JSON の仕様を Pydantic で表現します。

## services

### 役割・概要

`services` は業務ロジック層です。

#### `app/services/mapping_service.py`
- JSON からの値抽出、テンプレート読込、既定テンプレート投入を担当します。

#### `app/services/record_service.py`
- レコードのアップサート、検索、再同期、外部 API 実行を担当します。

#### `app/services/export_service.py`
- CSV / JSON 出力を生成します。

#### `app/services/app_setting_service.py`
- SFTP 設定の取得・保存を担当します。

#### `app/services/sftp_transfer_service.py`
- 定期 SFTP 転送を担当します。

## static

### 役割・概要

`static` はローカル配信する CSS / JS / Bootstrap 資材です。

#### `app/static/css/app.css`
- Polaris Connect の画面スタイルを定義します。

#### `app/static/js/app.js`
- 共通 JavaScript 置き場です。

#### `app/static/vendor/bootstrap/bootstrap.min.css`
- ローカル Bootstrap スタイルです。

#### `app/static/vendor/bootstrap/bootstrap.bundle.min.js`
- ローカル Bootstrap JavaScript です。

## templates

### 役割・概要

`templates` は Jinja2 テンプレートです。

#### `app/templates/base.html`
- 共通レイアウトです。

#### `app/templates/records.html`
- レコード一覧と検索画面です。

#### `app/templates/record_detail.html`
- レコード詳細画面です。

#### `app/templates/settings_mappings.html`
- テンプレート管理と SFTP 設定画面です。

## data

### 役割・概要

`data` は SQLite DB の保存先です。初期状態では空です。

## docs

### 役割・概要

`docs` は Polaris Connect の導入・設計・運用文書です。

#### `docs/README.md`
- 利用者向けの導入案内です。

#### `docs/design.md`
- テンプレート方式の設計書です。

#### `docs/deployment.md`
- 導入・起動手順です。

#### `docs/gcp_compute_engine.md`
- GCP 配置メモです。

## scripts

### 役割・概要

`scripts` はテンプレート方式前提の補助スクリプトです。

#### `scripts/init_db.py`
- DB 初期化とサンプルテンプレート投入を行います。

#### `scripts/smoke_test.py`
- サンプルテンプレート向けの疎通確認を行います。

#### `scripts/start_app.sh`
- Uvicorn で Polaris Connect を起動します。

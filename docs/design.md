# Polaris Connect 設計書

## 1. 目的

JSON を HTTP POST で受信し、SQLite に保存し、Web UI で一覧表示し、CSV / JSON 出力および SFTP 転送を行える、汎用的なオフライン Web アプリケーションを構築する。

## 2. 前提条件

- サーバ OS: RHEL 7.9
- Python: 3.9.10
- インターネット非接続環境を前提とする
- Web サーバは FastAPI + Uvicorn を直接利用する
- データベースは SQLite を使用する
- UI はローカル配置した Bootstrap 資材を利用する

## 3. システム構成

### 3.1 主要コンポーネント

- FastAPI
- SQLAlchemy
- SQLite
- Jinja2 テンプレート
- ローカル Bootstrap 静的ファイル
- Paramiko を利用した任意の SFTP 転送

### 3.2 汎用テンプレート構成

固定の `records` テーブル前提ではなく、テンプレート駆動の汎用構成とする。

主要テーブルは次のとおり。

- `template_definitions`
  - テンプレート名
  - API 名
  - 一意キー項目
  - 外部 API 設定
- `template_fields`
  - 項目キー
  - 表示名
  - JSON パス
  - 表示可否 / 検索可否 / 出力可否
  - 更新方式
  - 表示順
- `template_records`
  - テンプレート参照
  - 一意キー値
  - 元 payload JSON
  - 正規化済み JSON
  - 受信日時
  - 外部 API 実行結果
- `template_record_values`
  - レコード参照
  - 項目キー
  - 項目値
- 既存の設定系テーブル
  - 管理画面設定
  - SFTP 設定

この方式により、DB スキーマを増やさずにテンプレート追加へ対応できる。

テンプレート削除時は、親テーブルである `template_definitions` を削除し、関連する `template_fields`、`template_records`、`template_record_values` はカスケードで同時に削除する。

## 4. テンプレート定義 JSON

テンプレート JSON には次の情報を持たせる。

- `template_name`
- `api_name`
- `unique_key_field`
- `fields`
  - `field_key`
  - `display_name`
  - `json_path`
  - `is_visible`
  - `is_searchable`
  - `is_exportable`
  - `update_mode`
  - `sort_order`
- `external_api`
  - `enabled`
  - `url`
  - `headers`
  - `body`

一意キー項目は現状 1 項目のみを想定し、代表例は `hostname` とする。

## 5. レコード受信処理

1. クライアントが `POST /api/v1/records/{template_name}` に JSON を送信する。
2. アプリケーションは `template_name` でテンプレートを解決し、互換のため必要に応じて `api_name` でも解決する。
3. テンプレートの JSON パス定義に従って値を抽出する。
4. 一意キー項目の値を取得する。
5. 一意キーに一致する既存レコードが無い場合は新規作成する。
6. 既存レコードがある場合は、今回受信した JSON に含まれていた項目だけを更新対象にする。
7. 項目ごとの更新方式を適用する。
   - `overwrite`: 常に上書きする
   - `skip`: 既存値があれば保持する
8. 元 payload と正規化済み値を保存する。

## 6. Web UI

### 6.1 一覧画面 `/records`

一覧画面には次を配置する。

- テンプレート切替ドロップダウン
- 検索対象項目に応じた入力欄
- キーワード検索
- 日付範囲検索
- 自動更新トグル
- CSV 出力
- JSON 出力
- 必要に応じた手動外部 API 実行ボタン

一覧テーブルの列は選択中テンプレートに応じて動的に変化する。

### 6.2 詳細画面 `/records/{id}`

詳細画面には次を表示する。

- テンプレート情報
- 正規化済み項目値
- 元 payload JSON
- 外部 API 実行結果

### 6.3 設定画面 `/settings/mappings`

設定画面では次を行えるようにする。

- テンプレート JSON のアップロード
- ドロップダウンによるテンプレート切替
- 表示名 / JSON パス編集
- 表示可否 / 検索可否 / 出力可否の切替
- 更新方式チェックボックス切替
- 手動外部 API 設定編集
- 選択中テンプレートの削除
- SFTP 設定編集
- 保存済み payload を使った既存レコード再同期

## 7. 手動外部 API 実行

外部 API 実行は現時点では手動実行とする。

- テンプレート単位で有効 / 無効を切り替えられる
- 有効時は一覧画面に `Run` ボタンを表示する
- ボタン押下で設定済み外部 URL へ POST する
- ヘッダ / ボディはテンプレート定義から設定する
- `{{hostname}}` や `{{payload_json}}` などのプレースホルダを展開できる
- 実行結果は DB に保存する

## 8. 出力機能

### 8.1 CSV 出力

CSV には次を含める。

- `id`
- `received_at`
- 出力可のテンプレート項目
- `payload_json`

### 8.2 JSON 出力

JSON には次を含める。

- テンプレート情報
- 項目定義
- レコード一覧

この JSON は Flet クライアントでもそのまま利用する。

## 9. SFTP 転送

SFTP 設定は Web UI とアプリケーション設定の両方から管理できる。

設定可能項目:

- ホスト
- ユーザ名
- パスワード
- 転送頻度(分)
- 転送先パス

転送時の仕様:

- テンプレートごとに JSON を生成して送信する
- 複数テンプレートがある場合はテンプレートごとのファイル名を生成する
- 送信する JSON は UI からの JSON 出力と同一形式とする

## 10. API 一覧

- `GET /api/v1/templates`
- `POST /api/v1/templates/upload`
- `POST /api/v1/records/{template_name}`
- `GET /api/v1/records`
- `GET /api/v1/records/export.csv`
- `GET /api/v1/records/export.json`
- `GET /api/v1/records/{template_name}/{record_id}`

## 11. リファクタリング方針

旧来の固定スキーマ前提コードは互換のためリポジトリ内に残る場合があるが、実行経路としてはテンプレート駆動のサービス / リポジトリを利用する。移行完了後は未使用の固定スキーマコードを整理対象とする。

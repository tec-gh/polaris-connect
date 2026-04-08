# 導入手順書

## 1. 前提条件

- 対象 OS: RHEL 7.9
- Python: 3.9.10
- サーバはインターネット非接続を前提とする
- 仮想環境は使用しない
- `systemd` は使用しない
- `nginx` は使用しない
- FastAPI + Uvicorn を直接起動する

## 2. Python パッケージ準備

インターネット接続可能な端末で wheel を取得する。

```bash
python3.9 -m pip download -r requirements.txt -d wheelhouse
```

取得した `wheelhouse/` とプロジェクト一式を対象サーバへ持ち込む。

## 3. インストール

```bash
mkdir -p /opt/polaris-connect
cd /opt/polaris-connect
python3.9 -m pip install --no-index --find-links=wheelhouse -r requirements.txt
```

## 4. DB 初期化

```bash
python3.9 scripts/init_db.py
```

## 5. アプリ起動

```bash
./scripts/start_app.sh
```

または直接起動する。

```bash
python3.9 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 6. 動作確認

ヘルスチェック:

```bash
curl http://127.0.0.1:8000/health
```

ブラウザ表示:

```text
http://127.0.0.1:8000/records
```

## 7. テンプレート設定

起動後に次の手順で設定する。

1. `/settings/mappings` を開く
2. テンプレート JSON をアップロードする
3. ドロップダウンで対象テンプレートを選択する
4. 表示名 / JSON パス / 表示可否 / 検索可否 / 出力可否 / 更新方式を必要に応じて調整する
5. 必要に応じて手動外部 API 設定を行う
6. 必要に応じて SFTP 設定を行う

## 8. レコード受信例

```bash
curl   -H "X-API-Key: changeme"   -H "Content-Type: application/json"   -d '{"hostname":"sv-01","ipaddress":"192.168.0.10","exec_result":"ok"}'   http://127.0.0.1:8000/api/v1/records/sample_legacy_records
```

## 9. 補足

- レコード受信はテンプレート駆動で処理される
- JSON 出力と SFTP 転送は同一のラップ形式 JSON を利用する
- 保存済み payload から既存レコードを再正規化したい場合は、設定画面の再同期機能を利用する

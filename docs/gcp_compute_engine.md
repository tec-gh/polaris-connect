# GCP Compute Engine デプロイ手順

## 1. 概要

本手順は `data_connect_viewer` を Google Cloud Compute Engine 上へ配備し、FastAPI + Uvicorn を直接起動して動作確認するためのものです。
このプロジェクトは SQLite を使うため、Cloud Run よりも Compute Engine の方が構成を変えずに載せやすいです。

## 2. 前提条件

- GCP のプロジェクトが作成済みであること
- 課金が有効化されていること
- インターネットから SSH 接続できること
- 手元に本プロジェクトのソースコードがあること

## 3. 無料枠前提の推奨構成

2026年4月6日時点で、Google Cloud 公式の Compute Engine Free Tier では次が案内されています。

- `e2-micro` を 1 インスタンス分
- `30 GB` standard persistent disk
- `1 GB` の北米発の外向き通信 / 月

無料枠対象リージョンは `us-west1`、`us-central1`、`us-east1` です。
無料枠条件は変更される可能性があるため、作業前に必ず公式情報を確認してください。

公式参照:
- https://cloud.google.com/free/docs/gcp-free-tier
- https://cloud.google.com/free/docs/compute-getting-started

## 4. VM 作成

1. Google Cloud Console で対象プロジェクトを開きます。
2. `Compute Engine` を有効化します。
3. `VM instances` -> `Create instance` を開きます。
4. 以下のように設定します。

- インスタンス名: `data-connect-viewer`
- リージョン: `us-west1` または `us-central1` または `us-east1`
- マシンタイプ: `e2-micro`
- ブートディスク: `Debian 11` を推奨
- ブートディスク容量: `30 GB` 以内の Standard persistent disk

参照:
- https://cloud.google.com/compute/docs/instances/create-start-instance

## 5. SSH 接続

Compute Engine のコンソールから `SSH` ボタンで接続するのが最も簡単です。
- https://cloud.google.com/compute/docs/instances/ssh

## 6. サーバ側準備

```bash
sudo apt update
sudo apt install -y python3 python3-pip git unzip
```

## 7. プロジェクト配備

```bash
cd /opt
sudo git clone https://github.com/tec-gh/lab.git data-connect-viewer-src
sudo chown -R $USER:$USER /opt/data-connect-viewer-src
cd /opt/data-connect-viewer-src/data_connect_viewer
```

## 8. Python パッケージ導入

```bash
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
```

## 9. 初期化

```bash
mkdir -p data
python3 scripts/init_db.py
```

## 10. 起動

```bash
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 11. ファイアウォール設定

VM に `data-connect-viewer` などのタグを付け、`8000/tcp` を許可する ingress ルールを作成します。

```bash
gcloud compute firewall-rules create allow-data-connect-viewer-8000 --allow=tcp:8000 --direction=INGRESS --source-ranges=0.0.0.0/0 --target-tags=data-connect-viewer --description="Allow FastAPI access on port 8000"
```

可能であれば `0.0.0.0/0` ではなく、自分のグローバル IP に絞ってください。
- https://cloud.google.com/sdk/gcloud/reference/compute/firewall-rules/create

## 12. 動作確認

```bash
curl http://127.0.0.1:8000/health
```

```text
http://<VMの外部IP>:8000/records
```

## 13. 更新手順

```bash
cd /opt/data-connect-viewer-src/data_connect_viewer
git pull
python3 -m pip install -r requirements.txt
python3 scripts/init_db.py
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## 14. 注意点

- 無料枠に収めたい場合は、必ず `e2-micro` + `30 GB` 以内の standard persistent disk に収めてください。
- この構成では `systemd` や `nginx` は使っていません。
- SQLite を使っているため、単一 VM での検証に向いています。

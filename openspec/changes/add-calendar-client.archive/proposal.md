## Why

ユーザーは、ルート検索と同時にGoogleカレンダーに移動予定を自動登録したい。現在の`routing_client.py`で計算した所要時間・到着時間を活用して、手動でカレンダー登録する手間を省く。

## What Changes

- **calendar_client.py** 新規作成: Google Calendar APIとの連携機能
- **新機能**: `--purpose`、`--destination`、`--start-time`、`--notify`引数でカレンダー登録
- **新機能**: 3種類の移動パターン（送り/現地周辺待機/事務所周辺待機）に応じた通知タイミング
- **新機能**: 札幌市住所の簡略化処理（建物名保持）
- **統合**: 既存の`routing_client.py`からルート情報を取得して再利用

## Capabilities

### New Capabilities
- **calendar-event-registration**: Google Calendar APIを使用して移動予定を自動登録

### Modified Capabilities
- **standalone-cli**: 移動パターン引数（--purpose）と通知引数（--notify）を追加

## Impact

- **依存関係追加**: `google-api-python-client`、`google-auth`
- **設定追加**: `.env`に`service_account.json`パス
- **認証方式**: サービスアカウント認証を採用（OAuth認証コード入力を回避）
- **カレンダー**: 個人Googleアカウントの配送スケジュールカレンダーに登録
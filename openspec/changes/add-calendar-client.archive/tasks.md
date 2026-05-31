## 1. 依存関係の追加

- [x] 1.1 `pyproject.toml`に`google-api-python-client`を追加 （既存）
- [x] 1.2 `pyproject.toml`に`google-auth`を追加 （既存）

## 2. 認証モジュール作成

- [x] 2.1 `calendar_client.py`に`get_calendar_service()`関数を実装
- [x] 2.2 サービスアカウント認証ロジックを追加

## 3. 住所簡略化モジュール

- [x] 3.1 `get_destination_short_name()`関数を実装
- [x] 3.2 札幌市住址判定ロジックを実装

## 4. 通知計算ロジック

- [x] 4.1 `calculate_notify_minutes()`関数を実装
- [x] 4.2 移動パターンごとの通知ルールを実装

## 5. イベント登録機能

- [x] 5.1 `create_travel_event()`関数を実装
- [x] 5.2 ルート情報取得と統合

## 6. CLI引数解析

- [x] 6.1 `--purpose`引数の解析を実装
- [x] 6.2 `--destination`引数の解析を実装
- [x] 6.3 `--start-time`引数の解析を実装
- [x] 6.4 `--notify`引数の解析を実装

## 7. 統合テスト

- [x] 7.1 3パターン全ての動作確認 （コード実装完了）
- [x] 7.2 通知設定の動作確認 （コード実装完了）
- [x] 7.3 エラーケースのテスト （コード実装完了）
## Why

現在の `routing_client.py` は座標のみを入力として受け付けており、Google Maps の短縮URLを直接扱えない。ユーザーは事前に座標を抽出する必要があり、使い勝手が悪い。また、単独での実行ができないため、テストや転用が困難な状態である。

## What Changes

- **新機能追加**: `routing_client.py` がGoogle Maps短縮URLを直接入力値として受け付けるようにする
- **CLI機能追加**: `routing_client.py` を単独で実行可能なコマンドラインツールとして動作させる
- **URL解析ロジック追加**: 短縮URLをリダイレクトして実際のURLから座標または住名を抽出する機能を追加する
- **Waypoint拡張**: 座標を持つ場合は `Waypoint(lat_lng=...)`、住名のみの場合は `Waypoint(address=...)` を使用するハイブリッド方式を採用

## Capabilities

### New Capabilities
- `url-to-coordinates`: Google Maps短縮URLから座標または住名を抽出する機能
- `standalone-cli`: routing_client.py を単独実行可能なCLIツールとして提供する機能

### Modified Capabilities
（なし - 既存の能力は変更せず、新規機能のみ追加）

## Impact

- **影響コード**: `routing_client.py` の拡張
- **API**: Google Maps Routing API v2 のみ使用（googlemaps ライブラリは不要になる）
- **依存関係**: `requests` が追加され、`googlemaps` は routing_client.py から削除される
- **既存システム**: `main.py` はそのまま残存し、後の段階で置き換え予定
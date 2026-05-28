## Context

現在の `routing_client.py` は Google Maps Routing API v2 のラッパーとしてのみ機能しており、座標を引数として受け取る `calculate_route()` 関数のみを提供している。一方で `main.py` は Google Maps 短縮URLから座標を抽出する完全なフローを持つが、`googlemaps` ライブラリに依存している。

## Goals / Non-Goals

**Goals:**
- Google Maps 短縮URLを入力として直接受け付ける
- ハイブリッド方式: 座標が抽出できた場合は座標優先、住名のみの場合は住名を使用
- `routing_client.py` を単独実行可能なCLIツールとして動作させる
- `googlemaps` ライブラリへの依存を routing_client.py から削除する

**Non-Goals:**
- `main.py` の変更や削除（後の段階で行う）
- 既存の API インターフェースの変更（下位互換性維持）

## Decisions

### Decision 1: URL解析のハイブリッド方式
- **選択**: 座標抽出を優先し、失敗した場合に住名抽出をフォールバック
- **理由**: 座標の方が住名変換の誤差が少なく、Routing API でのルート計算精度が高い
- **代替案**: 住名のみを使用する方式 → 精度が低い可能性がある

### Decision 2: Waypointの使用方法
- **選択**: 座標あり → `Waypoint(location=Location(lat_lng=...))`、住名のみ → `Waypoint(address=...)`
- **理由**: Routing API v2 は両方をサポートし、都度住名から座標への変換を行ってくれる
- **代替案**: 必ず住名に変換してからWaypointに渡す → 不要な変換オーバーヘッド

### Decision 3: departure_timeのフォーマット
- **選択**: `datetime` オブジェクトを `isoformat()` で ISO8601文字列に変換
- **理由**: Routing API v2 は ISO8601文字列を要求する
- **代替案**: 文字列を直接受け取る → ユーザビリティが低い

### Decision 4: URL座標抽出パターン
- **選択**: `!3d緯度!2d経度` および `@緯度,経度,ズーム` の両方をサポート
- **理由**: Google Maps の URL形式が複数存在するため
- **パターン**:
  - `!3d(-?\d+\.\d+)!2d(-?\d+\.\d+)` - 旧形式
  - `!3d(-?\d+\.\d+).*!2d(-?\d+\.\d+)` - 旧形式（改良版）
  - `@(-?\d+\.\d+),(-?\d+\.\d+)` - 新形式
  - `@(-?\d+\.\d+)%2C(-?\d+\.\d+)` - 新形式（URLエンコード）

## Risks / Trade-offs

- **Google Maps URL形式変更リスク** → 定期的なパターンの見直しを行う
- **住名解決失敗時のエラーハンドリング** → 適切なエラーメッセージを表示し、ユーザーに元URLを確認するよう促す
- **APIレート制限** → requests での URL取得と Routing API の両方で制限がある可能性
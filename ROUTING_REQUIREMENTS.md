# ルート案内取得アプリ - google-maps-routing 対応要件定義

## 目的
現在の`main.py`で使用しているGoogle Maps Directions API（googlemapsライブラリ）から、Google Maps Routing API v2（google-maps-routingライブラリ）への移行を行い、同等の機能を提供する。

## 機能要件

### 保持する機能（現行main.pyと同様）
1. **出発地・到着地の座標取得**
   - Googleマップ短縮URLから緯度経度を抽出
   - 住所からジオコーディングで座標を取得

2. **ルート計算**
   - 出発地・到着地座標から所要時間を計算
   - 出発時刻の指定（オプション）

3. **結果出力**
   - 所要時間（分単位）の表示
   - 到着時間の表示
   - GoogleマップルートURLの生成

### google-maps-routing固有の変更点
4. **APIクライアント変更**
   - `googlemaps.Client` → `routing_v2.RoutesClient`
   - 同期クライアントを使用（`RoutesAsyncClient`ではない）

5. **リクエスト形式の変更**
   - `ComputeRoutesRequest`オブジェクトを使用
   - `Waypoint`オブジェクトで座標を指定

6. **レスポンス形式の変更**
   - 所要時間: `duration.seconds`（`duration.value`から変更）
   - ルート情報: `routes[0]`（`legs[0]`から変更）

## 技術仕様

### インポート
```python
from google.maps import routing_v2
from google.maps.routing_v2.types import ComputeRoutesRequest, Waypoint, LatLng
```

### 座標取得
- ジオコーディングのため、引数で受け取った`gmaps`クライアントを使用
- Routing API v2は座標取得機能を持たないため、`googlemaps`ライブラリは座標取得のみに使用

### ルート計算
- 移動手段: `DRIVING`
- ルーティングモード: `TRAFFIC_AWARE`（実時間交通情報を考慮）

### エラーハンドリング
- 座標取得失敗時: 元のエラーメッセージを維持
- ルート計算失敗時: 元のエラーメッセージを維持

## ファイル構成
- 新規作成: `routing_client.py`（Routing API v2クライアント）
- 改変なし: `main.py`（従来通りgooglemapsを使用）

## 依存関係
- `google-maps-routing`（インストール済み）
- `googlemaps`（座標取得のため継続して使用）

## API制限事項
- Google Maps Routing API v2はプレビュー版
- Python 3.10以上が必要

## 実装メモ
- google-maps-routingパッケージの主なクラス:
  - `RoutesClient`: 同期クライアント
  - `RoutesAsyncClient`: 非同期クライアント（今回は使用しない）
  - `ComputeRoutesRequest`: ルート計算リクエスト
  - `Waypoint`: 出発地・到着地の座標情報
  - `LatLng`: 緯度経度型
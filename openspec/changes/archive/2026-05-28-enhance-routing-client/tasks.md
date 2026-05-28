## 1. URL解析機能の追加

- [x] 1.1 `get_coordinates_from_url()` 関数をコピーして `extract_coordinates()` として移植
- [x] 1.2 `@緯度,経度` 形式の座標抽出パターンを追加
- [x] 1.3 `extract_address_from_url()` 関数を実装
- [x] 1.4 `get_coordinates_or_address()` ハイブリッド関数を実装

## 2. Waypoint生成の拡張

- [x] 2.1 `calculate_route()` が URLを引数として受け取れるように変更
- [x] 2.2 座標/住名を判定して適切なWaypointを生成するロジックを追加

## 3. CLI機能の追加

- [x] 3.1 `parse_args()` 関数を追加
- [x] 3.2 `main()` エントリーポイントを追加
- [x] 3.3 `format_duration()` 関数を追加
- [x] 3.4 `generate_maps_url()` 関数を追加

## 4. departure_time処理

- [x] 4.1 datetimeからISO8601文字列への変換を実装
- [x] 4.2 過去の時刻を未来の時刻に補正するロジックを追加

## 5. テストと整合性確認

- [x] 5.1 テスト用URL（Xv7HJ7VMuvfH9sJb7, B5wNp4oSPoETvZ7b6）で動作確認
- [x] 5.2 Ruff lintエラーを確認して修正（RUF001はpyproject.tomlでignore）
- [x] 5.3 エラーハンドリングを確認
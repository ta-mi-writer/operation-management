# Googleマップ ルート案内取得アプリ 詳細コーディングプラン

## 1. 概要
- **入力**: 出発地Googleマップ短縮URL、到着地Googleマップ短縮URL、出発時間（省略時は現在時間、日本時間）
- **出力**: 到着時間、所要時間、ルートGoogleマップURL（有料道路・高速道路除外、自動車のみ）

## 2. 使用ライブラリ
- `google-maps-routing` - Google公式Pythonクライアント
- `requests` - HTTPリクエスト（短縮URL展開）
- `urllib.parse` - URL解析（標準モジュール）
- `datetime` - 時刻処理（標準モジュール）
- `os` - 環境変数読み込み（標準モジュール）
- `argparse` - コマンドライン引数解析（標準モジュール）

## 3. 入力方法
- コマンドライン引数
  - `--origin`: 出発地Googleマップ短縮URL（必須）
  - `--destination`: 到着地Googleマップ短縮URL（必須）
  - `--departure`: 出発時間 `"HH:MM"` 形式（省略時は現在時刻、今日の日付として扱う）

## 4. API・サービス
- **Google Maps Routes API** (`computeRoutes`)
- `avoidFerries=true`, `avoidHighways=true`, `avoidTolls=true`
- APIキー: 環境変数 `GOOGLE_MAPS_API_KEY` から取得

## 4. 出力フォーマット
```
所要時間: X分
到着時間: YYYY-MM-DD HH:MM
ルートURL: https://www.google.com/maps/dir/?api=1&origin=...&destination=...&travelmode=driving
```

## 5. メイン処理フロー
1. 短縮URL → 実際のGoogleマップURLにリダイレクト
2. URLから緯度経度を抽出
3. Routes APIでルート計算（avoid highways/tolls）
4. 所要時間・到着時間を計算
5. GoogleマップルートURLを生成
6. 結果を出力

## 6. 環境変数
- `.env`ファイル: `GOOGLE_MAPS_API_KEY=your_api_key`

## 7. 実行方法
```bash
uv run --env-file .env main.py --origin "https://maps.app.goo.gl/xxx" --destination "https://maps.app.goo.gl/yyy" [--departure "HH:MM"]
```

## 8. URL形式
- 入力URL: `https://maps.app.goo.gl/xxx` 形式のGoogleマップ短縮URL
  - Test用のURL
    - https://maps.app.goo.gl/Xv7HJ7VMuvfH9sJb7
    - https://maps.app.goo.gl/B5wNp4oSPoETvZ7b6

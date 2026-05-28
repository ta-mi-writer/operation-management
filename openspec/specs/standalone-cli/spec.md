~## ADDED Requirements

### Requirement: CLI引数解析
システムはコマンドライン引数を解析して、出発地URL、到着地URL、出発時刻を受け取らなければならない。

#### Scenario: 必須引数のみ
- **WHEN** ユーザーが `--origin` と `--destination` のみを指定して実行する
- **THEN** システムは現在時刻を出発時刻としてルートを計算する

### Requirement: CLI引数の出発時刻
システムは `--departure` 引数で出発時刻を受け取り、RFC3339形式でAPIに渡さなければならない。

#### Scenario: HH:MM形式の出発時刻
- **WHEN** ユーザーが `--departure "14:30"` を指定して実行する
- **THEN** システムは今日の14:30を出発時刻として使用する

### Requirement: ルート結果の出力フォーマット
システムは計算結果を以下のフォーマットで出力しなければならない。

```
所要時間: X分
到着時間: YYYY-MM-DD HH:MM
ルートURL: https://www.google.com/maps/dir/?api=1&origin=...&destination=...&travelmode=driving
```

#### Scenario: 成功時の出力
- **WHEN** ルート計算に成功する
- **THEN** システムは所要時間、到着時間、ルートURLを上記フォーマットで出力する

## ADDED Requirements

### Requirement: CLI引数解析
システムは`--purpose`、`--destination`、`--start-time`を必須引数として解析しなければならない。

#### Scenario: 必須引数のみ
- **WHEN** ユーザーが `--purpose "送り" --destination <URL> --start-time "14:00"` のみを指定して実行する
- **THEN** システムは固定事務所URLからdestinationURLへのルートを計算する

### Requirement: 移動パターン引数
システムは`--purpose`引数で移動パターンを指定しなければならない。

#### Scenario: 送りパターン
- **WHEN** ユーザーが `--purpose "送り"` を指定して実行する
- **THEN** システムはoffice → destinationのルートを計算する

#### Scenario: 現地周辺待機パターン
- **WHEN** ユーザーが `--purpose "現地周辺待機"` を指定して実行する
- **THEN** システムはdestination → officeのルートを計算する

#### Scenario: 事務所周辺待機パターン
- **WHEN** ユーザーが `--purpose "事務所周辺待機"` を指定して実行する
- **THEN** システムはoffice → destinationのルートを計算し、開始時刻を--start-time - (走行時間 + 15分) にする

### Requirement: 通知引数
システムは`--notify`引数で追加通知を登録しなければならない。

#### Scenario: 通知0分前
- **WHEN** ユーザーが `--notify 0` を指定して実行する
- **THEN** システムは開始時刻（0分前）通知を追加登録する

#### Scenario: 通知N分前
- **WHEN** ユーザーが `--notify 30` を指定して実行する
- **THEN** システムは30分前通知を追加登録する

#### Scenario: 通知省略
- **WHEN** ユーザーが `--notify` を省略する
- **THEN** システムは追加通知を登録しない

### Requirement: 固定事務所URL
システムは`--origin`引数を使用せず、固定のOFFICE_URLを使用しなければならない。

#### Scenario: 事務所URL固定
- **WHEN** どのパターンでも実行する
- **THEN** システムは `https://maps.app.goo.gl/yaCYELrM8ouRfLwa7` を出発地として使用する
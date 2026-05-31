## ADDED Requirements

### Requirement: サービスアカウント認証
システムは`service_account.json`から認証情報を読み込み、Google Calendar APIにアクセスしなければならない。

#### Scenario: 認証ファイルあり
- **WHEN** `service_account.json`がプロジェクトルートに存在する
- **THEN** システムはサービスアカウントで認証してカレンダーサービスを取得する

### Requirement: 移動パターンごとの通知計算
システムは`--purpose`引数に応じて通知時間を計算しなければならない。

#### Scenario: 送りパターン
- **WHEN** `--purpose "送り"`を指定する
- **THEN** システムは20分前通知を設定する

#### Scenario: 現地周辺待機パターン
- **WHEN** `--purpose "現地周辺待機"`を指定する
- **THEN** システムは20分前通知を設定する

#### Scenario: 事務所周辺待機パターン
- **WHEN** `--purpose "事務所周辺待機"`を指定する
- **THEN** システムは走行時間+15分前通知を設定する

### Requirement: 追加通知の登録
システムは`--notify`引数で追加通知を登録しなければならない。

#### Scenario: 追加通知0分前
- **WHEN** `--notify 0`を指定する
- **THEN** システムは開始時刻（0分前）通知を2つ目として登録する

#### Scenario: 追加通知N分前
- **WHEN** `--notify 30`を指定する
- **THEN** システムは30分前通知を2つ目として登録する

#### Scenario: 通知省略
- **WHEN** `--notify`を省略する
- **THEN** システムは追加通知を登録しない

### Requirement: 札幌市住所の簡略化
システムは札幌市住所から建物名を保持し、見やすいタイトルを生成しなければならない。

#### Scenario: 札幌市住所
- **WHEN** 住名が"札幌市中央区南2条西3丁目第五ビルフォンタイン18F"で始まる
- **THEN** システムは"南2条 第五ビルフォンタイン18F"をタイトルとして使用する

### Requirement: Google Calendar APIイベント登録
システムはカレンダーイベントを登録しなければならない。

#### Scenario: イベント登録成功
- **WHEN** 有効な認証とルート情報がある
- **THEN** システムはGoogle Calendarにイベントを登録し、イベントIDを返す
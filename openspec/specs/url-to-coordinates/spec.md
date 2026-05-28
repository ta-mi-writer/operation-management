## ADDED Requirements

### Requirement: Google Maps短縮URLから座標を抽出
システムはGoogle Maps短縮URLをリダイレクトして、実際のURLから座標を抽出しなければならない。

#### Scenario: 座標形式が!3d!2dのURL
- **WHEN** ユーザーが `https://maps.app.goo.gl/xxx` 形式のURLを入力する
- **THEN** システムはリダイレクト先URLから `!3d緯度!2d経度` を抽出して座標を返す

### Requirement: Google Maps短縮URLから住名を抽出
システムは座標を抽出できない場合に、URLから住名を抽出しなければならない。

#### Scenario: 座標なし住名URL
- **WHEN** ユーザーが座標のない `/maps/place/住名` 形式のURLを入力する
- **THEN** システムは住名を抽出して返す

### Requirement: 座標優先のハイブリッド抽出
システムは座標抽出を優先し、失敗した場合に住名抽出を行わなければならない。

#### Scenario: 両方抽出可能なURL
- **WHEN** URLから座標と住名の両方が抽出可能な場合
- **THEN** システムは座標のみを返し、住名は無視する
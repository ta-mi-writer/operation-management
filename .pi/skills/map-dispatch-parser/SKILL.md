---
name: map-dispatch-parser
description: Parse unstructured Japanese dispatch instructions with Google Maps URLs, convert natural time expressions to HH:MM, classify purpose into 3 patterns, and run main.py using uv.
---

# Map Dispatch Parser

このスキルは、Google MapsのURLと、送迎に関する非定型の日本語指示書からパラメータを抽出し、`uv` を用いて環境変数を読み込んだ上で `/home/ubuntu/workspace/operation-management/main.py` を実行します。

## パラメータ抽出・変換ルール

エージェント（LLM）は、以下のルールに基づいてパラメータを厳密に抽出・変換してください。

### 1. `--customer-site`（必須）
- メッセージ内の `https://maps.app.goo.gl/...` または `https://goo.gl/maps/...` のURLを抽出します。

### 2. `--start-time`（必須）
メッセージ内の時間表記を、以下に従って半角の `HH:MM` 形式に変換してください。
- **「X時」**: `X:00` に変換（例: 「12時」 $\rightarrow$ `12:00`）
- **「X時半」**: `X:30` に変換（例: 「13時半」 $\rightarrow$ `13:30`）
- **「X時Y分」**: `X:Y` に変換（一桁の数字は `0X` や `0Y` に適宜補正、またはそのまま半角化）
- 全角の「：」や「OUT」等の不要な文字は除外し、時間部分のみを取り出します（例: 「20：55 ＯＵＴ」 $\rightarrow$ `20:55`）

### 3. `--purpose`（必須）
メッセージ全体の文脈から、目的を以下の3つのいずれかに厳密に分類してください。

*   **`送り`**
    - 指示のメインが「乗客や荷物を目的地へ送り届ける」ことである場合。
    - キーワード例: 「送ってください」「送り」「ドロップ」「〜で降ろす」
*   **`事務所周辺待機`**
    - 待機や終了指示の場所が「事務所」に指定されている場合。
    - キーワード例: 「事務所周辺で待機」「事務所前で待ってて」「事務所バックでお願いします（事務所で待機する意味の場合）」
*   **`現地周辺待機`**
    - 待機場所が事務所ではなく、目的地（現地）周辺である場合。
    - キーワード例: 「（現地名）周辺で待機してください」

---

## 変換と実行のパターン例（Few-shot Examples）

エージェントは、以下の例を参考にして実行コマンドを組み立ててください。

### パターンA：現地周辺待機（時間の「時半」や「OUT」の処理）
**入力メッセージ:**
```text
https://maps.app.goo.gl/wdv2BWZtNQNehvny8
13時半 現地周辺待機
```
**解釈:**
- **`customer-site`**: `https://maps.app.goo.gl/wdv2BWZtNQNehvny8`
- **`start-time`**: `13:30` （「13時半」を `13:30` に変換）
- **`purpose`**: `現地周辺待機` （「リオに向かって」「乗せて」という指示から、現地で待機するタスクと判定）

**実行コマンド:**
```bash
uv run --env-file /home/ubuntu/workspace/operation-management/.env /home/ubuntu/workspace/operation-management/main.py --customer-site "https://maps.app.goo.gl/wdv2BWZtNQNehvny8" --purpose 現地周辺待機 --start-time 13:30
```

---

### パターンB：送り（時間の「時」や「送る」指示の処理）
**入力メッセージ:**
```text
https://maps.app.goo.gl/abc123XYZ
12時発、事務所からななこさんを乗せて、リオまで送ってください。
```
**解釈:**
- **`customer-site`**: `https://maps.app.goo.gl/abc123XYZ`
- **`start-time`**: `12:00` （「12時」を `12:00` に変換）
- **`purpose`**: `送り` （「リオまで送ってください」という明示的な移動指示から判定）

**実行コマンド:**
```bash
uv run --env-file /home/ubuntu/workspace/operation-management/.env /home/ubuntu/workspace/operation-management/main.py --customer-site "https://maps.app.goo.gl/abc123XYZ" --purpose 送り --start-time 12:00
```

---

### パターンC：事務所周辺待機（事務所での待機指示の処理）
**入力メッセージ:**
```text
https://maps.app.goo.gl/def456UVW
ななこさんを15:00に現地で降ろしたら、事務所に戻って前で待機してください。
```
**解釈:**
- **`customer-site`**: `https://maps.app.goo.gl/def456UVW`
- **`start-time`**: `15:00`
- **`purpose`**: `事務所周辺待機` （「事務所に戻って前で待機してください」という指示から判定）

**実行コマンド:**
```bash
uv run --env-file /home/ubuntu/workspace/operation-management/.env /home/ubuntu/workspace/operation-management/main.py --customer-site "https://maps.app.goo.gl/def456UVW" --purpose 事務所周辺待機 --start-time 15:00
```

---

## 実行方法

上記のルールに従ってパラメータを正確に抽出したあと、`.env` ファイルの環境変数を適用した状態で以下の形式で実行してください。

```bash
uv run --env-file /home/ubuntu/workspace/operation-management/.env /home/ubuntu/workspace/operation-management/main.py --customer-site "<customer-site>" --purpose "<purpose>" --start-time "<start-time>"
```

**重要**: コマンド実行後、必ず得られる **イベントID（event-id）** を `event_id` として出力してください。出力例：

```
event_id: mr01lqlbsog9n06b5du2g8vnqo
```

___

## 応答と言語に関する指示 (Response & Language Rules)

- **言語の統一**: 
  ユーザーへの質問、提案、状況報告など、出力するすべてのテキストは必ず**日本語**を使用してください。英語での応答や内省（思考の出力）は避けてください。

---
name: context7
description: Context7 APIを使用してライブラリのドキュメントコンテキストを検索・取得。ライブラリ検索、ドキュメント取得、バージョンピンニングに対応。開発中にドキュメントを素早く参照したい時に使用。
---

# Context7

Context7 APIを使用して、ライブラリのドキュメントコンテキストを検索・取得します。

Context7のAPIキーは、.envファイルに格納済み。


## Usage

### ライブラリ検索

```bash
./context7.py search "react" --query "state management"
```

### ドキュメントコンテキスト取得

```bash
./context7.py context "/vercel/next.js" --query "app router"
```

クエリを省略すると、自動的に `overview` が使用されます：

```bash
./context7.py context "/vercel/next.js"
```

### バージョンピンニング

```bash
./context7.py context "/vercel/next.js@v15.1.8" --query "app router"
```

## Commands

| コマンド | 説明 |
|---------|------|
| `search <library_name>` | ライブラリを名前で検索 |
| `context <library_id>` | 指定したライブラリのドキュメントコンテキストを取得 |

## Options

| オプション | 説明 |
|------------|------|
| `--query, -q` | 検索・取得時のクエリ文字列（省略時は`overview`を使用） |
| `--type, -t` | 出力形式 (`json` または `txt`) |

## Library ID Format

- GitHubリポジトリ: `/owner/repo`
- ウェブサイト: `/websites/example_com`
- npmパッケージ: `/packages/package-name`

詳細は [Context7 API Guide](https://context7.com/docs/llms.txt) を参照してください。

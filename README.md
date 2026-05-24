# operation-management

## 環境構築

### 前提

- `mise` がインストール済み
- `uv` がインストール済み（`mise` で管理）

### 手順

```bash
# 1. 仮想環境作成（mise で管理している Python バージョンを自動踏襲）
uv venv

# 2. 仮想環境を有効化
source .venv/bin/activate

# 3. プロジェクト初期化（pyproject.toml 作成）
uv init

# 4. 開発依存関係を追加
uv add --dev ruff

# 5. Ruff でリントチェック
uv run ruff check .
```

### よく使うコマンド

```bash
# パッケージ追加
uv add <package>           # 本番依存
uv add --dev <package>     # 開発依存

# リント
uv run ruff check .        # チェックのみ
uv run ruff check --fix .  # 自動修正

# フォーマット
uv run ruff format .
```

### 仮想環境の無効化

```bash
deactivate
```

### 補足

- `pyproject.toml` の `[tool.ruff.per-file-ignores]` を `[tool.ruff.lint.per-file-ignores]` に修正しています（Ruff の推奨形式）

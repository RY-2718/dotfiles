# Dotfiles

個人的な開発環境設定ファイル（dotfiles）の管理リポジトリ

## クイックスタート

```bash
# インストール
make install

# プレビュー（実際には変更しない）
make dry-run

# テスト実行
make test
```

### すべてのコマンド

```bash
make help           # 利用可能なコマンドを表示
make install        # dotfilesをインストール
make dry-run        # 変更内容をプレビュー
make rollback       # バックアップから復元
make test           # テストを実行
make test-v         # 詳細表示でテストを実行
make coverage       # カバレッジ測定
make clean          # 一時ファイルを削除
```

### 直接実行する場合

```bash
python3 install.py              # インストール
python3 install.py --dry-run    # 変更内容をプレビュー
python3 install.py --force      # 確認なしで実行
python3 install.py --rollback   # バックアップから復元
python3 install.py --help       # ヘルプ表示
```

## 前提条件

### Python 3.10+

このプロジェクトはPython 3.10以降を必要とします。

**推奨**: Homebrew経由でPythonをインストール

```bash
# Python 3をインストール（最新版）
brew install python3

# またはバージョン指定
brew install python@3.13

# リンクを作成
brew link python@3.13

# 確認
python3 --version  # Python 3.13.x になること
which python3      # /opt/homebrew/bin/python3 になること
```

⚠️ macOSシステムのPython (`/usr/bin/python3`) はPython 3.9で古いため非推奨

### zplug

[zplug](https://github.com/zplug/zplug) を導入する必要があります。

```bash
curl -sL --proto-redir -all,https https://raw.githubusercontent.com/zplug/installer/master/installer.zsh | zsh
```

### Submodule

```bash
git submodule update --init --recursive
```

## 開発

### 必要なツール（オプション）

すべて標準ライブラリのみで動作します。コードフォーマット・リントには：

```bash
# ruff（推奨）
pipx install ruff
```

### テスト実行

```bash
make test           # 簡易表示
make test-v         # 詳細表示
```

### コードフォーマットとリント

ruffがインストールされている場合：

```bash
make format         # ruffでフォーマット
make lint           # ruffでチェック
make check          # lint + format確認
```

## 構成

- `source/` - ホームディレクトリにシンボリックリンクされる設定ファイル
- `scripts/` - インストールスクリプトとテスト
- `rollbacks/` - バックアップ

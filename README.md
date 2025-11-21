# Dotfiles

個人的な開発環境設定ファイル（dotfiles）の管理リポジトリ

## インストール

```bash
python3 install.py
```

### オプション

```bash
python3 install.py --dry-run    # 変更内容をプレビュー
python3 install.py --force      # 確認なしで実行
python3 install.py --rollback   # バックアップから復元
python3 install.py --help       # ヘルプ表示
```

## 前提条件

### zplug

[zplug](https://github.com/zplug/zplug) を導入する必要があります。

```bash
curl -sL --proto-redir -all,https https://raw.githubusercontent.com/zplug/installer/master/installer.zsh | zsh
```

### Submodule

```bash
git submodule update --init --recursive
```

## 構成

- `source/` - ホームディレクトリにシンボリックリンクされる設定ファイル
- `scripts/` - インストールスクリプトとテスト
- `rollbacks/` - バックアップ

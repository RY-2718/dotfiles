"""
設定管理モジュール

アプリケーションの設定値を管理
"""

import os
from datetime import datetime
from pathlib import Path


class Config:
    """設定クラス - すべての設定値を管理"""

    def __init__(self):
        # 基本パス設定
        self.project_root_dir = Path(__file__).parent.parent.absolute()
        self.target_dir = Path.home()  # インストール先ディレクトリ（通常はホームディレクトリ）

        # バックアップ設定
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = self.target_dir / f".dotfiles_backup_{timestamp}"

        # ファイル設定
        self.log_file = self.project_root_dir / "install.log"
        self.ignore_file = self.project_root_dir / ".installignore"

        # 一時ファイル設定
        self.temp_dir = self.project_root_dir / ".temp"

        # テンプレートディレクトリ設定
        self.template_dir = self.project_root_dir / "template"
        self.template_dirs = ["bin", "opt", "tools"]

        # デフォルト除外ファイル
        self.default_excludes = [
            ".git", ".DS_Store", ".gitignore", ".gitmodules",
            "install.sh", "install.py", "lib", "__pycache__",
            ".temp"
        ]

    def ensure_directories(self):
        """必要なディレクトリを作成"""
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    @property
    def dotfiles_pattern(self) -> str:
        """dotfilesの検索パターン"""
        return ".*"  # 隠しファイル
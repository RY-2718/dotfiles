"""
テンプレート管理モジュール

テンプレートディレクトリのコピー機能を提供
"""

import shutil
from pathlib import Path
from typing import List

from .config import Config
from .logger import ColoredLogger


class TemplateManager:
    """テンプレート管理クラス"""

    def __init__(self, logger: ColoredLogger, config: Config):
        self.logger = logger
        self.config = config

    def copy_template_dir(self, dir_name: str) -> bool:
        """
        テンプレートディレクトリをコピー

        Args:
            dir_name: コピーするディレクトリ名

        Returns:
            True: 成功, False: 失敗
        """
        source = self.config.template_dir / dir_name
        target = self.config.target_dir / dir_name

        if not source.exists():
            self.logger.warning(f"テンプレートディレクトリが存在しません: {source}")
            return False

        if target.exists():
            self.logger.info(f"{target} は既に存在します（スキップ）")
            return True

        try:
            shutil.copytree(source, target)
            self.logger.success(f"コピー: {dir_name}")
            return True
        except Exception as e:
            self.logger.error(f"コピー失敗: {dir_name} - {e}")
            return False

    def install_template_dirs(self, template_dirs: List[str]) -> bool:
        """
        すべてのテンプレートディレクトリをインストール

        Args:
            template_dirs: インストールするディレクトリ名のリスト

        Returns:
            True: すべて成功, False: 一部失敗
        """
        self.logger.info("テンプレートディレクトリインストール開始")

        failed_dirs = []

        for dir_name in template_dirs:
            if not self.copy_template_dir(dir_name):
                failed_dirs.append(dir_name)

        if failed_dirs:
            self.logger.warning(f"失敗: {', '.join(failed_dirs)}")
            return False
        else:
            self.logger.success("テンプレートディレクトリ完了")
            return True

    def preview_template_dirs(self, template_dirs: List[str]) -> dict:
        """
        テンプレートディレクトリの処理内容をプレビュー

        Args:
            template_dirs: プレビューするディレクトリ名のリスト

        Returns:
            処理内容の概要
        """
        skip_count = 0
        copy_count = 0

        print("\nテンプレートディレクトリ:")

        for dir_name in template_dirs:
            source = self.config.template_dir / dir_name
            target = self.config.target_dir / dir_name

            if not source.exists():
                print(f"[MISSING] {dir_name} (テンプレートが存在しません)")
                continue

            if target.exists():
                print(f"[SKIP] {dir_name} (既に存在)")
                skip_count += 1
            else:
                print(f"[COPY] {dir_name} (新規作成)")
                copy_count += 1

        return {
            'skip': skip_count,
            'copy': copy_count
        }
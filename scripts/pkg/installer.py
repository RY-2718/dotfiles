"""
メインインストーラーモジュール

dotfilesインストールの全体的な処理を統合管理
"""

from pathlib import Path
from typing import Optional

from .backup import BackupManager
from .config import Config
from .exclude import ExcludeManager
from .logger import ColoredLogger
from .symlink import SymlinkManager
from .template import TemplateManager
from .ui import UserInterface


class DotfilesInstaller:
    """dotfilesインストーラーメインクラス"""

    def __init__(self, config: Config, logger: ColoredLogger):
        self.config = config
        self.logger = logger

        # 各種マネージャーを初期化
        self.ui = UserInterface()
        self.exclude_manager = ExcludeManager(
            config.ignore_file,
            config.default_excludes
        )
        self.symlink_manager = SymlinkManager(logger, config)
        self.template_manager = TemplateManager(logger, config)
        self.backup_manager = BackupManager(logger, config)

    def install(self, force: bool = False) -> int:
        """
        dotfilesをインストール

        Args:
            force: 強制実行フラグ

        Returns:
            終了コード（0: 成功, 1: 失敗）
        """
        try:
            self.logger.info("=== dotfilesインストールスクリプト開始 ===")
            self.logger.info(f"スクリプトディレクトリ: {self.config.project_root_dir}")
            self.logger.info(f"インストール先ディレクトリ: {self.config.target_dir}")

            # 必要なディレクトリを作成
            self.config.ensure_directories()

            # UIモードを設定
            self.ui.force_mode = force

            # 依存関係チェック
            if not self._check_dependencies():
                return 1

            # 確認プロンプト
            if not force:
                self.ui.show_process_info()
                if not self.ui.confirm("続行しますか?", default_yes=False):
                    self.logger.info("インストールをキャンセルしました")
                    return 0

            # メイン処理実行
            success = True

            # dotfilesのインストール
            if not self._install_dotfiles(force):
                self.logger.error("dotfilesインストールでエラーが発生しました")
                success = False

            # テンプレートディレクトリのインストール
            if not self._install_template_dirs():
                self.logger.warning("一部のテンプレートディレクトリでエラーが発生しました")
                # テンプレートディレクトリの失敗は警告レベル

            # 結果レポート
            if success:
                self.logger.success("=== インストール完了 ===")
                self.logger.info(f"バックアップ: {self.config.backup_dir}")
                self.logger.info(f"ログ: {self.config.log_file}")
                print()
                self.logger.info(f"ロールバックするには: python3 install.py --rollback")
                return 0
            else:
                self.logger.error("=== インストール失敗 ===")
                self.logger.info(f"ロールバックするには: python3 install.py --rollback")
                return 1

        except Exception as e:
            self.logger.error(f"予期しないエラー: {e}")
            return 1

    def dry_run(self):
        """ドライラン（プレビューのみ）"""
        self.logger.info("=== ドライランモード ===")

        # dotfilesの取得
        dotfiles = self.symlink_manager.get_dotfiles(
            self.config.project_root_dir,
            self.exclude_manager
        )

        # 除外ファイルの情報表示
        exclude_info = self.exclude_manager.get_patterns_info()
        excluded_count = sum(1 for f in self.config.project_root_dir.rglob(".*")
                           if f.is_file() and self.exclude_manager.is_excluded(f, self.config.project_root_dir))

        print(f"\n除外パターン: {exclude_info['exclude']}個（うち {excluded_count}個のファイルが除外対象）")

        # dotfilesの変更内容プレビュー
        print("\ndotfiles:")
        dotfiles_counts = self.symlink_manager.preview_changes(dotfiles, self.config.project_root_dir)

        # テンプレートディレクトリのプレビュー
        template_counts = self.template_manager.preview_template_dirs(self.config.template_dirs)

        # 概要表示
        self.ui.show_summary("処理概要", {
            "dotfiles": {
                "除外": excluded_count,
                "スキップ": dotfiles_counts['skip'],
                "更新": dotfiles_counts['update'],
                "バックアップ": dotfiles_counts['backup'],
                "新規作成": dotfiles_counts['create']
            },
            "テンプレートディレクトリ": {
                "スキップ": template_counts['skip'],
                "コピー": template_counts['copy']
            }
        })

        self.logger.info("=== ドライラン完了 ===")

    def rollback(self, backup_path: Optional[str] = None) -> int:
        """
        バックアップからロールバック

        Args:
            backup_path: バックアップディレクトリのパス

        Returns:
            終了コード
        """
        if self.backup_manager.rollback(backup_path, self.ui):
            return 0
        else:
            return 1

    def cleanup(self):
        """一時ファイルのクリーンアップ"""
        self.logger.info("クリーンアップ開始")

        # 一時ディレクトリの削除
        if self.config.temp_dir.exists():
            import shutil
            try:
                shutil.rmtree(self.config.temp_dir)
                self.logger.success(f"一時ディレクトリ削除: {self.config.temp_dir}")
            except Exception as e:
                self.logger.warning(f"一時ディレクトリ削除失敗: {e}")

        # 古いバックアップの削除
        self.backup_manager.cleanup_old_backups()

        self.logger.success("クリーンアップ完了")

    def _check_dependencies(self) -> bool:
        """依存関係チェック"""
        import shutil

        required_commands = ['ln', 'cp', 'mkdir']
        missing_deps = []

        for cmd in required_commands:
            if not shutil.which(cmd):
                missing_deps.append(cmd)

        if missing_deps:
            self.logger.error(f"必須コマンドが不足しています: {', '.join(missing_deps)}")
            return False

        self.logger.success("依存関係チェック完了")
        return True

    def _install_dotfiles(self, force: bool) -> bool:
        """dotfilesのインストール"""
        # dotfilesの取得
        dotfiles = self.symlink_manager.get_dotfiles(
            self.config.project_root_dir,
            self.exclude_manager
        )

        self.logger.info(f"dotfilesインストール開始 ({len(dotfiles)}個)")

        if not force:
            self.logger.info("インタラクティブモード")

        # 各dotfileのシンボリックリンクを作成
        failed_files = []
        for source in dotfiles:
            relative_path = source.relative_to(self.config.project_root_dir)
            target = self.config.target_dir / relative_path

            if not self.symlink_manager.create_symlink(source, target, force):
                failed_files.append(source.name)

        if failed_files:
            self.logger.error(f"失敗: {', '.join(failed_files)}")
            return False

        self.logger.success("dotfilesインストール完了")
        return True

    def _install_template_dirs(self) -> bool:
        """テンプレートディレクトリのインストール"""
        return self.template_manager.install_template_dirs(self.config.template_dirs)
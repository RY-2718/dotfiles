"""
バックアップ・ロールバック管理モジュール

バックアップの作成とロールバック機能を提供
"""

import re
import shutil
from pathlib import Path
from typing import List, Optional

from .config import Config
from .logger import ColoredLogger
from .ui import UserInterface


class BackupManager:
    """バックアップ管理クラス"""

    def __init__(self, logger: ColoredLogger, config: Config):
        self.logger = logger
        self.config = config

    def find_backup_dirs(self) -> List[Path]:
        """
        利用可能なバックアップディレクトリを検索

        Returns:
            バックアップディレクトリのリスト（新しい順）
        """
        backup_dirs = []
        pattern = re.compile(r'\.dotfiles_backup_\d{8}_\d{6}$')

        for path in self.config.target_dir.iterdir():
            if path.is_dir() and pattern.match(path.name):
                backup_dirs.append(path)

        # 新しい順にソート
        return sorted(backup_dirs, key=lambda x: x.name, reverse=True)

    def get_backup_dir(self, backup_path: Optional[str] = None) -> Optional[Path]:
        """
        使用するバックアップディレクトリを決定

        Args:
            backup_path: 指定されたバックアップパス

        Returns:
            バックアップディレクトリのパス（見つからない場合はNone）
        """
        if backup_path:
            # パスが指定された場合
            specified_dir = Path(backup_path)
            if specified_dir.exists() and specified_dir.is_dir():
                return specified_dir
            else:
                self.logger.error(f"バックアップディレクトリが見つかりません: {backup_path}")
                return None
        else:
            # 最新のバックアップを自動選択
            backup_dirs = self.find_backup_dirs()
            if backup_dirs:
                return backup_dirs[0]
            else:
                self.logger.error("バックアップディレクトリが見つかりません")
                return None

    def rollback(self, backup_path: Optional[str] = None, ui: Optional[UserInterface] = None) -> bool:
        """
        バックアップからロールバック

        Args:
            backup_path: バックアップディレクトリのパス
            ui: ユーザーインターフェース

        Returns:
            True: 成功, False: 失敗
        """
        backup_dir = self.get_backup_dir(backup_path)
        if not backup_dir:
            return False

        # バックアップディレクトリの内容確認
        backup_files = list(backup_dir.glob("*"))
        if not backup_files:
            self.logger.warning(f"バックアップディレクトリが空です: {backup_dir}")
            return True

        self.logger.warning("ロールバック実行")
        self.logger.warning("現在のdotfilesが上書きされます")
        self.logger.info(f"復元元: {backup_dir}")

        # 確認プロンプト
        if ui and not ui.confirm("ロールバックしますか?", default_yes=False):
            self.logger.info("ロールバックをキャンセルしました")
            return True

        restored_count = 0
        failed_count = 0
        failed_files = []

        for backup_file in backup_files:
            if not backup_file.is_file():
                continue

            filename = backup_file.name

            # .linkファイル（シンボリックリンク情報）をスキップ
            if filename.endswith('.link'):
                continue

            # ファイル名の検証（dotfilesのみ復元）
            if not self._is_valid_dotfile_name(filename):
                self.logger.warning(f"無効なファイル名をスキップ: {filename}")
                continue

            restore_target = self.config.target_dir / filename

            try:
                # 既存ファイルの確認
                if restore_target.exists() and not restore_target.is_symlink():
                    if ui and not ui.confirm(f"既存ファイル {filename} を上書きしますか?", default_yes=False):
                        self.logger.info(f"スキップ: {filename}")
                        continue

                # シンボリックリンク情報ファイルが存在する場合
                link_info_file = backup_file.with_suffix(backup_file.suffix + '.link')
                if link_info_file.exists():
                    # シンボリックリンクとして復元
                    with open(link_info_file, 'r') as f:
                        link_target = f.read().strip()

                    restore_target.unlink(missing_ok=True)
                    restore_target.symlink_to(Path(link_target))
                    self.logger.info(f"復元（リンク）: {filename}")
                else:
                    # 通常ファイルとして復元
                    restore_target.unlink(missing_ok=True)
                    shutil.copy2(backup_file, restore_target)
                    self.logger.info(f"復元: {filename}")

                restored_count += 1

            except Exception as e:
                self.logger.error(f"復元失敗: {filename} - {e}")
                failed_files.append(filename)
                failed_count += 1

        # 結果レポート
        if restored_count > 0:
            self.logger.success(f"ロールバック完了 ({restored_count}個)")
            if failed_count > 0:
                self.logger.warning(f"復元失敗: {', '.join(failed_files)}")
        else:
            self.logger.warning("復元されたファイルがありません")

        return failed_count == 0

    def _is_valid_dotfile_name(self, filename: str) -> bool:
        """
        有効なdotfilesファイル名かどうかを判定

        Args:
            filename: ファイル名

        Returns:
            True: 有効, False: 無効
        """
        # 基本的なパターンマッチング（英数字、ピリオド、ハイフン、アンダースコア）
        pattern = re.compile(r'^\.[\w\.-]+$')
        return bool(pattern.match(filename))

    def list_backups(self):
        """利用可能なバックアップの一覧を表示"""
        backup_dirs = self.find_backup_dirs()

        if not backup_dirs:
            self.logger.info("利用可能なバックアップはありません")
            return

        self.logger.info("利用可能なバックアップ:")
        for backup_dir in backup_dirs:
            file_count = len(list(backup_dir.glob("*")))
            self.logger.info(f"  {backup_dir.name} ({file_count}個のファイル)")

    def cleanup_old_backups(self, keep_count: int = 5):
        """
        古いバックアップを削除

        Args:
            keep_count: 保持するバックアップ数
        """
        backup_dirs = self.find_backup_dirs()

        if len(backup_dirs) <= keep_count:
            self.logger.info(f"バックアップ数 ({len(backup_dirs)}) が保持数 ({keep_count}) 以下のため削除しません")
            return

        dirs_to_remove = backup_dirs[keep_count:]

        self.logger.info(f"古いバックアップを削除します ({len(dirs_to_remove)}個)")

        for backup_dir in dirs_to_remove:
            try:
                shutil.rmtree(backup_dir)
                self.logger.info(f"削除: {backup_dir.name}")
            except Exception as e:
                self.logger.warning(f"削除失敗: {backup_dir.name} - {e}")
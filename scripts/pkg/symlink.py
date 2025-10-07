"""
シンボリックリンク管理モジュール

dotfilesのシンボリックリンク作成と管理を行う
"""

import os
import shutil
from enum import Enum
from pathlib import Path
from typing import List, Tuple

from .config import Config
from .logger import ColoredLogger


class LinkStatus(Enum):
    """シンボリックリンクの状態"""
    SKIP = "skip"           # 既に正しいリンクが存在
    UPDATE = "update"       # 既存のシンボリックリンクを更新
    BACKUP = "backup"       # 通常ファイルをバックアップして置換
    CREATE = "create"       # 新規作成


class SymlinkManager:
    """シンボリックリンク管理クラス"""

    def __init__(self, logger: ColoredLogger, config: Config):
        self.logger = logger
        self.config = config

    def check_status(self, source: Path, target: Path) -> Tuple[LinkStatus, str]:
        """
        シンボリックリンクの状態をチェック

        Args:
            source: ソースファイルのパス
            target: ターゲットファイルのパス

        Returns:
            (状態, 詳細メッセージ)
        """
        if target.is_symlink():
            try:
                current_target = target.readlink()
                if current_target == source:
                    return LinkStatus.SKIP, "既に正しいリンクが存在"
                else:
                    return LinkStatus.UPDATE, f"リンク先変更: {current_target.name} -> {source.name}"
            except OSError:
                # 壊れたシンボリックリンク
                return LinkStatus.UPDATE, "壊れたシンボリックリンクを修復"
        elif target.exists():
            return LinkStatus.BACKUP, "既存ファイルをバックアップして置換"
        else:
            return LinkStatus.CREATE, "新規リンク作成"

    def create_symlink(self, source: Path, target: Path, force: bool = False) -> bool:
        """
        シンボリックリンクを作成

        Args:
            source: ソースファイルのパス
            target: ターゲットファイルのパス
            force: 強制実行フラグ

        Returns:
            True: 成功, False: 失敗
        """
        try:
            # ソースファイルの存在確認
            if not source.exists():
                self.logger.error(f"ソースファイルが存在しません: {source}")
                return False

            status, message = self.check_status(source, target)
            relative_path = target.relative_to(self.config.target_dir)

            # 状態に応じて処理
            if status == LinkStatus.SKIP:
                self.logger.info(f"スキップ: {relative_path} ({message})")
                return True

            elif status in (LinkStatus.UPDATE, LinkStatus.BACKUP):
                self.logger.info(f"処理対象: {relative_path} ({message})")

                # 既存ファイルのバックアップ
                if target.exists() or target.is_symlink():
                    self._backup_file(target)
                    target.unlink(missing_ok=True)

            elif status == LinkStatus.CREATE:
                self.logger.info(f"新規作成: {relative_path}")

            # 親ディレクトリの作成
            target.parent.mkdir(parents=True, exist_ok=True)

            # シンボリックリンク作成（相対パスを使用）
            try:
                # targetからsourceへの相対パスを計算
                relative_source = os.path.relpath(source, target.parent)
                target.symlink_to(relative_source)
                self.logger.success(f"作成: {relative_path}")
            except (ValueError, OSError):
                # 相対パス計算に失敗した場合は絶対パスにフォールバック
                target.symlink_to(source)
                self.logger.success(f"作成: {relative_path} (絶対パス)")
            return True

        except Exception as e:
            self.logger.error(f"作成失敗: {target.relative_to(self.config.target_dir)} - {e}")
            return False

    def _backup_file(self, target: Path):
        """ファイルをバックアップ"""
        try:
            # バックアップファイル名を決定（重複回避）
            backup_file = self.config.backup_dir / target.name

            # 同名ファイルが既にある場合は連番を付ける
            counter = 1
            original_name = target.name

            # ファイル名の構造を一度だけ解析
            if original_name.startswith('.'):
                # dotfileの場合
                remaining = original_name[1:]  # 最初のピリオドを除く
                if '.' in remaining:
                    # dotfileで拡張子あり: .config.json -> .config_1.json
                    parts = remaining.split('.')
                    base = '.' + '.'.join(parts[:-1])
                    ext = parts[-1]
                    name_template = lambda c: f"{base}_{c}.{ext}"
                else:
                    # dotfileで拡張子なし: .bashrc -> .bashrc_1
                    name_template = lambda c: f"{original_name}_{c}"
            elif '.' in original_name and not original_name.endswith('.'):
                # 通常ファイルで拡張子あり: file.txt -> file_1.txt
                parts = original_name.split('.')
                base = '.'.join(parts[:-1])
                ext = parts[-1]
                name_template = lambda c: f"{base}_{c}.{ext}"
            else:
                # 拡張子なし、または末尾ピリオド: README -> README_1, script. -> script._1
                name_template = lambda c: f"{original_name}_{c}"

            # 重複しないファイル名を生成
            while backup_file.exists():
                name = name_template(counter)
                backup_file = self.config.backup_dir / name
                counter += 1

            if target.is_symlink():
                # シンボリックリンクの場合はリンク情報を保存
                link_target = target.readlink()
                link_info_file = backup_file.with_suffix('.link')
                with open(link_info_file, 'w') as f:
                    f.write(str(link_target))
                # シンボリックリンク自体のメタデータも保存（オプション）
                try:
                    # 元のシンボリックリンクファイルも保存（デバッグ用）
                    shutil.copy2(target, backup_file, follow_symlinks=False)
                except OSError:
                    # シンボリックリンクのコピーに失敗した場合は情報ファイルのみ
                    pass
            else:
                # 通常ファイルをコピー
                shutil.copy2(target, backup_file)

            self.logger.info(f"バックアップ: {target.name}")

        except Exception as e:
            self.logger.warning(f"バックアップ失敗: {target.name} - {e}")

    def get_dotfiles(self, script_dir: Path, exclude_manager) -> List[Path]:
        """
        dotfilesのリストを取得

        Args:
            script_dir: スクリプトディレクトリ
            exclude_manager: 除外マネージャー

        Returns:
            dotfilesのパスリスト
        """
        dotfiles = []

        # 隠しファイルを再帰的に検索
        for file_path in script_dir.rglob(".*"):
            if not file_path.is_file():
                continue

            # 除外対象をスキップ
            if exclude_manager.is_excluded(file_path, script_dir):
                continue

            dotfiles.append(file_path)

        return sorted(dotfiles)

    def preview_changes(self, dotfiles: List[Path], script_dir: Path) -> dict:
        """
        変更内容をプレビュー

        Args:
            dotfiles: dotfilesのリスト
            script_dir: スクリプトディレクトリ

        Returns:
            各状態の件数を含む辞書
        """
        counts = {
            'skip': 0,
            'update': 0,
            'backup': 0,
            'create': 0
        }

        for source in dotfiles:
            relative_path = source.relative_to(script_dir)
            target = self.config.target_dir / relative_path

            status, message = self.check_status(source, target)
            counts[status.value] += 1

            # ドライラン時の表示
            action_labels = {
                LinkStatus.SKIP: "[SKIP]",
                LinkStatus.UPDATE: "[UPDATE]",
                LinkStatus.BACKUP: "[BACKUP]",
                LinkStatus.CREATE: "[CREATE]"
            }

            print(f"{action_labels[status]} {relative_path} ({message})")

        return counts
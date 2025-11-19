"""Plan を実際に適用する実行ロジック."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path

from ..backup_store import BackupManager
from ..logger import ColoredLogger
from ..ui import UserInterface

from .model import ActionType, Plan, PlanEntry


@dataclass
class ExecutionReport:
    """実行結果の簡易統計."""

    applied: int = 0
    skipped: int = 0
    errors: int = 0


class PlanExecutor:
    """Plan をもとにファイル操作を行う."""

    def __init__(self, ui: UserInterface, logger: ColoredLogger, backup_manager: BackupManager) -> None:
        self.ui = ui
        self.logger = logger
        self.backup_manager = backup_manager

    def execute(self, plan: Plan, *, dry_run: bool = False) -> ExecutionReport:
        report = ExecutionReport()

        if not dry_run and any(entry.needs_backup for entry in plan.entries):
            self.backup_manager.start()

        for entry in plan.entries:
            try:
                handled = self._handle_entry(entry, dry_run=dry_run)
            except Exception as error:  # pragma: no cover - ログを出して続行
                self.logger.error(f"処理中にエラー: {entry.spec.relative_path} - {error}")
                report.errors += 1
                continue

            if handled:
                report.applied += 1
            else:
                report.skipped += 1

        return report

    def _handle_entry(self, entry: PlanEntry, *, dry_run: bool) -> bool:
        action = entry.action

        if action is ActionType.ERROR:
            self.logger.warning(entry.describe())
            return False

        if action is ActionType.ENSURE_DIR:
            return self._ensure_directory(entry, dry_run=dry_run)

        if action is ActionType.SKIP:
            self.logger.info(entry.describe())
            return False

        if action in {ActionType.CREATE, ActionType.UPDATE, ActionType.BACKUP_ONLY}:
            return self._process_file(entry, dry_run=dry_run)

        self.logger.warning(f"未対応のアクション種別: {action}")
        return False

    def _ensure_directory(self, entry: PlanEntry, *, dry_run: bool) -> bool:
        dest_dir = entry.spec.dest
        if dry_run:
            self.logger.info(f"[DRY-RUN] mkdir -p {entry.spec.relative_path}")
            return False

        if dest_dir.exists():
            return False

        dest_dir.mkdir(parents=True, exist_ok=True)
        self.logger.success(f"ディレクトリ作成: {entry.spec.relative_path}")
        return True

    def _process_file(self, entry: PlanEntry, *, dry_run: bool) -> bool:
        dest_path = entry.spec.dest
        source_path = entry.spec.source

        if dry_run:
            self.logger.info(f"[DRY-RUN] {entry.describe()}")
            return False

        if entry.needs_confirmation and not self.ui.confirm(
            f"{entry.spec.relative_path} を処理しますか?", default_yes=True
        ):
            self.logger.info(f"スキップ: {entry.spec.relative_path}")
            return False

        if entry.needs_backup and dest_path.exists() or dest_path.is_symlink():
            relative = entry.spec.relative_path
            try:
                self.backup_manager.backup(dest_path, relative)
                self.logger.info(f"バックアップ: {relative}")
            except Exception as error:
                self.logger.warning(f"バックアップ失敗: {relative} - {error}")

        if dest_path.exists() or dest_path.is_symlink():
            dest_path.unlink()

        dest_path.parent.mkdir(parents=True, exist_ok=True)

        if source_path.is_symlink():
            link_target = os.readlink(source_path)
            dest_path.symlink_to(link_target)
        else:
            # 絶対パスでシンボリックリンクを作成
            dest_path.symlink_to(source_path.resolve())

        self.logger.success(f"適用: {entry.spec.relative_path}")
        return True

"""Plan を生成するビルダー."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .model import ActionType, InstallSpec, Plan, PlanEntry


@dataclass
class PlanBuilder:
    """source directory の内容から Plan を生成するユーティリティ."""

    source_dir: Path
    dest_dir: Path

    def build(self) -> Plan:
        source_dir = self.source_dir
        # source directory がないときはどうしようもない
        if not source_dir.exists():
            return Plan(entries=[PlanEntry(
                spec=InstallSpec(source_dir, Path("."), source_dir),
                action=ActionType.ERROR,
                message="source directory が存在しません",
                blocked_reason="source directoryを作成してください",
            )])

        entries: list[PlanEntry] = []

        # 先にディレクトリを処理しておく（mkdir -p 相当）
        for directory in sorted(p for p in source_dir.rglob("*") if p.is_dir()):
            relative = directory.relative_to(source_dir)
            dest_dir = self.dest_dir / relative
            # 既にディレクトリが存在する場合はスキップ
            if dest_dir.exists() and dest_dir.is_dir():
                continue
            entries.append(self._plan_ensure_directory(InstallSpec(
                source=directory,
                relative_path=relative,
                dest=dest_dir,
            )))

        for source in sorted(source_dir.rglob("*")):
            if source.is_dir():
                continue

            # symlink は対応しない
            if source.is_symlink():
                entries.append(self._plan_unsupported_link(source_dir, source))
                continue

            relative = source.relative_to(source_dir)
            dest = self.dest_dir / relative
            spec = InstallSpec(source=source, relative_path=relative, dest=dest)
            entries.append(self._decide_action(spec))

        return Plan(entries=entries)

    @staticmethod
    def _plan_ensure_directory(spec: InstallSpec) -> PlanEntry:
        """ホーム側ディレクトリの作成を計画する."""

        return PlanEntry(
            spec=spec,
            action=ActionType.ENSURE_DIR,
            message="mkdir -p でディレクトリを作成予定",
        )

    @staticmethod
    def _plan_unsupported_link(source_dir: Path, source: Path) -> PlanEntry:
        """source/ 内のシンボリックリンクに対するエラーを生成."""

        spec = InstallSpec(
            source=source,
            relative_path=source.relative_to(source_dir),
            dest=Path("-"),
        )
        return PlanEntry(
            spec=spec,
            action=ActionType.ERROR,
            message="source/ 内のシンボリックリンクは未対応です",
            blocked_reason="通常ファイルを配置してください",
        )

    @staticmethod
    def _decide_action(spec: InstallSpec) -> PlanEntry:
        """InstallSpec のファイル種別を見て適切なアクションを決定する."""
        dest = spec.dest

        # ファイルもシンボリックリンクも存在しない場合は新規作成
        # exists() はリンク先の存在を見るため、壊れたリンクは exists()=False, is_symlink()=True となる
        if not (dest.exists() or dest.is_symlink()):
            return PlanEntry(
                spec=spec,
                action=ActionType.CREATE,
                message="新規リンクを作成予定",
            )

        if dest.is_symlink():
            try:
                current = dest.resolve()
            except OSError:
                return PlanEntry(
                    spec=spec,
                    action=ActionType.UPDATE,
                    message="壊れたリンクを置き換え",
                    needs_confirmation=True,
                    needs_backup=True,
                )
            if current == spec.source.resolve():
                return PlanEntry(
                    spec=spec,
                    action=ActionType.SKIP,
                    message="既に正しいリンクです",
                )
            return PlanEntry(
                spec=spec,
                action=ActionType.UPDATE,
                message=f"リンク先を {current} から置き換え",
                needs_confirmation=True,
                needs_backup=True,
            )

        if dest.is_file():
            return PlanEntry(
                spec=spec,
                action=ActionType.UPDATE,
                message="既存ファイルをバックアップして上書き",
                needs_confirmation=True,
                needs_backup=True,
            )

        if dest.is_dir():
            return PlanEntry(
                spec=spec,
                action=ActionType.ERROR,
                message="同名のディレクトリが存在するためリンク不可",
                blocked_reason="source/ 側のディレクトリ構成を見直してください",
            )

        return PlanEntry(
            spec=spec,
            action=ActionType.ERROR,
            message="想定外のファイル種別です",
        )

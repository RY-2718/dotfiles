"""バックアップアーカイブからの復元処理を提供."""

from __future__ import annotations

import shutil
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class RollbackManager:
    """ロールバックアーカイブの適用を管理."""

    target_root: Path
    ui: Any

    def restore_archive(
        self,
        archive: Path,
        *,
        restore_all: bool = False,
        selected: Iterable[Path] | None = None,
    ) -> None:
        if not archive.exists():
            raise FileNotFoundError(f"バックアップが見つかりません: {archive}")

        selected_set = {p for p in selected} if selected else None

        for entry, info in self._iter_backup_entries(archive):
            relative_path = entry
            if selected_set is not None and relative_path not in selected_set:
                continue

            target = self.target_root / relative_path

            if not restore_all:
                if not self.ui.confirm(f"{relative_path} を復元しますか?", default_yes=False):
                    continue

            target.parent.mkdir(parents=True, exist_ok=True)

            if info == "symlink":
                link_file = archive / f"{relative_path}.link"
                link_target = Path(link_file.read_text().strip())
                target.unlink(missing_ok=True)
                target.symlink_to(link_target)
            else:
                source = archive / relative_path
                if target.exists() or target.is_symlink():
                    target.unlink()
                shutil.copy2(source, target)

    def _iter_backup_entries(self, archive: Path):
        for path in sorted(archive.rglob("*")):
            if path.is_dir():
                continue
            if path.name.endswith(".link"):
                relative = path.relative_to(archive)
                original = relative.with_suffix("")
                yield original, "symlink"
            else:
                relative = path.relative_to(archive)
                # `.link` とは別に同名ファイルが存在する可能性があるため
                if (archive / f"{relative}.link").exists():
                    continue
                yield relative, "file"

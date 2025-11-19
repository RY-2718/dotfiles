"""バックアップ（ロールバック用アーカイブ）管理モジュール."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional


@dataclass
class BackupManager:
    """1回のインストール実行で生成するバックアップを管理."""

    rollbacks_root: Path

    current_dir: Optional[Path] = None

    def start(self) -> Path:
        """新しいバックアップディレクトリを作成してパスを返す."""

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive = self.rollbacks_root / timestamp
        archive.mkdir(parents=True, exist_ok=False)
        self.current_dir = archive
        return archive

    def is_active(self) -> bool:
        return self.current_dir is not None

    def backup(self, source: Path, relative_path: Path) -> None:
        """対象ファイル/リンクをバックアップする."""

        if self.current_dir is None:
            raise RuntimeError("BackupManager.start() が呼ばれていません")

        destination = self.current_dir / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)

        # symlink の場合はリンク先情報を .link ファイルに保存
        if source.is_symlink():
            link_target = source.readlink()
            info_path = destination.with_name(destination.name + ".link")
            info_path.write_text(str(link_target))
        else:
            shutil.copy2(source, destination)

    def available_archives(self) -> list[Path]:
        """既存のバックアップディレクトリ一覧を新しい順で返す."""

        if not self.rollbacks_root.exists():
            return []
        archives = [p for p in self.rollbacks_root.iterdir() if p.is_dir()]
        return sorted(archives, reverse=True)

    def resolve_archive(self, name: Optional[str]) -> Optional[Path]:
        """指定名のアーカイブパスを取得（未指定時は最新）。"""

        archives = self.available_archives()
        if not archives:
            return None
        if not name:
            return archives[0]
        candidate = self.rollbacks_root / name
        return candidate if candidate.exists() else None

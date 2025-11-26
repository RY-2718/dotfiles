"""バックアップ（ロールバック用アーカイブ）管理モジュール."""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class BackupManager:
    """1回のインストール実行で生成するバックアップを管理."""

    rollbacks_root: Path

    current_dir: Path | None = None

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

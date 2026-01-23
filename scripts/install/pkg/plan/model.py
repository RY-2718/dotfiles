"""Plan関連のデータモデル定義."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path


class ActionType(Enum):
    """インストール時に取り得る処理種別."""

    ENSURE_DIR = auto()
    SKIP = auto()
    CREATE = auto()
    UPDATE = auto()
    BACKUP_ONLY = auto()
    ERROR = auto()


@dataclass(frozen=True)
class InstallSpec:
    """インストール対象のファイル/ディレクトリ1件分の仕様情報.

    source: 参照元ファイル/ディレクトリ (source/ 配下)
    relative_path: インストール先での相対パス (例: .bashrc, .config/test.conf)
    dest: インストール先の絶対パス
    """

    source: Path
    relative_path: Path
    dest: Path


@dataclass
class PlanEntry:
    """1エントリ分の計画内容. PlanEntry を見ればどんな操作が必要か分かる."""

    spec: InstallSpec
    action: ActionType
    message: str = ""
    needs_confirmation: bool = False
    needs_backup: bool = False
    blocked_reason: str | None = None

    def describe(self) -> str:
        """人間向けにシンプルな説明文を返す."""
        parts = [f"[{self.action.name}] {self.spec.relative_path}"]
        if self.message:
            parts.append(self.message)
        if self.blocked_reason:
            parts.append(f"理由: {self.blocked_reason}")
        return " - ".join(parts)


@dataclass
class Plan:
    """インストール処理全体の計画. PlanEntry を集めたもの + いくつかのユーティリティメソッド."""

    entries: list[PlanEntry] = field(default_factory=list)

    def summary(self) -> PlanSummary:
        summary = PlanSummary()
        for entry in self.entries:
            summary.increment(entry.action)
        return summary

    def iter_confirmations(self) -> Iterable[PlanEntry]:
        """ユーザー確認が必要なアクションを列挙."""
        return (entry for entry in self.entries if entry.needs_confirmation)


@dataclass
class PlanSummary:
    """Plan全体の統計情報. 各アクション種別ごとの件数を保持."""

    counts: dict[ActionType, int] = field(default_factory=dict)

    def increment(self, action_type: ActionType) -> None:
        self.counts[action_type] = self.counts.get(action_type, 0) + 1

    def format_lines(self) -> list[str]:
        if not self.counts:
            return ["処理対象がありません"]
        lines = ["処理予定件数:"]
        for action_type in ActionType:
            if action_type in self.counts:
                lines.append(f"  - {action_type.name}: {self.counts[action_type]} 件")
        return lines

    # 旧API互換用の便利プロパティ
    @property
    def ensure_dirs(self) -> int:
        return self.counts.get(ActionType.ENSURE_DIR, 0)

    @property
    def creates(self) -> int:
        return self.counts.get(ActionType.CREATE, 0)

    @property
    def updates(self) -> int:
        return self.counts.get(ActionType.UPDATE, 0)

    @property
    def skips(self) -> int:
        return self.counts.get(ActionType.SKIP, 0)

    @property
    def errors(self) -> int:
        return self.counts.get(ActionType.ERROR, 0)

    @property
    def total(self) -> int:
        return sum(self.counts.values())

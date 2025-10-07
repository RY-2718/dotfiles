"""
除外ファイル管理モジュール

.installignoreファイルの読み込みと除外判定を行う
"""

import fnmatch
import re
from pathlib import Path
from typing import List, Set, Tuple


class ExcludeManager:
    """除外ファイル管理クラス"""

    def __init__(self, ignore_file: Path, default_excludes: Set[str]):
        self.ignore_file = ignore_file
        self.default_excludes = default_excludes
        self.patterns: List[Tuple[str, str]] = []  # [('exclude'|'include', 'pattern'), ...]
        self._load_patterns()

    def _load_patterns(self):
        """除外パターンを読み込み"""
        # デフォルト除外パターンを追加
        for exclude in self.default_excludes:
            self.patterns.append(('exclude', exclude))

        # .installignoreファイルから読み込み
        if not self.ignore_file.exists():
            return

        try:
            with open(self.ignore_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    line = line.strip()

                    # 空行とコメント行をスキップ
                    if not line or line.startswith('#'):
                        continue

                    # 除外解除パターン（!で始まる）
                    if line.startswith('!'):
                        pattern = line[1:]
                        if pattern:  # 空でない場合のみ
                            self.patterns.append(('include', pattern))
                    else:
                        self.patterns.append(('exclude', line))

        except Exception as e:
            # ファイル読み込みエラーは警告レベルで処理
            print(f"警告: .installignoreファイルの読み込みに失敗しました: {e}")

    def is_excluded(self, file_path: Path, script_dir: Path) -> bool:
        """
        ファイルが除外対象かどうかを判定

        Args:
            file_path: 対象ファイルのパス
            script_dir: スクリプトディレクトリのパス

        Returns:
            True: 除外対象, False: インストール対象
        """
        filename = file_path.name
        relative_path = str(file_path.relative_to(script_dir))

        is_excluded = False
        longest_match_len = 0

        for action, pattern in self.patterns:
            if self._matches_pattern(pattern, filename, relative_path):
                # longest matchで判定
                if len(pattern) > longest_match_len:
                    longest_match_len = len(pattern)
                    is_excluded = (action == 'exclude')

        return is_excluded

    def _matches_pattern(self, pattern: str, filename: str, relative_path: str) -> bool:
        """
        パターンマッチング判定

        Args:
            pattern: マッチングパターン
            filename: ファイル名
            relative_path: 相対パス

        Returns:
            True: マッチする, False: マッチしない
        """
        # ディレクトリパターン（末尾が/）
        if pattern.endswith('/'):
            dir_pattern = pattern[:-1]
            return (relative_path == dir_pattern or
                    relative_path.startswith(dir_pattern + '/'))

        # ワイルドカードパターン
        if '*' in pattern or '?' in pattern or '[' in pattern:
            return (fnmatch.fnmatch(filename, pattern) or
                    fnmatch.fnmatch(relative_path, pattern))

        # 完全一致
        return filename == pattern or relative_path == pattern

    def get_patterns_info(self) -> dict:
        """除外パターンの情報を取得"""
        exclude_count = sum(1 for action, _ in self.patterns if action == 'exclude')
        include_count = sum(1 for action, _ in self.patterns if action == 'include')

        return {
            'total': len(self.patterns),
            'exclude': exclude_count,
            'include': include_count,
            'patterns': self.patterns
        }
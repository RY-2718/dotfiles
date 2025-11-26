"""
カラフルなログ出力モジュール

標準ライブラリのloggingを拡張してカラー出力に対応
"""

from __future__ import annotations

import logging
import sys
from pathlib import Path


class ColorCode:
    """ANSI カラーコード定数"""

    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    BLUE = "\033[0;34m"
    MAGENTA = "\033[0;35m"
    CYAN = "\033[0;36m"
    WHITE = "\033[1;37m"
    RESET = "\033[0m"

    # 絵文字
    INFO = "ℹ"
    SUCCESS = "✓"
    WARNING = "⚠"
    ERROR = "✗"
    DEBUG = "🔍"


class ColoredFormatter(logging.Formatter):
    """カラー対応フォーマッター"""

    def __init__(self, use_color: bool = True):
        super().__init__()
        self.use_color = use_color and sys.stdout.isatty()

        # ログレベル別の色設定
        self.colors = {
            logging.DEBUG: ColorCode.CYAN,
            logging.INFO: ColorCode.BLUE,
            logging.WARNING: ColorCode.YELLOW,
            logging.ERROR: ColorCode.RED,
            logging.CRITICAL: ColorCode.MAGENTA,
        }

        # ログレベル別のアイコン
        self.icons = {
            logging.DEBUG: ColorCode.DEBUG,
            logging.INFO: ColorCode.INFO,
            logging.WARNING: ColorCode.WARNING,
            logging.ERROR: ColorCode.ERROR,
            logging.CRITICAL: ColorCode.ERROR,
        }

    def format(self, record: logging.LogRecord) -> str:
        # タイムスタンプ付きフォーマット
        timestamp = self.formatTime(record, "%Y-%m-%d %H:%M:%S")

        if self.use_color:
            color = self.colors.get(record.levelno, ColorCode.WHITE)
            icon = self.icons.get(record.levelno, "")

            # コンソール用（カラー + アイコン）
            console_msg = f"{color}{icon}{ColorCode.RESET} {record.getMessage()}"

            # ファイル用（プレーンテキスト）
            file_msg = f"[{timestamp}] [{record.levelname}] {record.getMessage()}"

            # recordにファイル用メッセージを保存
            record.file_message = file_msg

            return console_msg
        else:
            return f"[{timestamp}] [{record.levelname}] {record.getMessage()}"


class FileHandler(logging.FileHandler):
    """ファイル出力専用ハンドラー（カラーコードを除去）

    ColoredFormatterが生成した file_message をそのままファイルに出力する。
    file_message は既に完全なフォーマット済み文字列なので、
    標準のフォーマッターを使わずに直接書き込む。
    """

    def emit(self, record: logging.LogRecord):
        try:
            # file_message があればそれを使用（既に完全フォーマット済み）
            if hasattr(record, "file_message"):
                msg = record.file_message
            else:
                # なければ標準フォーマット
                msg = self.format(record)

            # ファイルに書き込み
            stream = self.stream
            stream.write(msg + self.terminator)
            self.flush()
        except Exception:
            self.handleError(record)


class ColoredLogger:
    """カラー対応ロガークラス"""

    def __init__(self, name: str, log_file: Path | None = None):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # 既存のハンドラーをクリア（ファイルを適切に閉じる）
        for handler in self.logger.handlers[:]:
            handler.close()
            self.logger.removeHandler(handler)

        # コンソールハンドラー
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(ColoredFormatter(use_color=True))
        self.logger.addHandler(console_handler)

        # ファイルハンドラー（指定された場合のみ）
        if log_file:
            file_handler = FileHandler(log_file, mode="w", encoding="utf-8")
            file_handler.setFormatter(ColoredFormatter(use_color=False))
            self.logger.addHandler(file_handler)

    def debug(self, message: str):
        """デバッグメッセージ"""
        self.logger.debug(message)

    def info(self, message: str):
        """情報メッセージ"""
        self.logger.info(message)

    def success(self, message: str):
        """成功メッセージ（INFOレベルだが緑色で表示）"""
        # 成功メッセージ用に一時的にフォーマッターを変更
        for handler in self.logger.handlers:
            if isinstance(handler.formatter, ColoredFormatter):
                original_colors = handler.formatter.colors.copy()
                original_icons = handler.formatter.icons.copy()
                handler.formatter.colors[logging.INFO] = ColorCode.GREEN
                handler.formatter.icons[logging.INFO] = ColorCode.SUCCESS

                self.logger.info(message)

                # 元に戻す
                handler.formatter.colors = original_colors
                handler.formatter.icons = original_icons
                break
        else:
            self.logger.info(message)

    def warning(self, message: str):
        """警告メッセージ"""
        self.logger.warning(message)

    def error(self, message: str):
        """エラーメッセージ"""
        self.logger.error(message)

    def set_level(self, level):
        """ログレベルを設定"""
        self.logger.setLevel(level)

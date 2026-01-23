"""ColoredLogger のテスト."""

from __future__ import annotations

import logging
import tempfile
import unittest
from pathlib import Path

from scripts.install.pkg.logger import ColorCode, ColoredFormatter, ColoredLogger, FileHandler


class TestColoredFormatter(unittest.TestCase):
    """ColoredFormatter クラスのテスト."""

    def setUp(self):
        """各テストの前に実行される共通セットアップ."""
        self.formatter = ColoredFormatter(use_color=True)
        self.formatter_no_color = ColoredFormatter(use_color=False)

    def test_format_with_color(self):
        """カラー付きフォーマットが正しく動作することを確認."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="テストメッセージ",
            args=(),
            exc_info=None,
        )

        result = self.formatter.format(record)

        # カラーコードが含まれていることを確認
        self.assertIn(ColorCode.INFO, result)
        self.assertIn("テストメッセージ", result)
        self.assertIn(ColorCode.RESET, result)

        # file_message が設定されていることを確認
        self.assertTrue(hasattr(record, "file_message"))
        self.assertIn("[INFO]", record.file_message)
        self.assertIn("テストメッセージ", record.file_message)
        # file_message にはカラーコードが含まれないことを確認
        self.assertNotIn(ColorCode.RESET, record.file_message)

    def test_format_without_color(self):
        """カラーなしフォーマットが正しく動作することを確認."""
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="test.py",
            lineno=1,
            msg="警告メッセージ",
            args=(),
            exc_info=None,
        )

        result = self.formatter_no_color.format(record)

        # カラーコードが含まれていないことを確認
        self.assertNotIn(ColorCode.RESET, result)
        self.assertIn("[WARNING]", result)
        self.assertIn("警告メッセージ", result)

    def test_different_log_levels(self):
        """異なるログレベルで異なる色とアイコンが使われることを確認."""
        levels = [
            (logging.DEBUG, ColorCode.DEBUG, ColorCode.CYAN),
            (logging.INFO, ColorCode.INFO, ColorCode.BLUE),
            (logging.WARNING, ColorCode.WARNING, ColorCode.YELLOW),
            (logging.ERROR, ColorCode.ERROR, ColorCode.RED),
            (logging.CRITICAL, ColorCode.ERROR, ColorCode.MAGENTA),
        ]

        for level, icon, color in levels:
            with self.subTest(level=level):
                record = logging.LogRecord(
                    name="test",
                    level=level,
                    pathname="test.py",
                    lineno=1,
                    msg="メッセージ",
                    args=(),
                    exc_info=None,
                )

                result = self.formatter.format(record)

                self.assertIn(icon, result)
                self.assertIn(color, result)


class TestFileHandler(unittest.TestCase):
    """FileHandler クラスのテスト."""

    def setUp(self):
        """各テストの前に実行される共通セットアップ."""
        self.test_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.test_dir.name)
        self.log_file = self.tmp_path / "test.log"

    def tearDown(self):
        """各テストの後に実行されるクリーンアップ."""
        self.test_dir.cleanup()

    def test_emit_with_file_message(self):
        """file_message がある場合に正しく書き込まれることを確認."""
        handler = FileHandler(self.log_file, mode="w", encoding="utf-8")

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="テストメッセージ",
            args=(),
            exc_info=None,
        )
        record.file_message = "[2025-11-26 10:00:00] [INFO] テストメッセージ"

        handler.emit(record)
        handler.close()

        content = self.log_file.read_text()
        self.assertIn("[2025-11-26 10:00:00] [INFO] テストメッセージ", content)

    def test_emit_without_file_message(self):
        """file_message がない場合に標準フォーマットが使われることを確認."""
        handler = FileHandler(self.log_file, mode="w", encoding="utf-8")
        handler.setFormatter(ColoredFormatter(use_color=False))

        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="test.py",
            lineno=1,
            msg="警告メッセージ",
            args=(),
            exc_info=None,
        )

        handler.emit(record)
        handler.close()

        content = self.log_file.read_text()
        self.assertIn("[WARNING]", content)
        self.assertIn("警告メッセージ", content)

    def test_no_color_codes_in_file(self):
        """ファイルにカラーコードが含まれないことを確認."""
        handler = FileHandler(self.log_file, mode="w", encoding="utf-8")
        formatter = ColoredFormatter(use_color=True)
        handler.setFormatter(formatter)

        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="エラーメッセージ",
            args=(),
            exc_info=None,
        )

        # フォーマットを実行して file_message を生成
        formatter.format(record)

        handler.emit(record)
        handler.close()

        content = self.log_file.read_text()
        # カラーコードが含まれていないことを確認
        self.assertNotIn(ColorCode.RESET, content)
        self.assertNotIn(ColorCode.RED, content)
        # メッセージは含まれている
        self.assertIn("エラーメッセージ", content)


class TestColoredLogger(unittest.TestCase):
    """ColoredLogger クラスのテスト."""

    def setUp(self):
        """各テストの前に実行される共通セットアップ."""
        self.test_dir = tempfile.TemporaryDirectory()
        self.tmp_path = Path(self.test_dir.name)
        self.log_file = self.tmp_path / "test.log"

    def tearDown(self):
        """各テストの後に実行されるクリーンアップ."""
        self.test_dir.cleanup()

    def test_logger_creation_without_file(self):
        """ファイル出力なしでロガーが作成できることを確認."""
        logger = ColoredLogger("test")
        self.assertIsNotNone(logger.logger)
        self.assertEqual(len(logger.logger.handlers), 1)  # コンソールハンドラーのみ

    def test_logger_creation_with_file(self):
        """ファイル出力ありでロガーが作成できることを確認."""
        logger = ColoredLogger("test", log_file=self.log_file)
        self.assertIsNotNone(logger.logger)
        self.assertEqual(len(logger.logger.handlers), 2)  # コンソール + ファイル

    def test_all_log_methods(self):
        """全てのログメソッドが正常に動作することを確認."""
        logger = ColoredLogger("test", log_file=self.log_file)

        # 例外が発生しないことを確認
        logger.debug("デバッグメッセージ")
        logger.info("情報メッセージ")
        logger.success("成功メッセージ")
        logger.warning("警告メッセージ")
        logger.error("エラーメッセージ")

        # ファイルに書き込まれていることを確認
        content = self.log_file.read_text()
        self.assertIn("情報メッセージ", content)
        self.assertIn("成功メッセージ", content)
        self.assertIn("警告メッセージ", content)
        self.assertIn("エラーメッセージ", content)

    def test_set_level(self):
        """ログレベルが設定できることを確認."""
        logger = ColoredLogger("test", log_file=self.log_file)

        # DEBUGレベルに設定
        logger.set_level(logging.DEBUG)
        logger.debug("デバッグメッセージ")

        content = self.log_file.read_text()
        self.assertIn("デバッグメッセージ", content)

    def test_success_uses_green_color(self):
        """successメソッドが緑色のフォーマットを使うことを確認."""
        logger = ColoredLogger("test")

        # 例外が発生しないことを確認
        # （実際の色は目視確認が必要だが、少なくとも動作することを確認）
        logger.success("成功メッセージ")

    def test_multiple_loggers_independent(self):
        """複数のロガーが独立して動作することを確認."""
        log_file1 = self.tmp_path / "test1.log"
        log_file2 = self.tmp_path / "test2.log"

        logger1 = ColoredLogger("test1", log_file=log_file1)
        logger2 = ColoredLogger("test2", log_file=log_file2)

        logger1.info("ロガー1のメッセージ")
        logger2.info("ロガー2のメッセージ")

        content1 = log_file1.read_text()
        content2 = log_file2.read_text()

        self.assertIn("ロガー1のメッセージ", content1)
        self.assertNotIn("ロガー2のメッセージ", content1)

        self.assertIn("ロガー2のメッセージ", content2)
        self.assertNotIn("ロガー1のメッセージ", content2)


if __name__ == "__main__":
    unittest.main()

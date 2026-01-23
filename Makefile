.PHONY: help test test-verbose install dry-run rollback clean lint format check

# デフォルトターゲット: ヘルプを表示
help:
	@echo "利用可能なコマンド:"
	@echo "  make test          - テストを実行"
	@echo "  make test-v        - 詳細表示でテストを実行"
	@echo "  make install       - dotfilesをインストール"
	@echo "  make dry-run       - インストールのプレビュー"
	@echo "  make rollback      - 最新のバックアップからロールバック"
	@echo "  make lint          - コードの静的解析（ruff）"
	@echo "  make format        - コードフォーマット（ruff）"
	@echo "  make check         - lint + format確認"
	@echo "  make clean         - 一時ファイルを削除"

# テスト実行
test:
	@python3 -m unittest discover -s scripts/install/tests

# 詳細表示でテスト実行
test-v:
	@python3 -m unittest discover -s scripts/install/tests -v

# dotfilesインストール
install:
	@python3 install.py

# ドライラン
dry-run:
	@python3 install.py --dry-run

# ロールバック
rollback:
	@python3 install.py --rollback

# コードの静的解析
lint:
	@if command -v ruff >/dev/null 2>&1; then \
		ruff check scripts/ install.py; \
	else \
		echo "ruffがインストールされていません。"; \
		echo "インストール: pipx install ruff または pip3 install ruff"; \
	fi

# コードフォーマット
format:
	@if command -v ruff >/dev/null 2>&1; then \
		ruff check --fix scripts/ install.py && \
		ruff format scripts/ install.py; \
	else \
		echo "ruffがインストールされていません。"; \
		echo "インストール: pipx install ruff または pip3 install ruff"; \
	fi

# コードフォーマット確認（変更なし）
format-check:
	@if command -v ruff >/dev/null 2>&1; then \
		ruff format --check scripts/ install.py; \
	else \
		echo "ruffがインストールされていません。"; \
	fi

# lint + format確認
check: lint format-check
	@echo "✓ コードチェック完了"

# 一時ファイルを削除
clean:
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@find . -type f -name "*.pyo" -delete 2>/dev/null || true
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@rm -f install.log 2>/dev/null || true
	@echo "✓ クリーンアップ完了"

# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a personal dotfiles repository containing shell configuration, vim settings, git configuration, and development environment setup for macOS/Linux systems. Uses a Python-based installation script with automatic backup/rollback capabilities.

## Common Commands

### Installation and Setup
```bash
python3 install.py              # Interactive installation
python3 install.py --dry-run    # Preview changes without applying
python3 install.py --force      # Install without confirmation
python3 install.py --rollback   # Restore from backup
```

### Testing
```bash
python3 -m unittest discover -s scripts/tests  # Run all tests
```

### Prerequisites
The repository expects zplug to be installed:
```bash
curl -sL --proto-redir -all,https https://raw.githubusercontent.com/zplug/installer/master/installer.zsh | zsh
```

## Architecture and Structure

### Directory Structure
```
dotfiles/
├── source/              # Files to be symlinked to home directory
│   ├── .zshrc, .bashrc, etc.
│   ├── .config/         # Application configs
│   └── bin/, opt/, tools/  # Utility directories with READMEs
├── scripts/
│   ├── pkg/            # Installation script modules
│   │   ├── plan/       # Plan generation (Builder pattern)
│   │   │   ├── model.py      # Data models (InstallSpec, Plan, PlanEntry)
│   │   │   ├── builder.py    # Plan builder
│   │   │   └── executor.py   # Plan executor
│   │   ├── backup_store.py   # Backup management
│   │   ├── rollback_manager.py  # Rollback functionality
│   │   ├── logger.py         # Colored logging
│   │   └── ui.py             # User interaction
│   └── tests/          # Unit tests (unittest framework)
├── install.py          # Main installation script
├── rollbacks/          # Automatic backups (gitignored)
└── iterm2/, vue/       # Additional configs
```

### Installation Strategy

The installer uses a **Plan/Executor pattern**:

1. **Plan Generation** (`PlanBuilder`):
   - Scans `source/` directory
   - Determines actions for each file (CREATE/UPDATE/SKIP/ERROR)
   - Checks for conflicts and existing files
   - Generates a `Plan` with ordered entries

2. **Plan Execution** (`PlanExecutor`):
   - Creates backups before modifications
   - Creates absolute path symlinks: `~/.zshrc → /full/path/to/dotfiles/source/.zshrc`
   - Handles directory creation (`ENSURE_DIR`)
   - Provides dry-run mode for preview

3. **Backup/Rollback** (`BackupManager`, `RollbackManager`):
   - Automatic timestamped backups in `rollbacks/YYYYMMDD_HHMMSS/`
   - Symlinks stored as `.link` files containing target path
   - Interactive rollback with file selection

### Core Components

**Installation Script** (`scripts/pkg/`):
- **Model** (`plan/model.py`): Data classes for installation specs and plans
  - `InstallSpec`: Source file, destination path, relative path
  - `PlanEntry`: Action type, spec, message, confirmation flags
  - `Plan`: Collection of entries with summary
  - `ActionType`: ENSURE_DIR, CREATE, UPDATE, SKIP, ERROR
- **Builder** (`plan/builder.py`): Generates installation plan from source directory
  - Scans `source/` directory recursively
  - Determines appropriate action for each file
  - Detects conflicts and existing files
- **Executor** (`plan/executor.py`): Executes plan with backup support
  - Creates absolute path symlinks
  - Handles user confirmations
  - Integrates with BackupManager
- **Backup** (`backup_store.py`): Creates timestamped backups
  - Stores in `rollbacks/YYYYMMDD_HHMMSS/`
  - Symlinks saved as `.link` text files
- **Rollback** (`rollback_manager.py`): Restores from backups with interactive selection
  - Lists available backups
  - Shows before/after changes
  - Restores files and symlinks

### Key Features
- Plan-based installation with preview (dry-run)
- Automatic backup before any changes
- Interactive rollback with change visualization
- Absolute path symlinks for reliability
- Comprehensive test suite (21+ tests)

### Testing

Tests are located in `scripts/tests/` and use Python's built-in `unittest` framework (no external dependencies):
- `test_plan_builder.py` - Plan generation logic
- `test_plan_executor.py` - Plan execution and backup
- `test_rollback_manager.py` - Rollback functionality

Run tests with:
```bash
python3 -m unittest discover -s scripts/tests
```

### Development Notes

- All Python code uses type hints and dataclasses
- Symlinks are created with absolute paths for cross-directory reliability
- Backup symlinks stored as `.link` files (text files containing target path)
- Empty directories skipped during ENSURE_DIR to avoid unnecessary operations
- Tests cover all critical paths including edge cases (broken links, nested files, etc.)

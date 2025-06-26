# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Overview

This is a personal dotfiles repository containing shell configuration, vim settings, git configuration, and development environment setup for macOS/Linux systems.

## Common Commands

### Installation and Setup
- `./install.sh` - Symlinks dotfiles to home directory and copies template directories
- `git submodule update --init --recursive` - Updates submodules (as noted in README)

### Prerequisites
The repository expects zplug to be installed:
```bash
curl -sL --proto-redir -all,https https://raw.githubusercontent.com/zplug/installer/master/installer.zsh | zsh
```

## Architecture and Structure

### Core Components
- **Shell Configuration**: `.zshrc`, `.bashrc`, `.bash_profile`, `.zprofile` - Shell startup files with history settings, peco integration, and custom prompts
- **Shell Utilities**: `.aliases` - Common aliases with cross-platform compatibility for macOS/Linux
- **Editor Configuration**: `.vimrc`, `.gvimrc`, `.ideavimrc` - Vim settings with C-style indenting, search highlighting, and navigation improvements
- **Git Configuration**: `.gitconfig`, `.gitmessage.txt`, `.gitignore` - Git settings with SSH push configuration for GitHub/Bitbucket
- **Terminal Tools**: `.tmux.conf`, `.tigrc` - Terminal multiplexer and git CLI tool configurations
- **Application Configs**: `karabiner.json`, `iterm2/` directory - Keyboard remapping and terminal color schemes

### Installation Strategy
The `install.sh` script uses symbolic links for dotfiles and copies template directories (`bin/`, `opt/`, `tools/`) to avoid conflicts. It skips git-related files and system files during symlinking.

### Key Features
- Cross-platform shell aliases that detect OS type
- Peco integration for fuzzy command history search
- GHQ integration for repository management
- SSH-based git pushing while allowing HTTPS cloning
- Comprehensive vim configuration with syntax highlighting and smart indenting
#!/bin/bash
cd $(dirname $0)

for f in .??*
do
	[[ "$f" == ".git" ]] && continue
	[[ "$f" == ".DS_Store" ]] && continue
	[[ "$f" == ".gitignore" ]] && continue
	[[ "$f" == ".gitmodules" ]] && continue
	[[ "$f" == ".gitconfig" ]] && continue
	[[ "$f" == "install.sh" ]] && continue
    if [ "$f" == "com.googlecode.iterm2.plist" ]; then
        rm ~/Library/Preferences/com.googlecode.iterm2.plist
        ln -s ~/dotfiles/com.googlecode.iterm2.plist ~/Library/Preferences/com.googlecode.iterm2.plist
    fi

	ln -Fis "$PWD/$f" $HOME
	echo "$f"
done

# link Prezto.
# if [[ -s "${ZDOTDIR:-$HOME}/.zprezto/runcoms/zpreztorc" ]]; then
#     ln -s "${ZDOTDIR:-$HOME}/.zprezto/runcoms/zpreztorc" $HOME/.zpreztorc
# fi

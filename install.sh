#!/bin/bash
cd $(dirname $0)

for f in .??*
do
	[[ "$f" == ".git" ]] && continue
	[[ "$f" == ".DS_Store" ]] && continue
	[[ "$f" == ".gitignore" ]] && continue
	[[ "$f" == ".gitmodules" ]] && continue
	[[ "$f" == "install.sh" ]] && continue

	ln -Fis "$PWD/$f" $HOME
	echo "$f"
done

if [ ! -e $HOME/bin ]; then
    cp template/bin $HOME
fi

if [ ! -e $HOME/opt ]; then
    cp template/opt $HOME
fi

if [ ! -e $HOME/tools ]; then
    cp template/tools $HOME
fi

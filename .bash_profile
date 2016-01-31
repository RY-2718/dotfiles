if [ -f ~/.bashrc ]; then
	. ~/.bashrc
fi

export PATH
export CLICOLOR=1
eval "$(rbenv init -)"
export PATH="/usr/local/sbin:/Applications/Macvim.app/Contents/MacOS:$PATH"

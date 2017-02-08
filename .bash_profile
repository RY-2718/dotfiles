if [ -f ~/.bashrc ]; then
	. ~/.bashrc
fi

export PATH
export CLICOLOR=1
eval "$(rbenv init -)"

# Source local file.
if [[ -s "$HOME/.bash_profile.local" ]]; then
    source "$HOME/.bash_profile.local"
fi

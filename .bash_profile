if [ -f ~/.bashrc ]; then
	. ~/.bashrc
fi

export PATH
export CLICOLOR=1

# Source local file.
if [[ -s "$HOME/.bash_profile_local" ]]; then
    source "$HOME/.bash_profile_local"
fi

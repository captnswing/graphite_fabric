shopt -s histappend
export HISTSIZE=5000
export HISTCONTROL="erasedups"
export PROMPT_COMMAND="history -a"
export HISTIGNORE="l:ls -la:l[lhs]:h:..:...:cd:[bf]g:exit"
export PAGER=less
export LESS="-i -r -X"

export COLOR_NC='\e[0m'
export COLOR_GREEN='\e[0;32m'
export PS1="\[${COLOR_GREEN}\]\w > \[${COLOR_NC}\]"

test -r /etc/bash_completion && . /etc/bash_completion

function psa () {
	if [ $1 ]; then
		ps auxwwww | grep -v grep | grep -i $1
	else
		ps auxwwww
	fi
}

function h () {
	if [ $1 ]; then
		history | grep -i $1 | tail -250 | grep -i $1
	else
		history | tail -250
	fi
}

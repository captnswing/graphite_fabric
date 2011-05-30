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

export VIRTUALENVWRAPPER_PYTHON=@PYTHON@
test -r /usr/bin/virtualenvwrapper.sh && . /usr/bin/virtualenvwrapper.sh
test -r /usr/local/bin/virtualenvwrapper.sh && . /usr/local/bin/virtualenvwrapper.sh
export WORKON_HOME=/opt/virtualenvs
export PIP_REQUIRE_VIRTUALENV=true
export PIP_VIRTUALENV_BASE=$WORKON_HOME

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

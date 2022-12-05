#!/usr/bin/env bash

: '
Install the icav2 plugins into your home directory
'

set -euo pipefail

#########
# GLOCALS
#########

help_message="Usage: install.sh
Installs icav2-cli-plugins software and scripts into users home directory'.
You should have the following applications installed before continuing:

* aws
* curl
* jq
* python3
* rsync
* yq (version 4.18 or later)

MacOS users, please install greadlink through 'brew install coreutils'
"

ICAV2_CLI_PLUGINS_HOME="$HOME/.icav2-cli-plugins"

###########
# Functions
###########

get_realpath_binary(){
  if [[ "${OSTYPE}" == "darwin"* ]]; then
    echo "grealpath"
  else
    echo "realpath"
  fi
}

echo_stderr() {
  echo "$@" 1>&2
}

print_help() {
  echo_stderr "${help_message}"
}


check_readlink_program() {
  if [[ "${OSTYPE}" == "darwin"* ]]; then
    readlink_program="greadlink"
  else
    readlink_program="readlink"
  fi

  if ! type "${readlink_program}" 1>/dev/null; then
      if [[ "${readlink_program}" == "greadlink" ]]; then
        echo_stderr "On a mac but 'greadlink' not found"
        echo_stderr "Please run 'brew install coreutils' and then re-run this script"
        return 1
      else
        echo_stderr "readlink not installed. Please install before continuing"
      fi
  fi
}


binaries_check(){
  : '
  Check each of the required binaries are available
  '
  if ! (type aws curl jq python3 yq 1>/dev/null); then
    return 1
  fi
}

get_user_shell(){
  : '
  Quick one-liner to get user shell
  '
  # Quick "one liner" to get 'bash' or 'zsh'
  if [[ "${OSTYPE}" == "darwin"* ]]; then
    basename "$(finger "${USER}" | grep 'Shell:*' | cut -f3 -d ":")"
  else
    basename "$(awk -F: -v user="$USER" '$1 == user {print $NF}' /etc/passwd)"
  fi
}

get_this_path() {
  : '
  Mac users use greadlink over readlink
  Return the directory of where this install.sh file is located
  '
  local this_dir

  # darwin is for mac, else linux
  if [[ "${OSTYPE}" == "darwin"* ]]; then
    readlink_program="greadlink"
  else
    readlink_program="readlink"
  fi

  # Get directory name of the install.sh file
  this_dir="$(dirname "$("${readlink_program}" -f "${0}")")"

  # Return directory name
  echo "${this_dir}"
}



#########
# CHECKS
#########
if ! check_readlink_program; then
  echo_stderr "ERROR: Failed installation at readlink check stage"
  print_help
  exit 1
fi

if ! binaries_check; then
  echo_stderr "ERROR: Failed installation at the binaries check stage. Please check the requirements highlighted in usage."
  print_help
  exit 1
fi

# Steps get configuration / icav2 plugins home directory
# TODO - hardcode as $HOME/.icav2-cli-plugins/ for now

user_shell="$(get_user_shell)"

if [[ -z "${user_shell}" ]]; then
  echo_stderr "Couldn't get user shell, using '\$SHELL' env var '$SHELL'"
  user_shell="$(basename "${SHELL}")"
fi

# Check bash version
if [[ "${user_shell}" == "bash" ]]; then
  echo_stderr "Checking bash version"
  if [[ "$( "${SHELL}" -c "echo \"\${BASH_VERSION}\" 2>/dev/null" | cut -d'.' -f1)" -lt "4" ]]; then
    echo_stderr "Please upgrade to bash version 4 or higher, if you are running MacOS then please run the following commands"
    echo_stderr "brew install bash"
    echo_stderr "sudo bash -c \"echo \$(brew --prefix)/bin/bash >> /etc/shells\""
    echo_stderr "chsh -s \$(brew --prefix)/bin/bash"
    exit 1
  fi
fi


# Checking bash-completion is installed (for bash users only)
if [[ "${user_shell}" == "bash" ]]; then
  if ! ("${SHELL}" -lic "type _init_completion 1>/dev/null"); then
    echo_stderr "Could not find the command '_init_completion' which is necessary for auto-completion scripts"
    echo_stderr "If you are running on MacOS, please run the following command:"
    echo_stderr "brew install bash-completion@2 --HEAD"
    echo_stderr "Then add the following lines to ${HOME}/.bash_profile"
    echo_stderr "#######BASH COMPLETION######"
    echo_stderr "[[ -r \"\$(brew --prefix)/etc/profile.d/bash_completion.sh\" ]] && . \"\$(brew --prefix)/etc/profile.d/bash_completion.sh\""
    echo_stderr "############################"
    echo_stderr "If you are running on Linux:"
    echo_stderr "Please clone the following git repository \"https://github.com/scop/bash-completion\""
    echo_stderr "And following the installation commands. If you do not have sudo permissions"
    echo_stderr "Please set the --prefix option for the ./configure command to a local path"
    exit 1
  fi
fi

# Check bash version for macos users (even if they're not using bash as their shell)
if [[ "${OSTYPE}" == "darwin"* ]]; then
    echo_stderr "Checking env bash version"
    if [[ "$(bash -c "echo \${BASH_VERSION}" | cut -d'.' -f1)" -le "4" ]]; then
      echo_stderr "ERROR: Please install bash version 4 or higher (even if you're running zsh as your default shell)"
      echo_stderr "ERROR: Please run 'brew install bash'"
      exit 1
  fi
fi


#############
# CREATE DIRS
#############
mkdir -p "${ICAV2_CLI_PLUGINS_HOME}"


############################
# CREATE PYTHON3 VIRTUAL ENV
############################

if [[ -d "${ICAV2_CLI_PLUGINS_HOME}/pyenv" ]]; then
  if [[ ! -r "${ICAV2_CLI_PLUGINS_HOME}/pyenv/bin/python3" ]]; then
    echo_stderr "Error! Couldn't access pyenv path ${ICAV2_CLI_PLUGINS_HOME}/pyenv/bin/python3 but pyenv dir exists"
    exit 1
  fi
  echo_stderr "Updating pyenv"
else
  echo_stderr "Creating pyenv in $ICAV2_CLI_PLUGINS_HOME"
  python3 -m venv "${ICAV2_CLI_PLUGINS_HOME}/pyenv"
fi

cp "$(get_this_path)/src/plugins/requirements.txt" "${ICAV2_CLI_PLUGINS_HOME}/requirements.txt"
"${ICAV2_CLI_PLUGINS_HOME}/pyenv/bin/python3" -m pip install --upgrade pip --quiet
"${ICAV2_CLI_PLUGINS_HOME}/pyenv/bin/python3" -m pip install --requirement "${ICAV2_CLI_PLUGINS_HOME}/requirements.txt" --quiet

SITE_PACKAGES_DIR="$(
  find "${ICAV2_CLI_PLUGINS_HOME}/pyenv/lib/" \
    -mindepth 2 -maxdepth 2 \
    -name 'site-packages'
)"

##############
# COPY SCRIPTS
##############
mkdir -p "${ICAV2_CLI_PLUGINS_HOME}/plugins/"
rsync --delete --archive \
  "$(get_this_path)/src/plugins/bin/" "${ICAV2_CLI_PLUGINS_HOME}/plugins/bin/"
rsync --delete --archive \
  "$(get_this_path)/src/plugins/utils/" "${SITE_PACKAGES_DIR}/utils/"
rsync --delete --archive \
  "$(get_this_path)/src/plugins/subcommands/" "${SITE_PACKAGES_DIR}/subcommands/"
rsync --delete --archive \
  "$(get_this_path)/src/plugins/classes/" "${SITE_PACKAGES_DIR}/classes/"
rsync --delete --archive \
  "$(get_this_path)/shell_functions/" "${ICAV2_CLI_PLUGINS_HOME}/shell_functions/"



######################
# COPY AUTOCOMPLETIONS
######################
rsync --delete --archive \
  "$(get_this_path)/autocompletion/" "${ICAV2_CLI_PLUGINS_HOME}/autocompletion/"

#################
# PRINT USER HELP
#################
if [[ "${user_shell}" == "bash" ]]; then
  rc_profile="${HOME}/.bashrc"
elif [[ "${user_shell}" == "zsh" ]]; then
  rc_profile="${HOME}/.zshrc"
else
  rc_profile="${HOME}/.${user_shell}rc"
fi

echo_stderr "INSTALLATION COMPLETE!"
echo_stderr "To start using the plugins, add the following lines to ${rc_profile}"
echo_stderr "######ICAV2-CLI-PLUGINS######"
echo_stderr "export ICAV2_CLI_PLUGINS_HOME=\"\${HOME}/.icav2-cli-plugins/\""
echo_stderr "# Source functions"
echo_stderr "for file_name in \"\${ICAV2_CLI_PLUGINS_HOME}/shell_functions/\"*; do"
echo_stderr "    . \${file_name}; "
echo_stderr "done"

# Autocompletion differs between shells
echo_stderr "# Source autocompletions"
if [[ "${user_shell}" == "bash" ]]; then
  echo_stderr "for f in \"\$ICAV2_CLI_PLUGINS_HOME/autocompletion/${user_shell}/\"*\".bash\"; do"
  echo_stderr "    . \"\$f\""
  echo_stderr "done"
elif [[ "${user_shell}" == "zsh" ]]; then
  echo_stderr "fpath=(\"\$ICAV2_CLI_PLUGINS_HOME/autocompletion/${user_shell}/\" \$fpath)"
  if [[ "${OSTYPE}" == "darwin"* ]]; then
    # Mac Users need to run 'autoload' before running compinit
    echo_stderr "autoload -Uz compinit"
  fi
  echo_stderr "compinit"
fi

echo_stderr "########################"

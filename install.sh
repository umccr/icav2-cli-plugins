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
* gh
* yq (version 4.18 or later)

MacOS users, please install greadlink through 'brew install coreutils'

Options:
--install-pandoc:      Required for running the command icav2 projectpipelines create-cwl-from-zip
--no-autocompletion:   Only for installation into GitHub actions (where _init_completion is not present)
"

ICAV2_CLI_PLUGINS_HOME="$HOME/.icav2-cli-plugins"
PLUGIN_VERSION="__PLUGIN_VERSION__"
LIBICA_VERSION="__LIBICA_VERSION__"
YQ_VERSION="4.18.1"
CURL_VERSION="7.76.0"
PYTHON_VERSION="3.11"

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
  if ! (type aws curl jq python3 yq gh 1>/dev/null); then
    return 1
  fi
}

verlte() {
    [ "$1" = "$(echo -e "$1\n$2" | sort -V | head -n1)" ]
  }

verlt() {
    [ "$1" = "$2" ] && return 1 || verlte "$1" "$2"
}

get_yq_version(){
  # Input: yq (https://github.com/mikefarah/yq/) version 4.27.3
  # Output: 4.27.3
  yq --version 2>/dev/null | \
  tr ' ' '\n' | \
  grep --extended-regexp --only-matching '[0-9\.]+$' 
}

check_yq_version() {
  : '
  Make sure at the latest conda version
  '
  if ! verlte "${YQ_VERSION}" "$(get_yq_version)"; then
    echo_stderr "Your yq version is too old"
    return 1
  fi
}

get_curl_version(){
  # Input:
  #   curl 7.81.0 (x86_64-pc-linux-gnu) libcurl/7.81.0 OpenSSL/3.0.2 zlib/1.2.11 brotli/1.0.9 zstd/1.4.8 libidn2/2.3.2 libpsl/0.21.0 (+libidn2/2.3.2) libssh/0.9.6/openssl/zlib nghttp2/1.43.0 librtmp/2.3 OpenLDAP/2.5.16
  #   Release-Date: 2022-01-05
  #   Protocols: dict file ftp ftps gopher gophers http https imap imaps ldap ldaps mqtt pop3 pop3s rtmp rtsp scp sftp smb smbs smtp smtps telnet tftp
  #   Features: alt-svc AsynchDNS brotli GSS-API HSTS HTTP2 HTTPS-proxy IDN IPv6 Kerberos Largefile libz NTLM NTLM_WB PSL SPNEGO SSL TLS-SRP UnixSockets zstd
  # Output: 7.81.0
  curl --version 2>/dev/null | \
  head -n1 | \
  cut -d' ' -f2
}

check_curl_version() {
  : '
  Make sure at the latest conda version
  '
  if ! verlte "${CURL_VERSION}" "$(get_curl_version)"; then
    echo_stderr "Your curl version is too old"
  fi
}

set_python_binary_path(){
  pyenv_path="${ICAV2_CLI_PLUGINS_HOME}/pyenv/bin/python"

  if verlte "${PYTHON_VERSION}" "$(get_python_version "${pyenv_path}")"; then
    hash -p "${pyenv_path}" python3
  fi
}

get_python_version(){
  # Input: python3 --version
  # Python 3.10.12
  # Output: 3.10.12
  if [[ -n "${1-}" ]]; then
    python_path="$1"
  else
    python_path="python3"
  fi
  "${python_path}" --version 2>/dev/null | cut -d' ' -f2
}

check_python_version() {
  : '
  Make sure at the latest conda version
  '
  if ! verlte "${PYTHON_VERSION}" "$(get_python_version)"; then
    echo_stderr "Your python version is too old"
    echo_stderr "icav2 cli plugins requires python ${PYTHON_VERSION} or later"
    echo_stderr "You may wish to try"
    echo_stderr "conda create --name python${PYTHON_VERSION} python=${PYTHON_VERSION}"
    echo_stderr "conda activate python${PYTHON_VERSION}"
    echo_stderr "bash install.sh"
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

################
# ARGUMENTS
################
# Get args from command line
install_pandoc="false"
no_autocompletion="true"
while [ $# -gt 0 ]; do
  case "$1" in
    --install-pandoc)
      install_pandoc="true"
      ;;
    --no-autocompletion)
      no_autocompletion="true"
      ;;
    -h | --help)
      print_help
      exit 0
      ;;
  esac
  shift 1
done


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

if ! check_yq_version; then
  echo_stderr "Please update your version of yq and then rerun the installation"
  print_help
  exit 1
fi

if ! check_curl_version; then
  echo_stderr "Please update your version of curl to ${CURL_VERSION} or later and then rerun the installation"
  print_help
  exit 1
fi

set_python_binary_path

if ! check_python_version; then
  echo_stderr "Please update your version of python3 and then rerun the installation"
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
if [[ "${user_shell}" == "bash" && "${no_autocompletion}" == "false" ]]; then
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

"${ICAV2_CLI_PLUGINS_HOME}/pyenv/bin/python3" -m pip install --upgrade pip --quiet
"${ICAV2_CLI_PLUGINS_HOME}/pyenv/bin/python3" -m pip install "$(get_this_path)/." --quiet

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
  "$(get_this_path)/templates/" "${ICAV2_CLI_PLUGINS_HOME}/plugins/templates/"
rsync --delete --archive \
  "$(get_this_path)/shell_functions/" "${ICAV2_CLI_PLUGINS_HOME}/shell_functions/"


######################
# LINK PANDOC BINARY
######################
# Link pandoc binary from site-packages/pypandoc/files/pandoc to ${ICAV2_CLI_PLUGINS_HOME}/pyenv/bin
if [[ "${install_pandoc}" == "true" ]]; then
  echo_stderr "Installing pandoc requirements"
  "${ICAV2_CLI_PLUGINS_HOME}/pyenv/bin/python3" -m pip install "$(get_this_path)/.[pandoc]"
  if [[ -f "${SITE_PACKAGES_DIR}/pypandoc/files/pandoc" ]]; then
    ( \
      cd "${ICAV2_CLI_PLUGINS_HOME}/pyenv/bin/";
      ln -sf "${SITE_PACKAGES_DIR}/pypandoc/files/pandoc" "${ICAV2_CLI_PLUGINS_HOME}/pyenv/bin/pandoc"
    )
  fi
fi

################
# GET VERSIONS
################
if [[ "${PLUGIN_VERSION}" == "__PLUGIN_VERSION__" ]]; then
  echo "Installing from source" 1>&2
  latest_tag="$(git describe --abbrev=0 --tags)"
  latest_commit="$(git log --format="%H" -n 1 | cut -c1-7)"
  PLUGIN_VERSION="${latest_tag}--patch-${latest_commit}"
  echo "Setting plugin version as '${PLUGIN_VERSION}'"
fi
if [[ "${LIBICA_VERSION}" == "__LIBICA_VERSION__" ]]; then
  echo "Getting libica version from pyproject.toml" 1>&2
  LIBICA_VERSION="$( \
    "${ICAV2_CLI_PLUGINS_HOME}/pyenv/bin/python" -m pip show libica | \
    grep Version | \
    cut -d' ' -f2 \
  )"
  echo "Setting libica version as '${LIBICA_VERSION}'"
fi


#####################
# UPDATE VERSIONS
######################
# Update shell function
sed -i "s/__PLUGIN_VERSION__/${PLUGIN_VERSION}/" "${ICAV2_CLI_PLUGINS_HOME}/shell_functions/icav2.sh"
sed -i "s/__LIBICA_VERSION__/${LIBICA_VERSION}/" "${ICAV2_CLI_PLUGINS_HOME}/shell_functions/icav2.sh"

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
echo_stderr "export ICAV2_CLI_PLUGINS_HOME=\"\${HOME}/.icav2-cli-plugins\""
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

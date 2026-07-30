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
--skip-binary:         Skip downloading the icav2 binary (for environments where it's already available)
"

ICAV2_CLI_PLUGINS_HOME="$HOME/.icav2-cli-plugins"
PLUGIN_VERSION="__PLUGIN_VERSION__"
LIBICA_VERSION="__LIBICA_VERSION__"
JQ_VERSION="1.6"
YQ_VERSION="4.18.1"
CURL_VERSION="7.76.0"
PYTHON_VERSION="3.12"
ICAV2_CLI_VERSION="2.30.0"
ICAV2_CLI_DOWNLOAD_BASE_URL="https://stratus-documentation-us-east-1-public.s3.amazonaws.com/cli"

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

get_jq_version(){
  # Input jq-1.7
  # Output: 1.7
  jq --version | cut -d'-' -f2
}

check_jq_version(){
  if ! verlte "${JQ_VERSION}" "$(get_jq_version)"; then
    echo_stderr "Your jq version is too old"
    return 1
  fi
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

detect_platform(){
  : '
  Detect the operating system (linux or darwin)
  '
  local platform
  platform="$(uname -s | tr '[:upper:]' '[:lower:]')"
  case "${platform}" in
    linux|darwin)
      echo "${platform}"
      ;;
    *)
      echo_stderr "ERROR: Unsupported platform '${platform}'. Only linux and darwin are supported."
      return 1
      ;;
  esac
}

detect_architecture(){
  : '
  Detect the CPU architecture and map to amd64 or arm64
  '
  local arch
  arch="$(uname -m)"
  case "${arch}" in
    x86_64|amd64)
      echo "amd64"
      ;;
    aarch64|arm64)
      echo "arm64"
      ;;
    *)
      echo_stderr "ERROR: Unsupported architecture '${arch}'. Only x86_64/amd64 and aarch64/arm64 are supported."
      return 1
      ;;
  esac
}

download_icav2_binary(){
  : '
  Download the icav2 binary for the current platform and architecture.
  Aborts installation if download fails.
  '
  local platform="$1"
  local arch="$2"
  local version="${ICAV2_CLI_VERSION}"
  local download_url="${ICAV2_CLI_DOWNLOAD_BASE_URL}/${version}/${platform}/${arch}/icav2"
  local target_path="${ICAV2_CLI_PLUGINS_HOME}/bin/_icav2"

  echo_stderr "Downloading icav2 binary (version ${version}) for ${platform}/${arch}..."
  echo_stderr "URL: ${download_url}"

  if ! curl --fail --silent --location --output "${target_path}" "${download_url}"; then
    echo_stderr "ERROR: Failed to download icav2 binary from ${download_url}"
    echo_stderr "Please check your network connection and try again."
    rm -f "${target_path}"
    return 1
  fi

  # Verify the file was actually downloaded (non-empty)
  if [[ ! -s "${target_path}" ]]; then
    echo_stderr "ERROR: Downloaded icav2 binary is empty. Download may have failed."
    rm -f "${target_path}"
    return 1
  fi

  chmod 0755 "${target_path}"
  echo_stderr "icav2 binary installed at ${target_path}"
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
skip_binary="false"
while [ $# -gt 0 ]; do
  case "$1" in
    --install-pandoc)
      install_pandoc="true"
      ;;
    --no-autocompletion)
      no_autocompletion="true"
      ;;
    --skip-binary)
      skip_binary="true"
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

if ! check_jq_version; then
  echo_stderr "Please update your version of jq and then rerun the installation"
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
mkdir -p "${ICAV2_CLI_PLUGINS_HOME}/bin"
mkdir -p "${ICAV2_CLI_PLUGINS_HOME}/cache"


#############################
# DOWNLOAD ICAV2 BINARY
#############################
if [[ "${skip_binary}" == "false" ]]; then
  detected_platform="$(detect_platform)" || exit 1
  detected_arch="$(detect_architecture)" || exit 1

  if ! download_icav2_binary "${detected_platform}" "${detected_arch}"; then
    echo_stderr "ERROR: icav2 binary download failed. Aborting installation."
    exit 1
  fi
fi


#############################
# CREATE CONFIG FILE
#############################
if [[ ! -f "${ICAV2_CLI_PLUGINS_HOME}/config" ]]; then
  touch "${ICAV2_CLI_PLUGINS_HOME}/config"
  chmod 0600 "${ICAV2_CLI_PLUGINS_HOME}/config"
fi


#############################
# MIGRATION PROMPT
#############################
if [[ -d "${ICAV2_CLI_PLUGINS_HOME}/tenants" ]]; then
  if [ -t 0 ]; then
    echo_stderr ""
    echo_stderr "Existing tenant configurations detected in ${ICAV2_CLI_PLUGINS_HOME}/tenants/"
    read -r -p "Migrate to profile-based config? [y/N] " migrate_response
    if [[ "${migrate_response}" =~ ^[Yy]$ ]]; then
      echo_stderr ""
      echo_stderr "To migrate, run 'icav2 configure set <profile_name>' for each tenant."
      echo_stderr "Your existing tenant configurations remain in ${ICAV2_CLI_PLUGINS_HOME}/tenants/ until you remove them."
      echo_stderr ""
    else
      echo_stderr "Skipping migration. Existing tenants/ directory left unchanged."
    fi
  else
    echo_stderr "Non-interactive mode: skipping tenant migration prompt."
    echo_stderr "Existing tenants/ directory left unchanged."
  fi
fi


#############################
# TOUCH DEFAULT CONFIGURATION
#############################
if [[ ! -r "${HOME}/.icav2/config.yaml" ]]; then
  mkdir -p "${HOME}/.icav2/"
  touch "${HOME}/.icav2/config.yaml"
fi

if [[ -s "${HOME}/.icav2/config.yaml" ]]; then
  echo_stderr "'${HOME}/.icav2/config.yaml' is not empty, please delete this file before continuing"
  exit 1
fi

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
# Install dev version of wrapica from test pypi
"${ICAV2_CLI_PLUGINS_HOME}/pyenv/bin/python3" -m pip install \
  --extra-index-url https://test.pypi.org/simple \
  "$(get_this_path)/." --quiet

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
  echo_stderr "Installing from source"
  latest_tag="$(git describe --abbrev=0 --tags)"
  latest_commit="$(git log --format="%H" -n 1 | cut -c1-7)"
  PLUGIN_VERSION="${latest_tag}--patch-${latest_commit}"
  echo "Setting plugin version as '${PLUGIN_VERSION}'"
fi
if [[ "${LIBICA_VERSION}" == "__LIBICA_VERSION__" ]]; then
  echo_stderr "Getting libica version from pyproject.toml"
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
sed -i -e "s/__PLUGIN_VERSION__/${PLUGIN_VERSION}/" "${ICAV2_CLI_PLUGINS_HOME}/shell_functions/_icav2"
sed -i -e "s/__LIBICA_VERSION__/${LIBICA_VERSION}/" "${ICAV2_CLI_PLUGINS_HOME}/shell_functions/_icav2"

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

########################
# GENERATE SOURCE SCRIPT
########################
{
  echo "#!/usr/bin/env bash"
  echo ""
  echo "# ICAV2 CLI PLUGINS"
  echo "export ICAV2_CLI_PLUGINS_HOME=\"\${HOME}/.icav2-cli-plugins\""
  echo ""
  echo "# Add bin/ to PATH so _icav2 and icav2 wrapper are accessible"
  echo "export PATH=\"\${ICAV2_CLI_PLUGINS_HOME}/bin:\${PATH}\""
  echo ""
  echo "# Source shell functions if they exist (backward compatibility)"
  echo "if [[ -d \"\${ICAV2_CLI_PLUGINS_HOME}/shell_functions\" ]]; then"
  echo "  for __icav2_shell_function_file_name in \"\${ICAV2_CLI_PLUGINS_HOME}/shell_functions/\"*; do"
  echo "    if [[ -f \"\${__icav2_shell_function_file_name}\" ]]; then"
  echo "      . \"\${__icav2_shell_function_file_name}\""
  echo "    fi"
  echo "  done"
  echo "  unset __icav2_shell_function_file_name"
  echo "fi"

} > "${ICAV2_CLI_PLUGINS_HOME}/source.sh"


############################
# SHOW BASHRC LINE TO ADD
#############################
echo_stderr "Add the following line(s) to your ${rc_profile} file"
echo_stderr "############# ICAV2 CLI PLUGINS #############"
echo_stderr ". \"\${HOME}/.icav2-cli-plugins/source.sh\""
echo_stderr "#############################################"

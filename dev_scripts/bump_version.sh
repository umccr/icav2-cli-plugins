#!/usr/bin/env bash

set -euo pipefail

: '
Bump version of icav2-cli-plugins

Use parameters --dev or --prod

if using --prod parameter, we expect a version number,
for dev we expect the next iterable
'

# Add Globals for Github actions bot
GITHUB_ACTIONS_USERNAME="github-actions[bot]"
GITHUB_ACTIONS_EMAIL="41898282+github-actions[bot]@users.noreply.github.com"

REGEX="v[[:digit:]]+\.[[:digit:]]+\.[[:digit:]]+"
DATE_STR="$(date "+%Y%m%d%H%M%S")"
PROD_BRANCH="main"
PYPROJECT_TOML_NAME="pyproject.toml"
PYTHON_VERSION="3.12.0"

# Functions
print_help(){
  echo "
Usage: bump-version.sh 'v1.2.3' [ --dev | --prod ] [ --patch ]

Options:
  --dev:        Push a development tag
  --prod:       Push a production tag
  --patch:      This is a patch to a production tag

Description:
Updates pyproject.toml and creates an annotated git commit and then confirms with user before pushing commit to origin.

Also checks the version position arg is in the format v[0-9]+\.[0-9]+\.[0-9]+.

If --dev is specified, expects no existing production tag for semver, output tag is v1.2.3-dev-+%Y%m%d%H%M%S

Commit is done by GitHub Actions User however annotated tag is owned by executing user.

--dev does not have to be completed on a particular branch.

If --prod is specified user must be on updated main branch (git pull is done first),
A branch is then created and PR is made to main branch with annotated tag.

Because of the settings in the production environment, this will 'halt' a workflow and we wait for approval of workflow and PR
"
}

echo_stderr(){
  : '
  Write output to stderr
  '
  echo "${@}" 1>&2
}

verlte() {
    [ "$1" = "$(echo -e "$1\n$2" | sort -V | head -n1)" ]
  }

verlt() {
    [ "$1" = "$2" ] && return 1 || verlte "$1" "$2"
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

PYPROJECT_TOML_PATH="$(dirname "$(get_this_path)")/${PYPROJECT_TOML_NAME}"

## Checks
if ! git config --get user.name 1>/dev/null 2>&1; then
  echo_stderr "Please run git config user.name <username> and try again"
  print_help
fi

if ! git config --get user.email 1>/dev/null 2>&1; then
  echo_stderr "Please run git config user.email <user email> and try again"
  print_help
fi

set_python_binary_path

## Check toml
if ! check_python_version; then
  echo_stderr "Please update your version of python3 to at least ${PYTHON_VERSION} and then rerun the installation"
  print_help
  exit 1
fi

## Get args
version_number=""
is_dev="false"
is_prod="false"
is_patch="false"

while [ $# -gt 0 ]; do
  case "$1" in
    -h | --help)
      print_help
      exit 0
      ;;
    --dev)
      is_dev="true"
      ;;
    --prod)
      is_prod="true"
      ;;
    --patch)
      is_patch="true"
      ;;
    *)
      version_number="${1-}"
      ;;
  esac
  shift 1
done

## Check version regex
if ! grep --line-regexp --extended-regexp "${REGEX}" 1>/dev/null 2>&1 <<< "${version_number}"; then
  echo_stderr "Version parameter '${version_number}' did not match semver"
  print_help
  exit 1
fi

## Check one (and only one) of --dev and --prod were specified
if [[ "${is_prod}" == "true" && "${is_dev}" == "true" ]]; then
  echo_stderr "Please specify one and only one of --dev and --prod"
  print_help
  exit 1
elif [[ "${is_prod}" == "false" && "${is_dev}" == "false" ]]; then
  echo_stderr "Please specify one and only one of --dev and --prod"
  print_help
  exit 1
fi

## Check if patch, that prod is also selected
if [[ "${is_patch}" == "true" && ! "${is_prod}" == "true" ]]; then
  echo_stderr "Only use --patch when using --prod"
  print_help
fi

## Checks - make sure there is no existing semver tag for this arg
if [[ "${is_prod}" == "true" && "${is_patch}" == "false" ]]; then
  if ( \
    git tag --list 2>/dev/null | \
    grep --line-regexp "${version_number}" \
  ); then
    echo_stderr "Version ${version_number} already exists in production, are you trying to patch?"
    echo_stderr "If so please use --patch or otherwise specify a new version number"
    print_help
    exit 1
  fi
fi

## Get tag name
if [[ "${is_patch}" == "true" ]]; then
  tag="${version_number}.post${DATE_STR}"
elif [[ "${is_prod}" == "true" ]]; then
  tag="${version_number}"
elif [[ "${is_dev}" == "true" ]]; then
  tag="${version_number}.dev${DATE_STR}"
fi

## Get the current branch
current_branch="$(git branch --show-current)"

## Prod checks - make sure were on main branch and pulled from origin
if [[ "${is_prod}" == "true" ]]; then
  # Check we're on the right branch
  if [[ "${current_branch}" != "${PROD_BRANCH}" ]]; then
    echo_stderr "Please checkout ${PROD_BRANCH} branch before making a production version commit"
    exit 1
  fi

  # Pulling latest
  echo_stderr "Running a git pull from origin before making a tag"
  git pull origin "${PROD_BRANCH}"

  # Checkout a new branch (since we cant push to main without a PR)
  echo_stderr "Creating a new branch to merge into main"
  git checkout -b "bump/${tag}"

  # Set the current branch to the new branch
  current_branch="$(git branch --show-current)"
fi

## Update toml
echo_stderr "Updating pyproject.toml"
python3 - <<EOF

# Imports
import tomllib
import tomli_w
from pathlib import Path

# Load external variables
pyproject_toml_path = Path("${PYPROJECT_TOML_PATH}").absolute().resolve()
version_number = "${tag}".lstrip("v")

# Open toml file
with open(pyproject_toml_path, mode="rb") as toml_h:
    config = tomllib.load(toml_h)

# Edit toml file
config["project"]["version"] = version_number

# Write out toml file
with open(pyproject_toml_path, mode="wb") as toml_h:
    tomli_w.dump(config, toml_h)
EOF

## Commit edit toml - use GitHub Actions bot for commit author
echo_stderr "Committing pyproject.toml to git"
git add "${PYPROJECT_TOML_PATH}"
GIT_AUTHOR_NAME="${GITHUB_ACTIONS_USERNAME}" \
GIT_AUTHOR_EMAIL="${GITHUB_ACTIONS_EMAIL}" \
git commit -m "[bump-version.sh] Bumped version in toml to '${tag#v}'"

## Generate annotated tag - use standard user and email for this as we
## want to be able to trace who pushed the tag?
echo_stderr "Creating annotated tag"
git tag --annotate --message "Bumped version to '${tag}'" "${tag}"

## Push commit and tag
echo_stderr "Pushing branch and tag to GitHub"
git push origin "${current_branch}"
git push origin "${tag}"


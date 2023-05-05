#!/usr/bin/env bash

# This file is to be sourced
# The function below changes the ICAV2_ACCESS_TOKEN environment variable... maybe

_icav2__plugins__cli__tenants__enter(){
  : '
  Given a tenant name, collect the api key from ~/.icav2-plugins/tenants/<tenant_name>/config.yaml.
  Check if the --global parameter was set, in which case, just run icav2 config set
  '

  __icav2__get_base64_binary(){
    if [[ "${OSTYPE}" == "darwin"* ]]; then
      echo "gbase64"
    else
      echo "base64"
    fi
  }

  __icav2__get_sed_binary(){
    if [[ "${OSTYPE}" == "darwin"* ]]; then
      echo "gsed"
    else
      echo "sed"
    fi
  }

  __icav2__get_date_binary(){
    if [[ "${OSTYPE}" == "darwin"* ]]; then
      echo "gdate"
    else
      echo "date"
    fi
  }

  __icav2__tenants__enter_print_help() {
    echo "
Usage: icav2 tenants enter [tenant_name] [--global] [--help]
This command sets the project context for future commands by updating
the ICAV2_ACCESS_TOKEN env var.

If you wish to set this as the default tenant globally, please
use the --global parameter. This will recreate the config.yaml inside ~/.icav2/ directory by
running icav2 config set

Example:
  icav2 tenants enter umccr-beta

Parameters:
  -g, --global set tenant context globally
  -h, --help   help for enter
"
  }

  __icav2__create_token_from_api_key() {
    curl --fail --silent --location --show-error \
      --request 'POST' \
      --url "https://ica.illumina.com/ica/rest/api/tokens" \
      --header "Accept: application/vnd.illumina.v3+json" \
      --header "X-API-Key: $1" \
      -d '' |
    jq --raw-output \
      '.token'
  }

  __icav2__get_epoch_expiry() {
    local access_token="$1"
    echo "${access_token}" | \
      "$(__icav2__get_sed_binary)" -r 's/^(\S+)\.(\S+)\.(\S+)$/\2/' | \
      ( "$(__icav2__get_base64_binary)" --decode 2>/dev/null || true ) | \
    jq --raw-output \
      '.exp'
  }

  __icav2__get_seconds_to_expiry() {
    local expiry_epoch="$1"
    bc <<< "${expiry_epoch} - $("$(__icav2__get_date_binary)" +%s)"
  }

  __icav2__check_token_expiry() {
      # Inputs
      local access_token="$1"
      local SECONDS_PER_HOUR=3600

      # local vars
      local epoch_expiry
      local seconds_to_expiry

      # Get the JWT token expiry time
      epoch_expiry="$(__icav2__get_epoch_expiry "${access_token}")"

      # Compare expiry to current time
      seconds_to_expiry="$(__icav2__get_seconds_to_expiry "${epoch_expiry}")"

      # Check token expiry
      if [[ "${seconds_to_expiry}" -le 0 || "${seconds_to_expiry}" -le "${SECONDS_PER_HOUR}" ]]; then
        # Token has expired OR is about to expire
        return 1
      fi
  }

  # Initialise interal vars
  local global
  local tenant_name
  local x_api_key
  local access_token
  local project_id

  global="false"
  tenant_name=""
  x_api_key=""
  access_token=""
  server_url=""
  project_id=""

  # Get args from command line
  while [ $# -gt 0 ]; do
    case "$1" in
      -g | --global)
        global="true"
        ;;
      -h | --help)
        __icav2__tenants__enter_print_help
        return 0
        ;;
      *)
        # If name is already been set then we have the wrong command line entry
        if [[ -n "${tenant_name}" ]]; then
          echo "Got too many values for tenant. If your tenant name has spaces, please quote your inputs" 1>&2
          __icav2__tenants__enter_print_help 1>&2
          return 1
        fi
        tenant_name="$1"
      ;;
    esac
    shift 1
  done

  ## Check name was defined
  if [[ -z "${tenant_name}" ]]; then
    __icav2__tenants__enter_print_help 1>&2
    return 1
  fi

  # Check the ICAV2_CLI_PLUGINS_HOME env var has been set
  if [[ -z "${ICAV2_CLI_PLUGINS_HOME-}" ]]; then
    echo "Could not get the env var ICAV2_CLI_PLUGINS_HOME" 1>&2
    echo "Please ensure you have added the icav2 cli plugins source chunk to your rc file"
    return 1
  fi

  # Check the tenant directory for this tenant id
  if [[ ! -d "${ICAV2_CLI_PLUGINS_HOME}/tenants/${tenant_name}" ]]; then
    echo "Could not find the tenant '${tenant_name}'" 1>&2
    echo "Please run 'icav2 tenants list' to view the list of available tenants or alternatively run 'icav2 tenants init \"${tenant_name}\"' to initialise this tenant" 1>&2
    return 1
  fi

  # Check the config yaml exists
  if [[ ! -r "${ICAV2_CLI_PLUGINS_HOME}/tenants/${tenant_name}/config.yaml" ]]; then
    echo "Could not read '${ICAV2_CLI_PLUGINS_HOME}/tenants/${tenant_name}/config.yaml' please re-initialise this tenant with 'icav2 tenants init \"${tenant_name}\"'" 1>&2
    return 1
  fi

  # Read config
  x_api_key="$( \
    yq \
      --unwrapScalar \
      '.x-api-key' \
      < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${tenant_name}/config.yaml" \
  )"

  # Get the access token from .session.ica.yaml
  if [[ -r "${ICAV2_CLI_PLUGINS_HOME}/tenants/${tenant_name}/.session.ica.yaml" ]]; then
    if ! access_token="$( \
      yq '.access-token' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${tenant_name}/.session.ica.yaml"
    )"; then
      access_token=""
    else
      echo "Collected access_token token from tenant session yaml" 1>&2
    fi
  fi

  if [[ -z "${access_token}" || "${access_token}" == "null" ]] || ! __icav2__check_token_expiry "${access_token}"; then
    # Create token from API key
    # Check the api key
    if [[ -z "${x_api_key}" || "${x_api_key}" == "null" ]]; then
      echo "Could not get the api key from '${ICAV2_CLI_PLUGINS_HOME}/tenants/${tenant_name}/config.yaml'" 1>&2
      return 1
    fi

    # Create the token from the api key
    echo "Creating new access token from api-key in tenant config yaml" 1>&2
    if ! access_token="$( \
      __icav2__create_token_from_api_key "${x_api_key}"
    )"; then
      echo "Failed to create access token from api-key in '${ICAV2_CLI_PLUGINS_HOME}/tenants/${tenant_name}/config.yaml'" 1>&2
      return 1
    fi

    echo "Successfully created new access token" 1>&2
    if [[ -r "${ICAV2_CLI_PLUGINS_HOME}/tenants/${tenant_name}/.session.ica.yaml" ]]; then
      access_token="${access_token}" \
      yq --unwrapScalar \
        '.access-token=env(access_token)' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${tenant_name}/.session.ica.yaml" \
        > "${ICAV2_CLI_PLUGINS_HOME}/tenants/${tenant_name}/.session.ica.yaml.tmp"
        mv "${ICAV2_CLI_PLUGINS_HOME}/tenants/${tenant_name}/.session.ica.yaml.tmp" \
          "${ICAV2_CLI_PLUGINS_HOME}/tenants/${tenant_name}/.session.ica.yaml"
    else
      access_token="${access_token}" \
      yq --null-input --unwrapScalar \
        '.access-token=env(access_token)' > "${ICAV2_CLI_PLUGINS_HOME}/tenants/${tenant_name}/.session.ica.yaml.tmp"
      mv "${ICAV2_CLI_PLUGINS_HOME}/tenants/${tenant_name}/.session.ica.yaml.tmp" \
         "${ICAV2_CLI_PLUGINS_HOME}/tenants/${tenant_name}/.session.ica.yaml"
    fi
  fi

  # Export access token
  export ICAV2_ACCESS_TOKEN="${access_token}"

  # Check if global is specified
  if [[ "${global}" == "true" ]]; then
    echo "--global specified Setting '${tenant_name}' as tenant globally" 1>&2
    echo "${HOME}/.icav2/config.yaml will be updated with api key for tenant name" 1>&2
    "${ICAV2_CLI_PLUGINS_HOME}/pyenv/bin/python" "${ICAV2_CLI_PLUGINS_HOME}/plugins/bin/icav2-cli-plugins.py" \
      "tenants" "set-default-tenant" "${tenant_name}"
  fi

  # Get project id from tenant session yaml
  project_id="$( \
    yq --unwrapScalar '.project-id' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${tenant_name}/.session.ica.yaml"
  )"
  server_url="$( \
    yq --unwrapScalar '.server-url' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${tenant_name}/config.yaml"
  )"
  export ICAV2_BASE_URL="https://${server_url-ica.illumina.com}/ica/rest"

  # Check project id
  if [[ -n "${ICAV2_PROJECT_ID-}" ]]; then
    echo "ICAV2_PROJECT_ID is set, checking if project id is in tenant '${tenant_name}'" 1>&2
    if ! \
      curl --fail --location --silent \
        --request "GET" \
        --header 'Accept: application/vnd.illumina.v3+json' \
        --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}" \
        --url "${ICAV2_BASE_URL}/api/projects/${ICAV2_PROJECT_ID}" 1>/dev/null 2>&1; then
      echo "Project ID '${ICAV2_PROJECT_ID}' is not in tenant '${tenant_name}'" 1>&2
      if [[ -z "${project_id}" || "${project_id}" == "null" ]]; then
        echo "No project id set in session yaml" 1>&2
        echo "Unsetting ICAV2_PROJECT_ID env var" 1>&2
        unset ICAV2_PROJECT_ID
      else
        echo "Project ID found in session yaml" 1>&2
        echo "Setting ICAV2_PROJECT_ID env var to '${project_id}'" 1>&2
        export ICAV2_PROJECT_ID="${project_id}"
      fi
    else
      echo "Confirmed current project is in tenant '${tenant_name}'" 1>&2
    fi
  else
    if [[ -z "${project_id}" || "${project_id}" == "null" ]]; then
        echo "No project id set in session yaml for tenant '${tenant_name}' so not in a project" 1>&2
        echo "Please run 'icav2 projects enter <project-name>' to enter a project" 1>&2
    else
        echo "Project ID found in session yaml for tenant '${tenant_name}'" 1>&2
        echo "Setting ICAV2_PROJECT_ID env var to '${project_id}'" 1>&2
        export ICAV2_PROJECT_ID="${project_id}"
    fi
  fi
  # Done
}
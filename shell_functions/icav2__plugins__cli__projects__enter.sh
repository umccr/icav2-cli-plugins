#!/usr/bin/env bash

# This file is to be sourced
# The function below changes the ICAV2_PROJECT_ID environment variable... maybe

_icav2__plugins__cli__projects__enter(){
  : '
  Given a project name, collect the project id.
  Check if the --global parameter was set, in which case, update the ~/.icav2/.session.ica.yaml
  Were also screwed if we want to source something since this function sources so yeah...
  '

  __icav2__projects__enter_print_help() {
    echo "
Usage: icav2 projects enter [projectname] [--global] [--help]
This command sets the project context for future commands by updating
the ICAV2_PROJECT_ID env var.  If you wish to set the project id globally, please
use the --global parameter

Example:
  icav2 projects enter playground_v2

Parameters:
  -g, --global set project id globally
  -h, --help   help for enter
"
  }

  # Initialise interal vars
  local global
  local name

  global="false"
  name=""

  # Get args from command line
  while [ $# -gt 0 ]; do
    case "$1" in
      -g | --global)
        global="true"
        ;;
      -h | --help)
        __icav2__projects__enter_print_help
        return 0
        ;;
      *)
        # If name is already been set then we have the wrong command line entry
        if [[ -n "${name}" ]]; then
          echo "Got too many values for project. If your project name has spaces, please quote your inputs" 1>&2
          __icav2__projects__enter_print_help 1>&2
          return 1
        fi
        name="$1"
      ;;
    esac
    shift 1
  done

  ## Check name was defined
  if [[ -z "${name}" ]]; then
    __icav2__projects__enter_print_help 1>&2
    return 1
  fi

  # Get project id from project name
  project_id="$( \
    command icav2 projects list --output-format json | \
    jq --raw-output \
      --arg name "$name" \
      '
        .items |
        map(
          select(
            .name == $name
          )
          | .id
        ) |
        .[]
      ' \
  )"

  # Check project id
  if [[ -z "${project_id}" ]]; then
    echo "Could not get project id from project name '${name}'" 1>&2
    return 1
  fi

  # Check if global set to true
  if [[ "${global}" == "true" ]]; then
    command icav2 projects enter "${name}"
    echo "Updated project-id attribute in ~/.icav2/.session.ica.yaml" 1>&2
    if [[ -n "${ICAV2_PROJECT_ID-}" && "${ICAV2_PROJECT_ID}" != "${project_id}" ]]; then
      echo "Env var 'ICAV2_PROJECT_ID' is different" 1>&2
      echo "Also updating ICAV2_PROJECT_ID env var from '${ICAV2_PROJECT_ID}' to '${project_id}'" 1>&2
      export ICAV2_PROJECT_ID="${project_id}"
    fi
  else
    export ICAV2_PROJECT_ID="${project_id}"
    echo "ICAV2_PROJECT_ID env var now set to '${ICAV2_PROJECT_ID}"
  fi

  # Done
}
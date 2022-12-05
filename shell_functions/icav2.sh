#!/usr/bin/env bash

# Attempt 2
icav2() {
  : '
  Check
  '

  local plugin_subcommands_array
  local plugin_subfunctions_array

  plugin_subfunctions_array=( \
    "projects__enter"
  )

  plugin_subcommands_array=( \
    "projectdata__ls" \
    "projectdata__view" \
    "projectdata__s3-sync-download" \
    "projectdata__s3-sync-upload" \
    "projectdata__help" \
    "projectdata__-h" \
    "projectdata__--h" \
    "projectanalyses__list-analysis-steps" \
    "projectanalyses__get-cwl-analysis-input-json" \
    "projectanalyses__get-cwl-analysis-output-json" \
    "projectanalyses__get-analysis-step-logs" \
    "projectanalyses__help" \
    "projectanalyses__-h" \
    "projectanalyses__--h" \
    "projectpipelines__create-cwl-workflow-from-zip" \
    "projectpipelines__create-cwl-wes-input-template" \
    "projectpipelines__start-cwl-wes" \
    "projectpipelines__help"
    "projectpipelines__-h" \
    "projectpipelines__--h" \
  )

  # Check env var is set
  if [[ -z "${ICAV2_CLI_PLUGINS_HOME-}" ]]; then
    echo "Could not find env var 'ICAV2_CLI_PLUGINS_HOME'." 1>&2
    echo "Please ensure all these values are set first" 1>&2
    return 1
  fi

  # If blank or not matching, we just run the OG.
  if [[ -z "${1-}" || -z ${2-} ]]; then
    # FIXME - show plugin help over command help
    eval command icav2 '"${@}"'
  # Run the shell function
  elif [[ " ${plugin_subfunctions_array[*]} " =~ ${1}__${2} ]]; then
    eval "_icav2__plugins__cli__${1}__${2}" '"${@:3}"'
  # Run the wrapped python command
  elif [[ " ${plugin_subcommands_array[*]} " =~ ${1}__${2} ]]; then
    eval "${ICAV2_CLI_PLUGINS_HOME}/pyenv/bin/python3" "${ICAV2_CLI_PLUGINS_HOME}/plugins/bin/icav2-cli-plugins.py" "${1}" "${2}" '"${@:3}"'
  else
    eval command icav2 '"${@}"'
  fi
}


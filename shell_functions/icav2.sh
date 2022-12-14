#!/usr/bin/env bash

# Attempt 2
icav2() {
  : '
  Check
  '

  local plugin_subcommands_array
  local plugin_subfunctions_array
  local plugin_version="__PLUGIN_VERSION__"
  local top
  local bottom

  plugin_subfunctions_array=( \
    "projects__enter"
  )

  plugin_subcommands_top_only_array=( \
    "projectdata" \
    "projectanalyses" \
    "projectpipelines" \
  )

  plugin_subcommands_array=( \
    "projectdata__ls" \
    "projectdata__view" \
    "projectdata__s3-sync-download" \
    "projectdata__s3-sync-upload" \
    "projectdata__help" \
    "projectdata__-h" \
    "projectdata__--help" \
    "projectanalyses__list-analysis-steps" \
    "projectanalyses__get-cwl-analysis-input-json" \
    "projectanalyses__get-cwl-analysis-output-json" \
    "projectanalyses__get-analysis-step-logs" \
    "projectanalyses__help" \
    "projectanalyses__-h" \
    "projectanalyses__--help" \
    "projectpipelines__create-cwl-workflow-from-zip" \
    "projectpipelines__create-cwl-workflow-from-github-release" \
    "projectpipelines__create-cwl-wes-input-template" \
    "projectpipelines__start-cwl-wes" \
    "projectpipelines__help"
    "projectpipelines__-h" \
    "projectpipelines__--help" \
  )

  # Check env var is set
  if [[ -z "${ICAV2_CLI_PLUGINS_HOME-}" ]]; then
    echo "Could not find env var 'ICAV2_CLI_PLUGINS_HOME'." 1>&2
    echo "Please ensure all these values are set first" 1>&2
    return 1
  fi

  # Get first two args if they exist
  top="${1-}"
  bottom="${2-}"

  # If both blank or not matching, we just run the OG.
  if [[ -z "${top}" && -z "${bottom}" ]]; then
    eval command icav2 '"${@}"'
  # Otherwise if the first is matching top array and the bottom is empty, extend command with 'help'
  elif [[ -n "${top}" && -z "${bottom}" && " ${plugin_subcommands_top_only_array[*]} " =~ "${top}" ]]; then
        # Just the first subcommand, like icav2 projectdata help
        # Extend arg to include help
        bottom="help"
  # Or print version
  elif [[ "${top}" == "version" || "${top}" == "--version" || "${top}" == "-v" ]]; then
    echo "icav2-cli-plugins-version: ${plugin_version}"
    command icav2 --version
    return 0
  fi

  # Now if still one is empty print command
  if [[ -z "${top}" || -z "${bottom}" ]]; then
    eval command icav2 '"${@}"'
  # Run the shell function
  elif [[ " ${plugin_subfunctions_array[*]} " =~ ${top}__${bottom} ]]; then
    eval "_icav2__plugins__cli__${top}__${bottom}" '"${@:3}"'
  # Run the wrapped python command
  elif [[ " ${plugin_subcommands_array[*]} " =~ ${top}__${bottom} ]]; then
    eval "${ICAV2_CLI_PLUGINS_HOME}/pyenv/bin/python3" "${ICAV2_CLI_PLUGINS_HOME}/plugins/bin/icav2-cli-plugins.py" "${top}" "${bottom}" '"${@:3}"'
  else
    eval command icav2 '"${@}"'
  fi
}


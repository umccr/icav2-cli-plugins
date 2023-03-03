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
    "projectdata__ls_" \
    "projectdata__view_" \
    "projectdata__s3-sync-download_" \
    "projectdata__s3-sync-upload_" \
    "projectdata__create-download-script_"
    "projectdata__help_" \
    "projectdata__-h_" \
    "projectdata__--help_" \
    "projectanalyses__list-analysis-steps_" \
    "projectanalyses__get-cwl-analysis-input-json_" \
    "projectanalyses__get-cwl-analysis-output-json_" \
    "projectanalyses__get-analysis-step-logs_" \
    "projectanalyses__help_" \
    "projectanalyses__-h_" \
    "projectanalyses__--help_" \
    "projectpipelines__create-cwl-workflow-from-zip_" \
    "projectpipelines__create-cwl-workflow-from-github-release_" \
    "projectpipelines__create-cwl-wes-input-template_" \
    "projectpipelines__start-cwl-wes_" \
    "projectpipelines__help_"
    "projectpipelines__-h_" \
    "projectpipelines__--help_" \
  )

  # Check env var is set
  if [[ -z "${ICAV2_CLI_PLUGINS_HOME-}" ]]; then
    echo "Could not find env var 'ICAV2_CLI_PLUGINS_HOME'." 1>&2
    echo "Please ensure all these values are set first" 1>&2
    return 1
  fi

  # Get first two args if they exist
  top="${1-}"
  bottom="${2-}_"

  # If both blank or not matching, we just run the OG.
  if [[ -z "${top}" && -z "${bottom_}" ]]; then
    eval command icav2 '"${@}"'
  # Otherwise if the first is matching top array and the bottom is empty, extend command with 'help'
  elif [[ -n "${top}" && -z "${bottom%_}" && " ${plugin_subcommands_top_only_array[*]} " =~ ${top} ]]; then
        # Just the first subcommand, like icav2 projectdata help
        # Extend arg to include help
        bottom="help"
  # Or print version
  elif [[ "${top}" == "version" || "${top}" == "--version" || "${top}" == "-v" ]]; then
    echo "icav2-cli-plugins-version: ${plugin_version}"
    echo "libica module version: ${libica_version}"
    command icav2 --version
    return 0
  fi

  # Now if still one is empty print command
  if [[ -z "${top}" || -z "${bottom%_}" ]]; then
    eval command icav2 '"${@}"'
  # Run the shell function
  elif [[ " ${plugin_subfunctions_array[*]} " =~ ${top}__${bottom} ]]; then
    eval "_icav2__plugins__cli__${top}__${bottom%_}" '"${@:3}"'
  # Run the wrapped python command
  elif [[ " ${plugin_subcommands_array[*]} " =~ ${top}__${bottom} ]]; then
    eval PATH="'${ICAV2_CLI_PLUGINS_HOME}/pyenv/bin/:$PATH'" "${ICAV2_CLI_PLUGINS_HOME}/pyenv/bin/python3" "${ICAV2_CLI_PLUGINS_HOME}/plugins/bin/icav2-cli-plugins.py" "${top}" "${bottom%_}" '"${@:3}"'
  else
    eval command icav2 '"${@}"'
  fi
}


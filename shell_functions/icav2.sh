#!/usr/bin/env bash

# Attempt 2
icav2() {
  : '
  Check
  '

  local plugin_subcommands_array
  local plugin_subfunctions_array
  local plugin_version="__PLUGIN_VERSION__"
  local libica_version="__LIBICA_VERSION__"
  local top
  local bottom

  plugin_subfunctions_array=( \
    "_projects__enter_"
    "_tenants__enter_"
  )

  # subcommands that are entirely plugins
  plugin_only_subcommands_top_only_array=( \
    "_bundles"
  )

  # Contain both plugins and non plugin subcommands
  plugin_subcommands_top_only_array=( \
    "_bundles" \
    "_pipelines" \
    "_projectdata" \
    "_projectanalyses" \
    "_projectpipelines" \
    "_tenants" \
  )

  # List of plugin commands
  plugin_subcommands_array=( \
    "_bundles__init_" \
    "_bundles__get_"
    "_bundles__release_" \
    "_bundles__list_" \
    "_bundles__add-data_" \
    "_bundles__add-pipeline_" \
    "_bundles__add-bundle-to-project_" \
    "_bundles__help_" \
    "_bundles__-h_" \
    "_bundles__--help_" \
    "_projectdata__ls_" \
    "_projectdata__view_" \
    "_projectdata__find_" \
    "_projectdata__s3-sync-download_" \
    "_projectdata__s3-sync-upload_" \
    "_projectdata__create-download-script_"
    "_projectdata__help_" \
    "_projectdata__-h_" \
    "_projectdata__--help_" \
    "_projectanalyses__list-analysis-steps_" \
    "_projectanalyses__get-cwl-analysis-input-json_" \
    "_projectanalyses__get-cwl-analysis-output-json_" \
    "_projectanalyses__get-analysis-step-logs_" \
    "_projectanalyses__gantt-plot_" \
    "_projectanalyses__help_" \
    "_projectanalyses__-h_" \
    "_projectanalyses__--help_" \
    "_pipelines__check-ownership_" \
    "_pipelines__list-projects_" \
    "_pipelines__help_" \
    "_pipelines__-h_" \
    "_pipelines__--help_" \
    "_projectpipelines__create-cwl-workflow-from-zip_" \
    "_projectpipelines__create-cwl-workflow-from-github-release_" \
    "_projectpipelines__create-cwl-wes-input-template_" \
    "_projectpipelines__start-cwl-wes_" \
    "_projectpipelines__update_" \
    "_projectpipelines__release_" \
    "_projectpipelines__help_"
    "_projectpipelines__-h_" \
    "_projectpipelines__--help_" \
    "_tenants__help_" \
    "_tenants__-h_" \
    "_tenants__--help_" \
    "_tenants__init_" \
    "_tenants__list_" \
    "_tenants__set-default-project_" \
    "_tenants__set-default-tenant_" \
  )

  # Check env var is set
  if [[ -z "${ICAV2_CLI_PLUGINS_HOME-}" ]]; then
    echo "Could not find env var 'ICAV2_CLI_PLUGINS_HOME'." 1>&2
    echo "Please ensure all these values are set first" 1>&2
    return 1
  fi

  # Get first two args if they exist
  top="_${1-}"
  bottom="${2-}_"

  # If both blank or not matching, we just run the OG.
  if [[ -z "${top#_}" && -z "${bottom_}" ]]; then
    eval command icav2 '"${@}"'
  # Otherwise if the first is matching top array and the bottom is empty, extend command with 'help'
  elif [[ -n "${top#_}" && -z "${bottom%_}" && " ${plugin_subcommands_top_only_array[*]} " =~ ${top} ]]; then
    # Just the first subcommand, like icav2 projectdata help
    # Extend arg to include help
    bottom="help"
  # Or print version
  elif [[ "${top#_}" == "version" || "${top#_}" == "--version" || "${top#_}" == "-v" ]]; then
    echo "icav2-cli-plugins-version: ${plugin_version}"
    echo "libica module version: ${libica_version}"
    command icav2 --version
    return 0
  fi

  # Now if still one is empty print command
  if [[ -z "${top#_}" || -z "${bottom%_}" ]]; then
    eval command icav2 '"${@}"'
  # Run the shell function
  elif [[ " ${plugin_subfunctions_array[*]} " =~ ${top}__${bottom} ]]; then
    eval "_icav2__plugins__cli__${top#_}__${bottom%_}" '"${@:3}"'
  # Run the wrapped python command
  elif [[ " ${plugin_subcommands_array[*]} " =~ ${top}__${bottom} ]]; then
    eval PATH="'${ICAV2_CLI_PLUGINS_HOME}/pyenv/bin/:$PATH'" "${ICAV2_CLI_PLUGINS_HOME}/pyenv/bin/python3" "${ICAV2_CLI_PLUGINS_HOME}/pyenv/bin/icav2-cli-plugins.py" "${top#_}" "${bottom%_}" '"${@:3}"'
  # Dont eval if in a plugin_only subcommand
  elif [[ "${plugin_only_subcommands_top_only_array[*]} " =~ ${top} ]]; then
    echo "Unknown subcommand for icav2 ${top#_}"
    eval PATH="'${ICAV2_CLI_PLUGINS_HOME}/pyenv/bin/:$PATH'" "${ICAV2_CLI_PLUGINS_HOME}/pyenv/bin/python3" "${ICAV2_CLI_PLUGINS_HOME}/pyenv/bin/icav2-cli-plugins.py" "${top#_}" "help"
  else
    eval command icav2 '"${@}"'
  fi
}


#!/usr/bin/env bash

# Generated with perl module App::Spec v0.000

_icav2() {

    COMPREPLY=()
    local program=icav2
    local cur prev words cword
    _init_completion -n : || return
    declare -a FLAGS
    declare -a OPTIONS
    declare -a MYWORDS

    local INDEX=`expr $cword - 1`
    MYWORDS=("${words[@]:1:$cword}")

    FLAGS=('--help' 'Show command help' '-h' 'Show command help')
    OPTIONS=()
    __icav2_handle_options_flags

    case $INDEX in

    0)
        __comp_current_options || return
        __icav2_dynamic_comp 'commands' 'analysisstorages'$'\t''Analysis storages commands'$'\n''config'$'\t''Config actions'$'\n''dataformats'$'\t''Data format commands'$'\n''help'$'\t''Help about any command'$'\n''metadatamodels'$'\t''Metadata model commands'$'\n''pipelines'$'\t''Pipeline commands'$'\n''projectanalyses'$'\t''Project analyses commands'$'\n''projectdata'$'\t''Project Data commands'$'\n''projectpipelines'$'\t''Project pipeline commands'$'\n''projects'$'\t''Project commands'$'\n''projectsamples'$'\t''Project samples commands'$'\n''regions'$'\t''Region commands'$'\n''storagebundles'$'\t''Storage bundle commands'$'\n''storageconfigurations'$'\t''Storage configurations commands'$'\n''tokens'$'\t''Tokens commands'$'\n''version'$'\t''The version of this application'

    ;;
    *)
    # subcmds
    case ${MYWORDS[0]} in
      _meta)
        __icav2_handle_options_flags
        case $INDEX in

        1)
            __comp_current_options || return
            __icav2_dynamic_comp 'commands' 'completion'$'\t''Shell completion functions'$'\n''pod'$'\t''Pod documentation'

        ;;
        *)
        # subcmds
        case ${MYWORDS[1]} in
          completion)
            __icav2_handle_options_flags
            case $INDEX in

            2)
                __comp_current_options || return
                __icav2_dynamic_comp 'commands' 'generate'$'\t''Generate self completion'

            ;;
            *)
            # subcmds
            case ${MYWORDS[2]} in
              generate)
                FLAGS+=('--zsh' 'for zsh' '--bash' 'for bash')
                OPTIONS+=('--name' 'name of the program (optional, override name in spec)')
                __icav2_handle_options_flags
                case ${MYWORDS[$INDEX-1]} in
                  --name)
                  ;;

                esac
                case $INDEX in

                *)
                    __comp_current_options || return
                ;;
                esac
              ;;
            esac

            ;;
            esac
          ;;
          pod)
            __icav2_handle_options_flags
            case $INDEX in

            2)
                __comp_current_options || return
                __icav2_dynamic_comp 'commands' 'generate'$'\t''Generate self pod'

            ;;
            *)
            # subcmds
            case ${MYWORDS[2]} in
              generate)
                __icav2_handle_options_flags
                __comp_current_options true || return # no subcmds, no params/opts
              ;;
            esac

            ;;
            esac
          ;;
        esac

        ;;
        esac
      ;;
      analysisstorages)
        __icav2_handle_options_flags
        case $INDEX in

        1)
            __comp_current_options || return
            __icav2_dynamic_comp 'commands' 'list'$'\t''list of storage id'"'"'s'

        ;;
        *)
        # subcmds
        case ${MYWORDS[1]} in
          list)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
        esac

        ;;
        esac
      ;;
      config)
        __icav2_handle_options_flags
        case $INDEX in

        1)
            __comp_current_options || return
            __icav2_dynamic_comp 'commands' 'get'$'\t''Get configuration information'$'\n''reset'$'\t''Remove the configuration information'$'\n''set'$'\t''Set configuration information'

        ;;
        *)
        # subcmds
        case ${MYWORDS[1]} in
          get)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          reset)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          set)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
        esac

        ;;
        esac
      ;;
      dataformats)
        __icav2_handle_options_flags
        case $INDEX in

        1)
            __comp_current_options || return
            __icav2_dynamic_comp 'commands' 'list'$'\t''List data formats'

        ;;
        *)
        # subcmds
        case ${MYWORDS[1]} in
          list)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
        esac

        ;;
        esac
      ;;
      help)
        __icav2_handle_options_flags
        __comp_current_options true || return # no subcmds, no params/opts
      ;;
      metadatamodels)
        __icav2_handle_options_flags
        case $INDEX in

        1)
            __comp_current_options || return
            __icav2_dynamic_comp 'commands' 'list'$'\t''list of metadata models'

        ;;
        *)
        # subcmds
        case ${MYWORDS[1]} in
          list)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
        esac

        ;;
        esac
      ;;
      pipelines)
        __icav2_handle_options_flags
        case $INDEX in

        1)
            __comp_current_options || return
            __icav2_dynamic_comp 'commands' 'get'$'\t''Get details of a pipeline'$'\n''list'$'\t''List pipelines'

        ;;
        *)
        # subcmds
        case ${MYWORDS[1]} in
          get)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          list)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
        esac

        ;;
        esac
      ;;
      projectanalyses)
        __icav2_handle_options_flags
        case $INDEX in

        1)
            __comp_current_options || return
            __icav2_dynamic_comp 'commands' 'gantt-plot'$'\t''Create a gantt chart for an analysis'$'\n''get'$'\t''Get the details of an analysis'$'\n''get-analysis-step-logs'$'\t''List analysis step logs'$'\n''get-cwl-analysis-input-json'$'\t''List cwl analysis input json'$'\n''get-cwl-analysis-output-json'$'\t''List cwl analysis output json'$'\n''input'$'\t''Retrieve input of analyses commands'$'\n''list'$'\t''List of analyses for a project'$'\n''list-analysis-steps'$'\t''List analysis steps'$'\n''output'$'\t''Retrieve output of analyses commands'$'\n''update'$'\t''Update tags of analyses'

        ;;
        *)
        # subcmds
        case ${MYWORDS[1]} in
          gantt-plot)
            OPTIONS+=('--output-path' 'Write output to file')
            __icav2_handle_options_flags
            case ${MYWORDS[$INDEX-1]} in
              --output-path)
                compopt -o filenames
                return
              ;;

            esac
            case $INDEX in
              2)
                  __comp_current_options || return
                    _icav2_projectanalyses_gantt-plot_param_analysis_id_completion
              ;;


            *)
                __comp_current_options || return
            ;;
            esac
          ;;
          get)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          get-analysis-step-logs)
            OPTIONS+=('--step-name' 'step name' '--stdout' 'get stdout of a step' '--stderr' 'get stderr of a step' '--output-path' 'Write output to file')
            __icav2_handle_options_flags
            case ${MYWORDS[$INDEX-1]} in
              --step-name)
              ;;
              --stdout)
              ;;
              --stderr)
              ;;
              --output-path)
                compopt -o filenames
                return
              ;;

            esac
            case $INDEX in
              2)
                  __comp_current_options || return
                    _icav2_projectanalyses_get-analysis-step-logs_param_analysis_id_completion
              ;;


            *)
                __comp_current_options || return
            ;;
            esac
          ;;
          get-cwl-analysis-input-json)
            __icav2_handle_options_flags
            case ${MYWORDS[$INDEX-1]} in

            esac
            case $INDEX in
              2)
                  __comp_current_options || return
                    _icav2_projectanalyses_get-cwl-analysis-input-json_param_analysis_id_completion
              ;;


            *)
                __comp_current_options || return
            ;;
            esac
          ;;
          get-cwl-analysis-output-json)
            __icav2_handle_options_flags
            case ${MYWORDS[$INDEX-1]} in

            esac
            case $INDEX in
              2)
                  __comp_current_options || return
                    _icav2_projectanalyses_get-cwl-analysis-output-json_param_analysis_id_completion
              ;;


            *)
                __comp_current_options || return
            ;;
            esac
          ;;
          input)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          list)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          list-analysis-steps)
            OPTIONS+=('--show-technical-steps' 'Also list technical steps')
            __icav2_handle_options_flags
            case ${MYWORDS[$INDEX-1]} in
              --show-technical-steps)
              ;;

            esac
            case $INDEX in
              2)
                  __comp_current_options || return
                    _icav2_projectanalyses_list-analysis-steps_param_analysis_id_completion
              ;;


            *)
                __comp_current_options || return
            ;;
            esac
          ;;
          output)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          update)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
        esac

        ;;
        esac
      ;;
      projectdata)
        __icav2_handle_options_flags
        case $INDEX in

        1)
            __comp_current_options || return
            __icav2_dynamic_comp 'commands' 'archive'$'\t''archive data'$'\n''create'$'\t''Create data id for a project'$'\n''create-download-script'$'\t''Create download script'$'\n''delete'$'\t''delete data'$'\n''download'$'\t''Download a file/folder'$'\n''downloadurl'$'\t''get download url'$'\n''find'$'\t''Find files and directories in icav2 directory'$'\n''folderuploadsession'$'\t''Get details of a folder upload'$'\n''get'$'\t''Get details of a data'$'\n''link'$'\t''Link data to a project'$'\n''list'$'\t''List data'$'\n''ls'$'\t''List data in directory, similar to ls in a posix file system'$'\n''mount'$'\t''Mount project data'$'\n''s3-sync-download'$'\t''Upload a folder to icav2 using aws s3 sync.'$'\n''s3-sync-upload'$'\t''Upload a folder to icav2 using aws s3 sync.'$'\n''temporarycredentials'$'\t''fetch temporal credentials for data'$'\n''unarchive'$'\t''unarchive data'$'\n''unlink'$'\t''Unlink data to a project'$'\n''unmount'$'\t''Unmount project data'$'\n''update'$'\t''Updates the details of a data'$'\n''upload'$'\t''Upload a file/folder'$'\n''view'$'\t''View a file to stdout'

        ;;
        *)
        # subcmds
        case ${MYWORDS[1]} in
          archive)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          create)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          create-download-script)
            OPTIONS+=('--name' 'name of file or directory, regex accepted' '--output-directory' 'directory to output the file' '--public-key' 'path to public key' '--keybase-username' 'Name of keybase user to encrypt for' '--keybase-team' 'name of keybase team to encrypt for' '--file-regex' 'Expression to select only certain files')
            __icav2_handle_options_flags
            case ${MYWORDS[$INDEX-1]} in
              --name)
              ;;
              --output-directory)
              ;;
              --public-key)
              ;;
              --keybase-username)
              ;;
              --keybase-team)
              ;;
              --file-regex)
              ;;

            esac
            case $INDEX in
              2)
                  __comp_current_options || return
                    _icav2_projectdata_create-download-script_param_data_path_completion
              ;;


            *)
                __comp_current_options || return
            ;;
            esac
          ;;
          delete)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          download)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          downloadurl)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          find)
            OPTIONS+=('--min-depth' 'minimum depth to search' '--max-depth' 'maximum depth to search' '--type' 'data type' '--name' 'name of file or directory, regex accepted' '--creator' 'The creator id or username' '--long-listing' 'use long-listing format to show owner, modification timestamp and size' '--time' 'sort items by time' '--reverse' 'reverse order')
            __icav2_handle_options_flags
            case ${MYWORDS[$INDEX-1]} in
              --min-depth)
              ;;
              --max-depth)
              ;;
              --type)
                _icav2_compreply "FILE" "FOLDER"
                return
              ;;
              --name)
              ;;
              --creator)
              ;;
              --long-listing)
              ;;
              --time)
              ;;
              --reverse)
              ;;

            esac
            case $INDEX in
              2)
                  __comp_current_options || return
                    _icav2_projectdata_find_param_data_path_completion
              ;;


            *)
                __comp_current_options || return
            ;;
            esac
          ;;
          folderuploadsession)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          get)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          link)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          list)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          ls)
            OPTIONS+=('--long-listing' 'use long-listing format to show owner, modification timestamp and size' '--time' 'sort items by time' '--reverse' 'reverse order')
            __icav2_handle_options_flags
            case ${MYWORDS[$INDEX-1]} in
              --long-listing)
              ;;
              --time)
              ;;
              --reverse)
              ;;

            esac
            case $INDEX in
              2)
                  __comp_current_options || return
                    _icav2_projectdata_ls_param_data_path_completion
              ;;


            *)
                __comp_current_options || return
            ;;
            esac
          ;;
          mount)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          s3-sync-download)
            OPTIONS+=('--write-script-path' 'Optional, write out a script instead of invoking aws s3 command' '--s3-sync-arg' 'Other arguments are sent to aws s3 sync, specify multiple times for multiple arguments')
            __icav2_handle_options_flags
            case ${MYWORDS[$INDEX-1]} in
              --write-script-path)
                compopt -o filenames
                return
              ;;
              --s3-sync-arg)
              ;;

            esac
            case $INDEX in
              2)
                  __comp_current_options || return
                    _icav2_projectdata_s3-sync-download_param_data_path_completion
              ;;
              3)
                  __comp_current_options || return
                    compopt -o dirnames
              ;;


            *)
                __comp_current_options || return
            ;;
            esac
          ;;
          s3-sync-upload)
            OPTIONS+=('--write-script-path' 'Optional, write out a script instead of invoking aws s3 command' '--s3-sync-arg' 'Other arguments are sent to aws s3 sync, specify multiple times for multiple arguments')
            __icav2_handle_options_flags
            case ${MYWORDS[$INDEX-1]} in
              --write-script-path)
                compopt -o filenames
                return
              ;;
              --s3-sync-arg)
              ;;

            esac
            case $INDEX in
              2)
                  __comp_current_options || return
                    compopt -o dirnames
              ;;
              3)
                  __comp_current_options || return
                    _icav2_projectdata_s3-sync-upload_param_data_path_completion
              ;;


            *)
                __comp_current_options || return
            ;;
            esac
          ;;
          temporarycredentials)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          unarchive)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          unlink)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          unmount)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          update)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          upload)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          view)
            OPTIONS+=('--browser' 'Display file in browser')
            __icav2_handle_options_flags
            case ${MYWORDS[$INDEX-1]} in
              --browser)
              ;;

            esac
            case $INDEX in
              2)
                  __comp_current_options || return
                    _icav2_projectdata_view_param_data_path_completion
              ;;


            *)
                __comp_current_options || return
            ;;
            esac
          ;;
        esac

        ;;
        esac
      ;;
      projectpipelines)
        __icav2_handle_options_flags
        case $INDEX in

        1)
            __comp_current_options || return
            __icav2_dynamic_comp 'commands' 'create'$'\t''Create a pipeline'$'\n''create-cwl-wes-input-template'$'\t''Create a WES input template for a CWL workflow ready for launch'$'\n''create-cwl-workflow-from-github-release'$'\t''From a github release, deploy a workflow to icav2'$'\n''create-cwl-workflow-from-zip'$'\t''From a zip file, deploy a workflow to icav2'$'\n''input'$'\t''Retrieve input parameters of pipeline'$'\n''link'$'\t''Link pipeline to a project'$'\n''list'$'\t''List of pipelines for a project'$'\n''start'$'\t''Start a pipeline'$'\n''start-cwl-wes'$'\t''Launch an analysis on icav2'$'\n''unlink'$'\t''Unlink pipeline from a project'

        ;;
        *)
        # subcmds
        case ${MYWORDS[1]} in
          create)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          create-cwl-wes-input-template)
            OPTIONS+=('--pipeline-id' 'Optional, id of the pipeline you wish to launch' '--pipeline-code' 'Optional, name of the pipeline you wish to launch' '--user-reference' 'Optional, name of the workflow analysis' '--name' 'Optional, name of the workflow analysis' '--output-template-yaml-path' 'Required, Output template yaml path, parent directory must exist' '--output-parent-folder-id' 'Optional, the id of the parent folder to write outputs to' '--output-parent-folder-path' 'Optional, the path to the parent folder to write outputs to (will be created if it doesn'"\\'"'t exist)' '--analysis-storage-id' 'Optional, analysis storage id, overrides default analysis storage size' '--analysis-storage-size' 'Optional, analysis storage size, one of Small, Medium, Large' '--activation-id' 'Optional, the activation id used by the pipeline analysis' '--user-tag' 'User tags to attach to the analysis pipeline, specify multiple times for multiple user tags' '--technical-tag' 'User tags to attach to the analysis pipeline, specify multiple times for multiple technical tags' '--reference-tag' 'User tags to attach to the analysis pipeline, specify multiple times for multiple reference tags')
            __icav2_handle_options_flags
            case ${MYWORDS[$INDEX-1]} in
              --pipeline-id)
                _icav2_projectpipelines_create-cwl-wes-input-template_option_pipeline_id_completion
              ;;
              --pipeline-code)
                _icav2_projectpipelines_create-cwl-wes-input-template_option_pipeline_code_completion
              ;;
              --user-reference)
              ;;
              --name)
              ;;
              --output-template-yaml-path)
                compopt -o filenames
                return
              ;;
              --output-parent-folder-id)
              ;;
              --output-parent-folder-path)
                _icav2_projectpipelines_create-cwl-wes-input-template_option_output_parent_folder_path_completion
              ;;
              --analysis-storage-id)
              ;;
              --analysis-storage-size)
                _icav2_compreply "Small" "Medium" "Large"
                return
              ;;
              --activation-id)
              ;;
              --user-tag)
              ;;
              --technical-tag)
              ;;
              --reference-tag)
              ;;

            esac
            case $INDEX in

            *)
                __comp_current_options || return
            ;;
            esac
          ;;
          create-cwl-workflow-from-github-release)
            OPTIONS+=('--analysis-storage-id' 'analysis storage id' '--analysis-storage-size' 'analysis storage size')
            __icav2_handle_options_flags
            case ${MYWORDS[$INDEX-1]} in
              --analysis-storage-id)
              ;;
              --analysis-storage-size)
                _icav2_compreply "Small" "Medium" "Large"
                return
              ;;

            esac
            case $INDEX in
              2)
                  __comp_current_options || return
              ;;


            *)
                __comp_current_options || return
            ;;
            esac
          ;;
          create-cwl-workflow-from-zip)
            OPTIONS+=('--analysis-storage-id' 'analysis storage id' '--analysis-storage-size' 'analysis storage size')
            __icav2_handle_options_flags
            case ${MYWORDS[$INDEX-1]} in
              --analysis-storage-id)
              ;;
              --analysis-storage-size)
                _icav2_compreply "Small" "Medium" "Large"
                return
              ;;

            esac
            case $INDEX in
              2)
                  __comp_current_options || return
                    compopt -o filenames
              ;;


            *)
                __comp_current_options || return
            ;;
            esac
          ;;
          input)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          link)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          list)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          start)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          start-cwl-wes)
            OPTIONS+=('--launch-yaml' 'Required, input json similar to v1' '--pipeline-id' 'Optional, id of the pipeline you wish to launch' '--pipeline-code' 'Optional, name of the pipeline you wish to launch' '--output-parent-folder-id' 'Optional, the id of the parent folder to write outputs to' '--output-parent-folder-path' 'Optional, the path to the parent folder to write outputs to (will be created if it doesn'"\\'"'t exist)' '--analysis-storage-id' 'Optional, analysis storage id, overrides default analysis storage size' '--analysis-storage-size' 'Optional, analysis storage size, one of Small, Medium, Large' '--activation-id' 'Optional, the activation id used by the pipeline analysis' '--create-cwl-analysis-json-output-path' 'Optional, Path to output a json file that contains the body for a create cwl analysis (https://ica.illumina.com/ica/api/swagger/index.html#/Project%20Analysis/createCwlAnalysis)')
            __icav2_handle_options_flags
            case ${MYWORDS[$INDEX-1]} in
              --launch-yaml)
                compopt -o filenames
                return
              ;;
              --pipeline-id)
                _icav2_projectpipelines_start-cwl-wes_option_pipeline_id_completion
              ;;
              --pipeline-code)
                _icav2_projectpipelines_start-cwl-wes_option_pipeline_code_completion
              ;;
              --output-parent-folder-id)
              ;;
              --output-parent-folder-path)
                _icav2_projectpipelines_start-cwl-wes_option_output_parent_folder_path_completion
              ;;
              --analysis-storage-id)
              ;;
              --analysis-storage-size)
                _icav2_compreply "Small" "Medium" "Large"
                return
              ;;
              --activation-id)
              ;;
              --create-cwl-analysis-json-output-path)
              ;;

            esac
            case $INDEX in

            *)
                __comp_current_options || return
            ;;
            esac
          ;;
          unlink)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
        esac

        ;;
        esac
      ;;
      projects)
        __icav2_handle_options_flags
        case $INDEX in

        1)
            __comp_current_options || return
            __icav2_dynamic_comp 'commands' 'create'$'\t''Create a project'$'\n''enter'$'\t''Enter project context'$'\n''exit'$'\t''Exit project context'$'\n''get'$'\t''Get details of a project'$'\n''list'$'\t''List projects'

        ;;
        *)
        # subcmds
        case ${MYWORDS[1]} in
          create)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          enter)
            __icav2_handle_options_flags
            case ${MYWORDS[$INDEX-1]} in

            esac
            case $INDEX in
              2)
                  __comp_current_options || return
                    _icav2_projects_enter_param_project_name_completion
              ;;


            *)
                __comp_current_options || return
            ;;
            esac
          ;;
          exit)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          get)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          list)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
        esac

        ;;
        esac
      ;;
      projectsamples)
        __icav2_handle_options_flags
        case $INDEX in

        1)
            __comp_current_options || return
            __icav2_dynamic_comp 'commands' 'complete'$'\t''Set sample to complete'$'\n''create'$'\t''Create a sample for a project'$'\n''delete'$'\t''Delete a sample for a project'$'\n''get'$'\t''Get details of a sample'$'\n''link'$'\t''Link data to a sample for a project'$'\n''list'$'\t''List of samples for a project'$'\n''listdata'$'\t''List data from given sample'$'\n''unlink'$'\t''Unlink data from a sample for a project'$'\n''update'$'\t''Update a sample for a project'

        ;;
        *)
        # subcmds
        case ${MYWORDS[1]} in
          complete)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          create)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          delete)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          get)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          link)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          list)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          listdata)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          unlink)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          update)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
        esac

        ;;
        esac
      ;;
      regions)
        __icav2_handle_options_flags
        case $INDEX in

        1)
            __comp_current_options || return
            __icav2_dynamic_comp 'commands' 'list'$'\t''list of regions'

        ;;
        *)
        # subcmds
        case ${MYWORDS[1]} in
          list)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
        esac

        ;;
        esac
      ;;
      storagebundles)
        __icav2_handle_options_flags
        case $INDEX in

        1)
            __comp_current_options || return
            __icav2_dynamic_comp 'commands' 'list'$'\t''list of storage bundles'

        ;;
        *)
        # subcmds
        case ${MYWORDS[1]} in
          list)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
        esac

        ;;
        esac
      ;;
      storageconfigurations)
        __icav2_handle_options_flags
        case $INDEX in

        1)
            __comp_current_options || return
            __icav2_dynamic_comp 'commands' 'list'$'\t''list of storage configurations'

        ;;
        *)
        # subcmds
        case ${MYWORDS[1]} in
          list)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
        esac

        ;;
        esac
      ;;
      tokens)
        __icav2_handle_options_flags
        case $INDEX in

        1)
            __comp_current_options || return
            __icav2_dynamic_comp 'commands' 'create'$'\t''Create a JWT token'$'\n''refresh'$'\t''Refresh a JWT token from basic authentication'

        ;;
        *)
        # subcmds
        case ${MYWORDS[1]} in
          create)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          refresh)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
        esac

        ;;
        esac
      ;;
      version)
        __icav2_handle_options_flags
        __comp_current_options true || return # no subcmds, no params/opts
      ;;
    esac

    ;;
    esac

}

_icav2_compreply() {
    local prefix=""
    local IFS=$'\n'
    cur="$(printf '%q' "$cur")"
    IFS=$IFS COMPREPLY=($(compgen -P "$prefix" -W "$*" -- "$cur"))
    __ltrim_colon_completions "$prefix$cur"

    # http://stackoverflow.com/questions/7267185/bash-autocompletion-add-description-for-possible-completions
    if [[ ${#COMPREPLY[*]} -eq 1 ]]; then # Only one completion
        COMPREPLY=( "${COMPREPLY[0]%% -- *}" ) # Remove ' -- ' and everything after
        COMPREPLY=( "${COMPREPLY[0]%%+( )}" ) # Remove trailing spaces
    fi
}

_icav2_projectanalyses_gantt-plot_param_analysis_id_completion() {
    local CURRENT_WORD="${words[$cword]}"
    local param_analysis_id="$(
## CONFIG SETUP ##

if [[ -z "${ICAV2_ACCESS_TOKEN-}" ]]; then
  ICAV2_ACCESS_TOKEN="$(yq \
    --unwrapScalar \
    '
      .access-token
    ' < "${HOME}/.icav2/.session.ica.yaml"
  )"
fi


if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  ICAV2_PROJECT_ID="$(yq \
    --unwrapScalar \
      '
        .project-id
      ' < "${HOME}/.icav2/.session.ica.yaml"
  )"
fi

if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  exit
fi

# Check token expiry
if [[ \
  "$(  \
    cut -d'.' -f2 <<< "${ICAV2_ACCESS_TOKEN}" | \
      (
        if type gbase64 1>/dev/null 2>&1; then
          gbase64 -d 2>/dev/null || true
        else
          base64 -d 2>/dev/null || true
        fi
      ) | \
    jq --raw-output '.exp' \
  )" < "$(date +%s)" ]]; then
 ICAV2_ACCESS_TOKEN="$(icav2 tokens create)"

 # Replace token
 ICAV2_ACCESS_TOKEN="${ICAV2_ACCESS_TOKEN}" \
 yq --inplace \
   '
      .access-token = env(ICAV2_ACCESS_TOKEN)
   ' "${HOME}/.icav2/.session.ica.yaml"
fi

ICAV2_BASE_URL="${ICAV2_BASE_URL-ica.illumina.com}"

## END CONFIG SETUP ##

## LIST ANALYSIS IDS

curl \
  --fail --silent --location \
  --request 'GET' \
  --header 'Accept: application/vnd.illumina.v3+json' \
  --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}" \
  "https://${ICAV2_BASE_URL}/ica/rest/api/projects/${ICAV2_PROJECT_ID}/analyses" | \
jq --raw-output \
  '
   .items |
   map(.id) |
   .[]
  '
)"
    _icav2_compreply "$param_analysis_id"
}
_icav2_projectanalyses_get-analysis-step-logs_param_analysis_id_completion() {
    local CURRENT_WORD="${words[$cword]}"
    local param_analysis_id="$(
## CONFIG SETUP ##

if [[ -z "${ICAV2_ACCESS_TOKEN-}" ]]; then
  ICAV2_ACCESS_TOKEN="$(yq \
    --unwrapScalar \
    '
      .access-token
    ' < "${HOME}/.icav2/.session.ica.yaml"
  )"
fi


if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  ICAV2_PROJECT_ID="$(yq \
    --unwrapScalar \
      '
        .project-id
      ' < "${HOME}/.icav2/.session.ica.yaml"
  )"
fi

if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  exit
fi

# Check token expiry
if [[ \
  "$(  \
    cut -d'.' -f2 <<< "${ICAV2_ACCESS_TOKEN}" | \
      (
        if type gbase64 1>/dev/null 2>&1; then
          gbase64 -d 2>/dev/null || true
        else
          base64 -d 2>/dev/null || true
        fi
      ) | \
    jq --raw-output '.exp' \
  )" < "$(date +%s)" ]]; then
 ICAV2_ACCESS_TOKEN="$(icav2 tokens create)"

 # Replace token
 ICAV2_ACCESS_TOKEN="${ICAV2_ACCESS_TOKEN}" \
 yq --inplace \
   '
      .access-token = env(ICAV2_ACCESS_TOKEN)
   ' "${HOME}/.icav2/.session.ica.yaml"
fi

ICAV2_BASE_URL="${ICAV2_BASE_URL-ica.illumina.com}"

## END CONFIG SETUP ##

## LIST ANALYSIS IDS

curl \
  --fail --silent --location \
  --request 'GET' \
  --header 'Accept: application/vnd.illumina.v3+json' \
  --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}" \
  "https://${ICAV2_BASE_URL}/ica/rest/api/projects/${ICAV2_PROJECT_ID}/analyses" | \
jq --raw-output \
  '
   .items |
   map(.id) |
   .[]
  '
)"
    _icav2_compreply "$param_analysis_id"
}
_icav2_projectanalyses_get-cwl-analysis-input-json_param_analysis_id_completion() {
    local CURRENT_WORD="${words[$cword]}"
    local param_analysis_id="$(
## CONFIG SETUP ##

if [[ -z "${ICAV2_ACCESS_TOKEN-}" ]]; then
  ICAV2_ACCESS_TOKEN="$(yq \
    --unwrapScalar \
    '
      .access-token
    ' < "${HOME}/.icav2/.session.ica.yaml"
  )"
fi


if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  ICAV2_PROJECT_ID="$(yq \
    --unwrapScalar \
      '
        .project-id
      ' < "${HOME}/.icav2/.session.ica.yaml"
  )"
fi

if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  exit
fi

# Check token expiry
if [[ \
  "$(  \
    cut -d'.' -f2 <<< "${ICAV2_ACCESS_TOKEN}" | \
      (
        if type gbase64 1>/dev/null 2>&1; then
          gbase64 -d 2>/dev/null || true
        else
          base64 -d 2>/dev/null || true
        fi
      ) | \
    jq --raw-output '.exp' \
  )" < "$(date +%s)" ]]; then
 ICAV2_ACCESS_TOKEN="$(icav2 tokens create)"

 # Replace token
 ICAV2_ACCESS_TOKEN="${ICAV2_ACCESS_TOKEN}" \
 yq --inplace \
   '
      .access-token = env(ICAV2_ACCESS_TOKEN)
   ' "${HOME}/.icav2/.session.ica.yaml"
fi

ICAV2_BASE_URL="${ICAV2_BASE_URL-ica.illumina.com}"

## END CONFIG SETUP ##

## LIST ANALYSIS IDS

curl \
  --fail --silent --location \
  --request 'GET' \
  --header 'Accept: application/vnd.illumina.v3+json' \
  --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}" \
  "https://${ICAV2_BASE_URL}/ica/rest/api/projects/${ICAV2_PROJECT_ID}/analyses" | \
jq --raw-output \
  '
   .items |
   map(.id) |
   .[]
  '
)"
    _icav2_compreply "$param_analysis_id"
}
_icav2_projectanalyses_get-cwl-analysis-output-json_param_analysis_id_completion() {
    local CURRENT_WORD="${words[$cword]}"
    local param_analysis_id="$(
## CONFIG SETUP ##

if [[ -z "${ICAV2_ACCESS_TOKEN-}" ]]; then
  ICAV2_ACCESS_TOKEN="$(yq \
    --unwrapScalar \
    '
      .access-token
    ' < "${HOME}/.icav2/.session.ica.yaml"
  )"
fi


if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  ICAV2_PROJECT_ID="$(yq \
    --unwrapScalar \
      '
        .project-id
      ' < "${HOME}/.icav2/.session.ica.yaml"
  )"
fi

if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  exit
fi

# Check token expiry
if [[ \
  "$(  \
    cut -d'.' -f2 <<< "${ICAV2_ACCESS_TOKEN}" | \
      (
        if type gbase64 1>/dev/null 2>&1; then
          gbase64 -d 2>/dev/null || true
        else
          base64 -d 2>/dev/null || true
        fi
      ) | \
    jq --raw-output '.exp' \
  )" < "$(date +%s)" ]]; then
 ICAV2_ACCESS_TOKEN="$(icav2 tokens create)"

 # Replace token
 ICAV2_ACCESS_TOKEN="${ICAV2_ACCESS_TOKEN}" \
 yq --inplace \
   '
      .access-token = env(ICAV2_ACCESS_TOKEN)
   ' "${HOME}/.icav2/.session.ica.yaml"
fi

ICAV2_BASE_URL="${ICAV2_BASE_URL-ica.illumina.com}"

## END CONFIG SETUP ##

## LIST ANALYSIS IDS

curl \
  --fail --silent --location \
  --request 'GET' \
  --header 'Accept: application/vnd.illumina.v3+json' \
  --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}" \
  "https://${ICAV2_BASE_URL}/ica/rest/api/projects/${ICAV2_PROJECT_ID}/analyses" | \
jq --raw-output \
  '
   .items |
   map(.id) |
   .[]
  '
)"
    _icav2_compreply "$param_analysis_id"
}
_icav2_projectanalyses_list-analysis-steps_param_analysis_id_completion() {
    local CURRENT_WORD="${words[$cword]}"
    local param_analysis_id="$(
## CONFIG SETUP ##

if [[ -z "${ICAV2_ACCESS_TOKEN-}" ]]; then
  ICAV2_ACCESS_TOKEN="$(yq \
    --unwrapScalar \
    '
      .access-token
    ' < "${HOME}/.icav2/.session.ica.yaml"
  )"
fi


if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  ICAV2_PROJECT_ID="$(yq \
    --unwrapScalar \
      '
        .project-id
      ' < "${HOME}/.icav2/.session.ica.yaml"
  )"
fi

if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  exit
fi

# Check token expiry
if [[ \
  "$(  \
    cut -d'.' -f2 <<< "${ICAV2_ACCESS_TOKEN}" | \
      (
        if type gbase64 1>/dev/null 2>&1; then
          gbase64 -d 2>/dev/null || true
        else
          base64 -d 2>/dev/null || true
        fi
      ) | \
    jq --raw-output '.exp' \
  )" < "$(date +%s)" ]]; then
 ICAV2_ACCESS_TOKEN="$(icav2 tokens create)"

 # Replace token
 ICAV2_ACCESS_TOKEN="${ICAV2_ACCESS_TOKEN}" \
 yq --inplace \
   '
      .access-token = env(ICAV2_ACCESS_TOKEN)
   ' "${HOME}/.icav2/.session.ica.yaml"
fi

ICAV2_BASE_URL="${ICAV2_BASE_URL-ica.illumina.com}"

## END CONFIG SETUP ##

## LIST ANALYSIS IDS

curl \
  --fail --silent --location \
  --request 'GET' \
  --header 'Accept: application/vnd.illumina.v3+json' \
  --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}" \
  "https://${ICAV2_BASE_URL}/ica/rest/api/projects/${ICAV2_PROJECT_ID}/analyses" | \
jq --raw-output \
  '
   .items |
   map(.id) |
   .[]
  '
)"
    _icav2_compreply "$param_analysis_id"
}
_icav2_projectdata_create-download-script_param_data_path_completion() {
    local CURRENT_WORD="${words[$cword]}"
    local param_data_path="$(
## CONFIG SETUP ##

if [[ -z "${ICAV2_ACCESS_TOKEN-}" ]]; then
  ICAV2_ACCESS_TOKEN="$(yq \
    --unwrapScalar \
    '
      .access-token
    ' < "${HOME}/.icav2/.session.ica.yaml"
  )"
fi


if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  ICAV2_PROJECT_ID="$(yq \
    --unwrapScalar \
      '
        .project-id
      ' < "${HOME}/.icav2/.session.ica.yaml"
  )"
fi

if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  exit
fi

# Check token expiry
if [[ \
  "$(  \
    cut -d'.' -f2 <<< "${ICAV2_ACCESS_TOKEN}" | \
      (
        if type gbase64 1>/dev/null 2>&1; then
          gbase64 -d 2>/dev/null || true
        else
          base64 -d 2>/dev/null || true
        fi
      ) | \
    jq --raw-output '.exp' \
  )" < "$(date +%s)" ]]; then
 ICAV2_ACCESS_TOKEN="$(icav2 tokens create)"

 # Replace token
 ICAV2_ACCESS_TOKEN="${ICAV2_ACCESS_TOKEN}" \
 yq --inplace \
   '
      .access-token = env(ICAV2_ACCESS_TOKEN)
   ' "${HOME}/.icav2/.session.ica.yaml"
fi

ICAV2_BASE_URL="${ICAV2_BASE_URL-ica.illumina.com}"

## END CONFIG SETUP ##

ITEM_TYPE="FOLDER"

## INVOKE DATA FUNCTION ##


max_items=1000
parent_folder_path="/"
if [[ -n "${CURRENT_WORD-}" ]]; then
  if [[ "${CURRENT_WORD}" =~ ^.*/$ ]]; then
    parent_folder_path="${CURRENT_WORD}"
    basename_var=""
  else
    parent_folder_path="$(dirname "${CURRENT_WORD}")/"
    if [[ "${parent_folder_path}" == "//" ]]; then
      parent_folder_path="/"
    fi
    basename_var="$(basename "${CURRENT_WORD}")"
  fi
fi

params="$( \
  jq --null-input --raw-output \
    --arg parent_folder_path "${parent_folder_path}" \
    --arg file_name "${basename_var}" \
    --arg type "${ITEM_TYPE-}" \
    --arg page_size "${max_items}" \
    '
      # Intialise parameters
      {
        "parentFolderPath": $parent_folder_path,
        "filename": $file_name,
        "filenameMatchMode": "FUZZY",
        "page_size": $page_size,
        "type": $type
      } |
      # Drop nulls
      with_entries(
        select(
          .value != ""
        )
      ) |
      # Convert to string
      to_entries |
      map(
        "\(.key)=\(.value)"
      ) |
      join("&")
    '
)"

# List Data in Directory
curl \
  --fail --silent --location \
  --request GET \
  --header "Accept: application/vnd.illumina.v3+json" \
  --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}" \
  --url "https://${ICAV2_BASE_URL}/ica/rest/api/projects/${ICAV2_PROJECT_ID}/data?${params}" | \
jq --raw-output \
  '
    .items |
    map(
      .data.details.path
    ) |
    .[]
  '

## INVOKE DATA FUNCTION ##
)"
    _icav2_compreply "$param_data_path"
}
_icav2_projectdata_find_param_data_path_completion() {
    local CURRENT_WORD="${words[$cword]}"
    local param_data_path="$(
## CONFIG SETUP ##

if [[ -z "${ICAV2_ACCESS_TOKEN-}" ]]; then
  ICAV2_ACCESS_TOKEN="$(yq \
    --unwrapScalar \
    '
      .access-token
    ' < "${HOME}/.icav2/.session.ica.yaml"
  )"
fi


if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  ICAV2_PROJECT_ID="$(yq \
    --unwrapScalar \
      '
        .project-id
      ' < "${HOME}/.icav2/.session.ica.yaml"
  )"
fi

if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  exit
fi

# Check token expiry
if [[ \
  "$(  \
    cut -d'.' -f2 <<< "${ICAV2_ACCESS_TOKEN}" | \
      (
        if type gbase64 1>/dev/null 2>&1; then
          gbase64 -d 2>/dev/null || true
        else
          base64 -d 2>/dev/null || true
        fi
      ) | \
    jq --raw-output '.exp' \
  )" < "$(date +%s)" ]]; then
 ICAV2_ACCESS_TOKEN="$(icav2 tokens create)"

 # Replace token
 ICAV2_ACCESS_TOKEN="${ICAV2_ACCESS_TOKEN}" \
 yq --inplace \
   '
      .access-token = env(ICAV2_ACCESS_TOKEN)
   ' "${HOME}/.icav2/.session.ica.yaml"
fi

ICAV2_BASE_URL="${ICAV2_BASE_URL-ica.illumina.com}"

## END CONFIG SETUP ##

ITEM_TYPE="FOLDER"

## INVOKE DATA FUNCTION ##


max_items=1000
parent_folder_path="/"
if [[ -n "${CURRENT_WORD-}" ]]; then
  if [[ "${CURRENT_WORD}" =~ ^.*/$ ]]; then
    parent_folder_path="${CURRENT_WORD}"
    basename_var=""
  else
    parent_folder_path="$(dirname "${CURRENT_WORD}")/"
    if [[ "${parent_folder_path}" == "//" ]]; then
      parent_folder_path="/"
    fi
    basename_var="$(basename "${CURRENT_WORD}")"
  fi
fi

params="$( \
  jq --null-input --raw-output \
    --arg parent_folder_path "${parent_folder_path}" \
    --arg file_name "${basename_var}" \
    --arg type "${ITEM_TYPE-}" \
    --arg page_size "${max_items}" \
    '
      # Intialise parameters
      {
        "parentFolderPath": $parent_folder_path,
        "filename": $file_name,
        "filenameMatchMode": "FUZZY",
        "page_size": $page_size,
        "type": $type
      } |
      # Drop nulls
      with_entries(
        select(
          .value != ""
        )
      ) |
      # Convert to string
      to_entries |
      map(
        "\(.key)=\(.value)"
      ) |
      join("&")
    '
)"

# List Data in Directory
curl \
  --fail --silent --location \
  --request GET \
  --header "Accept: application/vnd.illumina.v3+json" \
  --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}" \
  --url "https://${ICAV2_BASE_URL}/ica/rest/api/projects/${ICAV2_PROJECT_ID}/data?${params}" | \
jq --raw-output \
  '
    .items |
    map(
      .data.details.path
    ) |
    .[]
  '

## INVOKE DATA FUNCTION ##
)"
    _icav2_compreply "$param_data_path"
}
_icav2_projectdata_ls_param_data_path_completion() {
    local CURRENT_WORD="${words[$cword]}"
    local param_data_path="$(
## CONFIG SETUP ##

if [[ -z "${ICAV2_ACCESS_TOKEN-}" ]]; then
  ICAV2_ACCESS_TOKEN="$(yq \
    --unwrapScalar \
    '
      .access-token
    ' < "${HOME}/.icav2/.session.ica.yaml"
  )"
fi


if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  ICAV2_PROJECT_ID="$(yq \
    --unwrapScalar \
      '
        .project-id
      ' < "${HOME}/.icav2/.session.ica.yaml"
  )"
fi

if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  exit
fi

# Check token expiry
if [[ \
  "$(  \
    cut -d'.' -f2 <<< "${ICAV2_ACCESS_TOKEN}" | \
      (
        if type gbase64 1>/dev/null 2>&1; then
          gbase64 -d 2>/dev/null || true
        else
          base64 -d 2>/dev/null || true
        fi
      ) | \
    jq --raw-output '.exp' \
  )" < "$(date +%s)" ]]; then
 ICAV2_ACCESS_TOKEN="$(icav2 tokens create)"

 # Replace token
 ICAV2_ACCESS_TOKEN="${ICAV2_ACCESS_TOKEN}" \
 yq --inplace \
   '
      .access-token = env(ICAV2_ACCESS_TOKEN)
   ' "${HOME}/.icav2/.session.ica.yaml"
fi

ICAV2_BASE_URL="${ICAV2_BASE_URL-ica.illumina.com}"

## END CONFIG SETUP ##

ITEM_TYPE=""

## INVOKE DATA FUNCTION ##


max_items=1000
parent_folder_path="/"
if [[ -n "${CURRENT_WORD-}" ]]; then
  if [[ "${CURRENT_WORD}" =~ ^.*/$ ]]; then
    parent_folder_path="${CURRENT_WORD}"
    basename_var=""
  else
    parent_folder_path="$(dirname "${CURRENT_WORD}")/"
    if [[ "${parent_folder_path}" == "//" ]]; then
      parent_folder_path="/"
    fi
    basename_var="$(basename "${CURRENT_WORD}")"
  fi
fi

params="$( \
  jq --null-input --raw-output \
    --arg parent_folder_path "${parent_folder_path}" \
    --arg file_name "${basename_var}" \
    --arg type "${ITEM_TYPE-}" \
    --arg page_size "${max_items}" \
    '
      # Intialise parameters
      {
        "parentFolderPath": $parent_folder_path,
        "filename": $file_name,
        "filenameMatchMode": "FUZZY",
        "page_size": $page_size,
        "type": $type
      } |
      # Drop nulls
      with_entries(
        select(
          .value != ""
        )
      ) |
      # Convert to string
      to_entries |
      map(
        "\(.key)=\(.value)"
      ) |
      join("&")
    '
)"

# List Data in Directory
curl \
  --fail --silent --location \
  --request GET \
  --header "Accept: application/vnd.illumina.v3+json" \
  --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}" \
  --url "https://${ICAV2_BASE_URL}/ica/rest/api/projects/${ICAV2_PROJECT_ID}/data?${params}" | \
jq --raw-output \
  '
    .items |
    map(
      .data.details.path
    ) |
    .[]
  '

## INVOKE DATA FUNCTION ##
)"
    _icav2_compreply "$param_data_path"
}
_icav2_projectdata_s3-sync-download_param_data_path_completion() {
    local CURRENT_WORD="${words[$cword]}"
    local param_data_path="$(
## CONFIG SETUP ##

if [[ -z "${ICAV2_ACCESS_TOKEN-}" ]]; then
  ICAV2_ACCESS_TOKEN="$(yq \
    --unwrapScalar \
    '
      .access-token
    ' < "${HOME}/.icav2/.session.ica.yaml"
  )"
fi


if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  ICAV2_PROJECT_ID="$(yq \
    --unwrapScalar \
      '
        .project-id
      ' < "${HOME}/.icav2/.session.ica.yaml"
  )"
fi

if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  exit
fi

# Check token expiry
if [[ \
  "$(  \
    cut -d'.' -f2 <<< "${ICAV2_ACCESS_TOKEN}" | \
      (
        if type gbase64 1>/dev/null 2>&1; then
          gbase64 -d 2>/dev/null || true
        else
          base64 -d 2>/dev/null || true
        fi
      ) | \
    jq --raw-output '.exp' \
  )" < "$(date +%s)" ]]; then
 ICAV2_ACCESS_TOKEN="$(icav2 tokens create)"

 # Replace token
 ICAV2_ACCESS_TOKEN="${ICAV2_ACCESS_TOKEN}" \
 yq --inplace \
   '
      .access-token = env(ICAV2_ACCESS_TOKEN)
   ' "${HOME}/.icav2/.session.ica.yaml"
fi

ICAV2_BASE_URL="${ICAV2_BASE_URL-ica.illumina.com}"

## END CONFIG SETUP ##

ITEM_TYPE="FOLDER"

## INVOKE DATA FUNCTION ##


max_items=1000
parent_folder_path="/"
if [[ -n "${CURRENT_WORD-}" ]]; then
  if [[ "${CURRENT_WORD}" =~ ^.*/$ ]]; then
    parent_folder_path="${CURRENT_WORD}"
    basename_var=""
  else
    parent_folder_path="$(dirname "${CURRENT_WORD}")/"
    if [[ "${parent_folder_path}" == "//" ]]; then
      parent_folder_path="/"
    fi
    basename_var="$(basename "${CURRENT_WORD}")"
  fi
fi

params="$( \
  jq --null-input --raw-output \
    --arg parent_folder_path "${parent_folder_path}" \
    --arg file_name "${basename_var}" \
    --arg type "${ITEM_TYPE-}" \
    --arg page_size "${max_items}" \
    '
      # Intialise parameters
      {
        "parentFolderPath": $parent_folder_path,
        "filename": $file_name,
        "filenameMatchMode": "FUZZY",
        "page_size": $page_size,
        "type": $type
      } |
      # Drop nulls
      with_entries(
        select(
          .value != ""
        )
      ) |
      # Convert to string
      to_entries |
      map(
        "\(.key)=\(.value)"
      ) |
      join("&")
    '
)"

# List Data in Directory
curl \
  --fail --silent --location \
  --request GET \
  --header "Accept: application/vnd.illumina.v3+json" \
  --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}" \
  --url "https://${ICAV2_BASE_URL}/ica/rest/api/projects/${ICAV2_PROJECT_ID}/data?${params}" | \
jq --raw-output \
  '
    .items |
    map(
      .data.details.path
    ) |
    .[]
  '

## INVOKE DATA FUNCTION ##
)"
    _icav2_compreply "$param_data_path"
}
_icav2_projectdata_s3-sync-upload_param_data_path_completion() {
    local CURRENT_WORD="${words[$cword]}"
    local param_data_path="$(
## CONFIG SETUP ##

if [[ -z "${ICAV2_ACCESS_TOKEN-}" ]]; then
  ICAV2_ACCESS_TOKEN="$(yq \
    --unwrapScalar \
    '
      .access-token
    ' < "${HOME}/.icav2/.session.ica.yaml"
  )"
fi


if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  ICAV2_PROJECT_ID="$(yq \
    --unwrapScalar \
      '
        .project-id
      ' < "${HOME}/.icav2/.session.ica.yaml"
  )"
fi

if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  exit
fi

# Check token expiry
if [[ \
  "$(  \
    cut -d'.' -f2 <<< "${ICAV2_ACCESS_TOKEN}" | \
      (
        if type gbase64 1>/dev/null 2>&1; then
          gbase64 -d 2>/dev/null || true
        else
          base64 -d 2>/dev/null || true
        fi
      ) | \
    jq --raw-output '.exp' \
  )" < "$(date +%s)" ]]; then
 ICAV2_ACCESS_TOKEN="$(icav2 tokens create)"

 # Replace token
 ICAV2_ACCESS_TOKEN="${ICAV2_ACCESS_TOKEN}" \
 yq --inplace \
   '
      .access-token = env(ICAV2_ACCESS_TOKEN)
   ' "${HOME}/.icav2/.session.ica.yaml"
fi

ICAV2_BASE_URL="${ICAV2_BASE_URL-ica.illumina.com}"

## END CONFIG SETUP ##

ITEM_TYPE="FOLDER"

## INVOKE DATA FUNCTION ##


max_items=1000
parent_folder_path="/"
if [[ -n "${CURRENT_WORD-}" ]]; then
  if [[ "${CURRENT_WORD}" =~ ^.*/$ ]]; then
    parent_folder_path="${CURRENT_WORD}"
    basename_var=""
  else
    parent_folder_path="$(dirname "${CURRENT_WORD}")/"
    if [[ "${parent_folder_path}" == "//" ]]; then
      parent_folder_path="/"
    fi
    basename_var="$(basename "${CURRENT_WORD}")"
  fi
fi

params="$( \
  jq --null-input --raw-output \
    --arg parent_folder_path "${parent_folder_path}" \
    --arg file_name "${basename_var}" \
    --arg type "${ITEM_TYPE-}" \
    --arg page_size "${max_items}" \
    '
      # Intialise parameters
      {
        "parentFolderPath": $parent_folder_path,
        "filename": $file_name,
        "filenameMatchMode": "FUZZY",
        "page_size": $page_size,
        "type": $type
      } |
      # Drop nulls
      with_entries(
        select(
          .value != ""
        )
      ) |
      # Convert to string
      to_entries |
      map(
        "\(.key)=\(.value)"
      ) |
      join("&")
    '
)"

# List Data in Directory
curl \
  --fail --silent --location \
  --request GET \
  --header "Accept: application/vnd.illumina.v3+json" \
  --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}" \
  --url "https://${ICAV2_BASE_URL}/ica/rest/api/projects/${ICAV2_PROJECT_ID}/data?${params}" | \
jq --raw-output \
  '
    .items |
    map(
      .data.details.path
    ) |
    .[]
  '

## INVOKE DATA FUNCTION ##
)"
    _icav2_compreply "$param_data_path"
}
_icav2_projectdata_view_param_data_path_completion() {
    local CURRENT_WORD="${words[$cword]}"
    local param_data_path="$(
## CONFIG SETUP ##

if [[ -z "${ICAV2_ACCESS_TOKEN-}" ]]; then
  ICAV2_ACCESS_TOKEN="$(yq \
    --unwrapScalar \
    '
      .access-token
    ' < "${HOME}/.icav2/.session.ica.yaml"
  )"
fi


if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  ICAV2_PROJECT_ID="$(yq \
    --unwrapScalar \
      '
        .project-id
      ' < "${HOME}/.icav2/.session.ica.yaml"
  )"
fi

if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  exit
fi

# Check token expiry
if [[ \
  "$(  \
    cut -d'.' -f2 <<< "${ICAV2_ACCESS_TOKEN}" | \
      (
        if type gbase64 1>/dev/null 2>&1; then
          gbase64 -d 2>/dev/null || true
        else
          base64 -d 2>/dev/null || true
        fi
      ) | \
    jq --raw-output '.exp' \
  )" < "$(date +%s)" ]]; then
 ICAV2_ACCESS_TOKEN="$(icav2 tokens create)"

 # Replace token
 ICAV2_ACCESS_TOKEN="${ICAV2_ACCESS_TOKEN}" \
 yq --inplace \
   '
      .access-token = env(ICAV2_ACCESS_TOKEN)
   ' "${HOME}/.icav2/.session.ica.yaml"
fi

ICAV2_BASE_URL="${ICAV2_BASE_URL-ica.illumina.com}"

## END CONFIG SETUP ##

ITEM_TYPE=""

## INVOKE DATA FUNCTION ##


max_items=1000
parent_folder_path="/"
if [[ -n "${CURRENT_WORD-}" ]]; then
  if [[ "${CURRENT_WORD}" =~ ^.*/$ ]]; then
    parent_folder_path="${CURRENT_WORD}"
    basename_var=""
  else
    parent_folder_path="$(dirname "${CURRENT_WORD}")/"
    if [[ "${parent_folder_path}" == "//" ]]; then
      parent_folder_path="/"
    fi
    basename_var="$(basename "${CURRENT_WORD}")"
  fi
fi

params="$( \
  jq --null-input --raw-output \
    --arg parent_folder_path "${parent_folder_path}" \
    --arg file_name "${basename_var}" \
    --arg type "${ITEM_TYPE-}" \
    --arg page_size "${max_items}" \
    '
      # Intialise parameters
      {
        "parentFolderPath": $parent_folder_path,
        "filename": $file_name,
        "filenameMatchMode": "FUZZY",
        "page_size": $page_size,
        "type": $type
      } |
      # Drop nulls
      with_entries(
        select(
          .value != ""
        )
      ) |
      # Convert to string
      to_entries |
      map(
        "\(.key)=\(.value)"
      ) |
      join("&")
    '
)"

# List Data in Directory
curl \
  --fail --silent --location \
  --request GET \
  --header "Accept: application/vnd.illumina.v3+json" \
  --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}" \
  --url "https://${ICAV2_BASE_URL}/ica/rest/api/projects/${ICAV2_PROJECT_ID}/data?${params}" | \
jq --raw-output \
  '
    .items |
    map(
      .data.details.path
    ) |
    .[]
  '

## INVOKE DATA FUNCTION ##
)"
    _icav2_compreply "$param_data_path"
}
_icav2_projectpipelines_create-cwl-wes-input-template_option_pipeline_id_completion() {
    local CURRENT_WORD="${words[$cword]}"
    local param_pipeline_id="$(
## CONFIG SETUP ##

if [[ -z "${ICAV2_ACCESS_TOKEN-}" ]]; then
  ICAV2_ACCESS_TOKEN="$(yq \
    --unwrapScalar \
    '
      .access-token
    ' < "${HOME}/.icav2/.session.ica.yaml"
  )"
fi


if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  ICAV2_PROJECT_ID="$(yq \
    --unwrapScalar \
      '
        .project-id
      ' < "${HOME}/.icav2/.session.ica.yaml"
  )"
fi

if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  exit
fi

# Check token expiry
if [[ \
  "$(  \
    cut -d'.' -f2 <<< "${ICAV2_ACCESS_TOKEN}" | \
      (
        if type gbase64 1>/dev/null 2>&1; then
          gbase64 -d 2>/dev/null || true
        else
          base64 -d 2>/dev/null || true
        fi
      ) | \
    jq --raw-output '.exp' \
  )" < "$(date +%s)" ]]; then
 ICAV2_ACCESS_TOKEN="$(icav2 tokens create)"

 # Replace token
 ICAV2_ACCESS_TOKEN="${ICAV2_ACCESS_TOKEN}" \
 yq --inplace \
   '
      .access-token = env(ICAV2_ACCESS_TOKEN)
   ' "${HOME}/.icav2/.session.ica.yaml"
fi

ICAV2_BASE_URL="${ICAV2_BASE_URL-ica.illumina.com}"

## END CONFIG SETUP ##

ATTRIBUTE_NAME="id"

## INVOKE PROJECT PIPELINE ##

curl \
  --fail --silent --location \
  --request "GET" \
  --url "https://ica.illumina.com/ica/rest/api/projects/${ICAV2_PROJECT_ID}/pipelines" \
  --header "Accept: application/vnd.illumina.v3+json" \
  --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}" | \
jq \
  --raw-output \
  --arg attribute_type "${ATTRIBUTE_NAME}" \
  '
    .items |
    map(.pipeline | .[$attribute_type]) |
    .[]
  '

## INVOKE PROJECT PIPELINE ##
)"
    _icav2_compreply "$param_pipeline_id"
}
_icav2_projectpipelines_create-cwl-wes-input-template_option_pipeline_code_completion() {
    local CURRENT_WORD="${words[$cword]}"
    local param_pipeline_code="$(
## CONFIG SETUP ##

if [[ -z "${ICAV2_ACCESS_TOKEN-}" ]]; then
  ICAV2_ACCESS_TOKEN="$(yq \
    --unwrapScalar \
    '
      .access-token
    ' < "${HOME}/.icav2/.session.ica.yaml"
  )"
fi


if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  ICAV2_PROJECT_ID="$(yq \
    --unwrapScalar \
      '
        .project-id
      ' < "${HOME}/.icav2/.session.ica.yaml"
  )"
fi

if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  exit
fi

# Check token expiry
if [[ \
  "$(  \
    cut -d'.' -f2 <<< "${ICAV2_ACCESS_TOKEN}" | \
      (
        if type gbase64 1>/dev/null 2>&1; then
          gbase64 -d 2>/dev/null || true
        else
          base64 -d 2>/dev/null || true
        fi
      ) | \
    jq --raw-output '.exp' \
  )" < "$(date +%s)" ]]; then
 ICAV2_ACCESS_TOKEN="$(icav2 tokens create)"

 # Replace token
 ICAV2_ACCESS_TOKEN="${ICAV2_ACCESS_TOKEN}" \
 yq --inplace \
   '
      .access-token = env(ICAV2_ACCESS_TOKEN)
   ' "${HOME}/.icav2/.session.ica.yaml"
fi

ICAV2_BASE_URL="${ICAV2_BASE_URL-ica.illumina.com}"

## END CONFIG SETUP ##

ATTRIBUTE_NAME="code"

## INVOKE PROJECT PIPELINE ##

curl \
  --fail --silent --location \
  --request "GET" \
  --url "https://ica.illumina.com/ica/rest/api/projects/${ICAV2_PROJECT_ID}/pipelines" \
  --header "Accept: application/vnd.illumina.v3+json" \
  --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}" | \
jq \
  --raw-output \
  --arg attribute_type "${ATTRIBUTE_NAME}" \
  '
    .items |
    map(.pipeline | .[$attribute_type]) |
    .[]
  '

## INVOKE PROJECT PIPELINE ##
)"
    _icav2_compreply "$param_pipeline_code"
}
_icav2_projectpipelines_create-cwl-wes-input-template_option_output_parent_folder_path_completion() {
    local CURRENT_WORD="${words[$cword]}"
    local param_output_parent_folder_path="$(
## CONFIG SETUP ##

if [[ -z "${ICAV2_ACCESS_TOKEN-}" ]]; then
  ICAV2_ACCESS_TOKEN="$(yq \
    --unwrapScalar \
    '
      .access-token
    ' < "${HOME}/.icav2/.session.ica.yaml"
  )"
fi


if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  ICAV2_PROJECT_ID="$(yq \
    --unwrapScalar \
      '
        .project-id
      ' < "${HOME}/.icav2/.session.ica.yaml"
  )"
fi

if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  exit
fi

# Check token expiry
if [[ \
  "$(  \
    cut -d'.' -f2 <<< "${ICAV2_ACCESS_TOKEN}" | \
      (
        if type gbase64 1>/dev/null 2>&1; then
          gbase64 -d 2>/dev/null || true
        else
          base64 -d 2>/dev/null || true
        fi
      ) | \
    jq --raw-output '.exp' \
  )" < "$(date +%s)" ]]; then
 ICAV2_ACCESS_TOKEN="$(icav2 tokens create)"

 # Replace token
 ICAV2_ACCESS_TOKEN="${ICAV2_ACCESS_TOKEN}" \
 yq --inplace \
   '
      .access-token = env(ICAV2_ACCESS_TOKEN)
   ' "${HOME}/.icav2/.session.ica.yaml"
fi

ICAV2_BASE_URL="${ICAV2_BASE_URL-ica.illumina.com}"

## END CONFIG SETUP ##

ITEM_TYPE="FOLDER"

## INVOKE DATA FUNCTION ##


max_items=1000
parent_folder_path="/"
if [[ -n "${CURRENT_WORD-}" ]]; then
  if [[ "${CURRENT_WORD}" =~ ^.*/$ ]]; then
    parent_folder_path="${CURRENT_WORD}"
    basename_var=""
  else
    parent_folder_path="$(dirname "${CURRENT_WORD}")/"
    if [[ "${parent_folder_path}" == "//" ]]; then
      parent_folder_path="/"
    fi
    basename_var="$(basename "${CURRENT_WORD}")"
  fi
fi

params="$( \
  jq --null-input --raw-output \
    --arg parent_folder_path "${parent_folder_path}" \
    --arg file_name "${basename_var}" \
    --arg type "${ITEM_TYPE-}" \
    --arg page_size "${max_items}" \
    '
      # Intialise parameters
      {
        "parentFolderPath": $parent_folder_path,
        "filename": $file_name,
        "filenameMatchMode": "FUZZY",
        "page_size": $page_size,
        "type": $type
      } |
      # Drop nulls
      with_entries(
        select(
          .value != ""
        )
      ) |
      # Convert to string
      to_entries |
      map(
        "\(.key)=\(.value)"
      ) |
      join("&")
    '
)"

# List Data in Directory
curl \
  --fail --silent --location \
  --request GET \
  --header "Accept: application/vnd.illumina.v3+json" \
  --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}" \
  --url "https://${ICAV2_BASE_URL}/ica/rest/api/projects/${ICAV2_PROJECT_ID}/data?${params}" | \
jq --raw-output \
  '
    .items |
    map(
      .data.details.path
    ) |
    .[]
  '

## INVOKE DATA FUNCTION ##
)"
    _icav2_compreply "$param_output_parent_folder_path"
}
_icav2_projectpipelines_start-cwl-wes_option_pipeline_id_completion() {
    local CURRENT_WORD="${words[$cword]}"
    local param_pipeline_id="$(
## CONFIG SETUP ##

if [[ -z "${ICAV2_ACCESS_TOKEN-}" ]]; then
  ICAV2_ACCESS_TOKEN="$(yq \
    --unwrapScalar \
    '
      .access-token
    ' < "${HOME}/.icav2/.session.ica.yaml"
  )"
fi


if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  ICAV2_PROJECT_ID="$(yq \
    --unwrapScalar \
      '
        .project-id
      ' < "${HOME}/.icav2/.session.ica.yaml"
  )"
fi

if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  exit
fi

# Check token expiry
if [[ \
  "$(  \
    cut -d'.' -f2 <<< "${ICAV2_ACCESS_TOKEN}" | \
      (
        if type gbase64 1>/dev/null 2>&1; then
          gbase64 -d 2>/dev/null || true
        else
          base64 -d 2>/dev/null || true
        fi
      ) | \
    jq --raw-output '.exp' \
  )" < "$(date +%s)" ]]; then
 ICAV2_ACCESS_TOKEN="$(icav2 tokens create)"

 # Replace token
 ICAV2_ACCESS_TOKEN="${ICAV2_ACCESS_TOKEN}" \
 yq --inplace \
   '
      .access-token = env(ICAV2_ACCESS_TOKEN)
   ' "${HOME}/.icav2/.session.ica.yaml"
fi

ICAV2_BASE_URL="${ICAV2_BASE_URL-ica.illumina.com}"

## END CONFIG SETUP ##

ATTRIBUTE_NAME="id"

## INVOKE PROJECT PIPELINE ##

curl \
  --fail --silent --location \
  --request "GET" \
  --url "https://ica.illumina.com/ica/rest/api/projects/${ICAV2_PROJECT_ID}/pipelines" \
  --header "Accept: application/vnd.illumina.v3+json" \
  --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}" | \
jq \
  --raw-output \
  --arg attribute_type "${ATTRIBUTE_NAME}" \
  '
    .items |
    map(.pipeline | .[$attribute_type]) |
    .[]
  '

## INVOKE PROJECT PIPELINE ##
)"
    _icav2_compreply "$param_pipeline_id"
}
_icav2_projectpipelines_start-cwl-wes_option_pipeline_code_completion() {
    local CURRENT_WORD="${words[$cword]}"
    local param_pipeline_code="$(
## CONFIG SETUP ##

if [[ -z "${ICAV2_ACCESS_TOKEN-}" ]]; then
  ICAV2_ACCESS_TOKEN="$(yq \
    --unwrapScalar \
    '
      .access-token
    ' < "${HOME}/.icav2/.session.ica.yaml"
  )"
fi


if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  ICAV2_PROJECT_ID="$(yq \
    --unwrapScalar \
      '
        .project-id
      ' < "${HOME}/.icav2/.session.ica.yaml"
  )"
fi

if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  exit
fi

# Check token expiry
if [[ \
  "$(  \
    cut -d'.' -f2 <<< "${ICAV2_ACCESS_TOKEN}" | \
      (
        if type gbase64 1>/dev/null 2>&1; then
          gbase64 -d 2>/dev/null || true
        else
          base64 -d 2>/dev/null || true
        fi
      ) | \
    jq --raw-output '.exp' \
  )" < "$(date +%s)" ]]; then
 ICAV2_ACCESS_TOKEN="$(icav2 tokens create)"

 # Replace token
 ICAV2_ACCESS_TOKEN="${ICAV2_ACCESS_TOKEN}" \
 yq --inplace \
   '
      .access-token = env(ICAV2_ACCESS_TOKEN)
   ' "${HOME}/.icav2/.session.ica.yaml"
fi

ICAV2_BASE_URL="${ICAV2_BASE_URL-ica.illumina.com}"

## END CONFIG SETUP ##

ATTRIBUTE_NAME="code"

## INVOKE PROJECT PIPELINE ##

curl \
  --fail --silent --location \
  --request "GET" \
  --url "https://ica.illumina.com/ica/rest/api/projects/${ICAV2_PROJECT_ID}/pipelines" \
  --header "Accept: application/vnd.illumina.v3+json" \
  --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}" | \
jq \
  --raw-output \
  --arg attribute_type "${ATTRIBUTE_NAME}" \
  '
    .items |
    map(.pipeline | .[$attribute_type]) |
    .[]
  '

## INVOKE PROJECT PIPELINE ##
)"
    _icav2_compreply "$param_pipeline_code"
}
_icav2_projectpipelines_start-cwl-wes_option_output_parent_folder_path_completion() {
    local CURRENT_WORD="${words[$cword]}"
    local param_output_parent_folder_path="$(
## CONFIG SETUP ##

if [[ -z "${ICAV2_ACCESS_TOKEN-}" ]]; then
  ICAV2_ACCESS_TOKEN="$(yq \
    --unwrapScalar \
    '
      .access-token
    ' < "${HOME}/.icav2/.session.ica.yaml"
  )"
fi


if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  ICAV2_PROJECT_ID="$(yq \
    --unwrapScalar \
      '
        .project-id
      ' < "${HOME}/.icav2/.session.ica.yaml"
  )"
fi

if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  exit
fi

# Check token expiry
if [[ \
  "$(  \
    cut -d'.' -f2 <<< "${ICAV2_ACCESS_TOKEN}" | \
      (
        if type gbase64 1>/dev/null 2>&1; then
          gbase64 -d 2>/dev/null || true
        else
          base64 -d 2>/dev/null || true
        fi
      ) | \
    jq --raw-output '.exp' \
  )" < "$(date +%s)" ]]; then
 ICAV2_ACCESS_TOKEN="$(icav2 tokens create)"

 # Replace token
 ICAV2_ACCESS_TOKEN="${ICAV2_ACCESS_TOKEN}" \
 yq --inplace \
   '
      .access-token = env(ICAV2_ACCESS_TOKEN)
   ' "${HOME}/.icav2/.session.ica.yaml"
fi

ICAV2_BASE_URL="${ICAV2_BASE_URL-ica.illumina.com}"

## END CONFIG SETUP ##

ITEM_TYPE="FOLDER"

## INVOKE DATA FUNCTION ##


max_items=1000
parent_folder_path="/"
if [[ -n "${CURRENT_WORD-}" ]]; then
  if [[ "${CURRENT_WORD}" =~ ^.*/$ ]]; then
    parent_folder_path="${CURRENT_WORD}"
    basename_var=""
  else
    parent_folder_path="$(dirname "${CURRENT_WORD}")/"
    if [[ "${parent_folder_path}" == "//" ]]; then
      parent_folder_path="/"
    fi
    basename_var="$(basename "${CURRENT_WORD}")"
  fi
fi

params="$( \
  jq --null-input --raw-output \
    --arg parent_folder_path "${parent_folder_path}" \
    --arg file_name "${basename_var}" \
    --arg type "${ITEM_TYPE-}" \
    --arg page_size "${max_items}" \
    '
      # Intialise parameters
      {
        "parentFolderPath": $parent_folder_path,
        "filename": $file_name,
        "filenameMatchMode": "FUZZY",
        "page_size": $page_size,
        "type": $type
      } |
      # Drop nulls
      with_entries(
        select(
          .value != ""
        )
      ) |
      # Convert to string
      to_entries |
      map(
        "\(.key)=\(.value)"
      ) |
      join("&")
    '
)"

# List Data in Directory
curl \
  --fail --silent --location \
  --request GET \
  --header "Accept: application/vnd.illumina.v3+json" \
  --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}" \
  --url "https://${ICAV2_BASE_URL}/ica/rest/api/projects/${ICAV2_PROJECT_ID}/data?${params}" | \
jq --raw-output \
  '
    .items |
    map(
      .data.details.path
    ) |
    .[]
  '

## INVOKE DATA FUNCTION ##
)"
    _icav2_compreply "$param_output_parent_folder_path"
}
_icav2_projects_enter_param_project_name_completion() {
    local CURRENT_WORD="${words[$cword]}"
    local param_project_name="$(
## CONFIG SETUP ##

if [[ -z "${ICAV2_ACCESS_TOKEN-}" ]]; then
  ICAV2_ACCESS_TOKEN="$(yq \
    --unwrapScalar \
    '
      .access-token
    ' < "${HOME}/.icav2/.session.ica.yaml"
  )"
fi


if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  ICAV2_PROJECT_ID="$(yq \
    --unwrapScalar \
      '
        .project-id
      ' < "${HOME}/.icav2/.session.ica.yaml"
  )"
fi

if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  exit
fi

# Check token expiry
if [[ \
  "$(  \
    cut -d'.' -f2 <<< "${ICAV2_ACCESS_TOKEN}" | \
      (
        if type gbase64 1>/dev/null 2>&1; then
          gbase64 -d 2>/dev/null || true
        else
          base64 -d 2>/dev/null || true
        fi
      ) | \
    jq --raw-output '.exp' \
  )" < "$(date +%s)" ]]; then
 ICAV2_ACCESS_TOKEN="$(icav2 tokens create)"

 # Replace token
 ICAV2_ACCESS_TOKEN="${ICAV2_ACCESS_TOKEN}" \
 yq --inplace \
   '
      .access-token = env(ICAV2_ACCESS_TOKEN)
   ' "${HOME}/.icav2/.session.ica.yaml"
fi

ICAV2_BASE_URL="${ICAV2_BASE_URL-ica.illumina.com}"

## END CONFIG SETUP ##

ATTRIBUTE_NAME="name"

## INVOKE PROJECT FUNCTION ##

curl \
  --fail --silent --location \
  --request "GET" \
  --url "https://ica.illumina.com/ica/rest/api/projects/" \
  --header "Accept: application/vnd.illumina.v3+json" \
  --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}" | \
jq \
  --raw-output \
  --arg attribute_name "${ATTRIBUTE_NAME}" \
  '
    .items |
    map(.[$attribute_name]) |
    .[]
  '

## INVOKE PROJECT FUNCTION ##
)"
    _icav2_compreply "$param_project_name"
}

__icav2_dynamic_comp() {
    local argname="$1"
    local arg="$2"
    local name desc cols desclength formatted
    local comp=()
    local max=0

    while read -r line; do
        name="$line"
        desc="$line"
        name="${name%$'\t'*}"
        if [[ "${#name}" -gt "$max" ]]; then
            max="${#name}"
        fi
    done <<< "$arg"

    while read -r line; do
        name="$line"
        desc="$line"
        name="${name%$'\t'*}"
        desc="${desc/*$'\t'}"
        if [[ -n "$desc" && "$desc" != "$name" ]]; then
            # TODO portable?
            cols=`tput cols`
            [[ -z $cols ]] && cols=80
            desclength=`expr $cols - 4 - $max`
            formatted=`printf "%-*s -- %-*s" "$max" "$name" "$desclength" "$desc"`
            comp+=("$formatted")
        else
            comp+=("'$name'")
        fi
    done <<< "$arg"
    _icav2_compreply ${comp[@]}
}

function __icav2_handle_options() {
    local i j
    declare -a copy
    local last="${MYWORDS[$INDEX]}"
    local max=`expr ${#MYWORDS[@]} - 1`
    for ((i=0; i<$max; i++))
    do
        local word="${MYWORDS[$i]}"
        local found=
        for ((j=0; j<${#OPTIONS[@]}; j+=2))
        do
            local option="${OPTIONS[$j]}"
            if [[ "$word" == "$option" ]]; then
                found=1
                i=`expr $i + 1`
                break
            fi
        done
        if [[ -n $found && $i -lt $max ]]; then
            INDEX=`expr $INDEX - 2`
        else
            copy+=("$word")
        fi
    done
    MYWORDS=("${copy[@]}" "$last")
}

function __icav2_handle_flags() {
    local i j
    declare -a copy
    local last="${MYWORDS[$INDEX]}"
    local max=`expr ${#MYWORDS[@]} - 1`
    for ((i=0; i<$max; i++))
    do
        local word="${MYWORDS[$i]}"
        local found=
        for ((j=0; j<${#FLAGS[@]}; j+=2))
        do
            local flag="${FLAGS[$j]}"
            if [[ "$word" == "$flag" ]]; then
                found=1
                break
            fi
        done
        if [[ -n $found ]]; then
            INDEX=`expr $INDEX - 1`
        else
            copy+=("$word")
        fi
    done
    MYWORDS=("${copy[@]}" "$last")
}

__icav2_handle_options_flags() {
    __icav2_handle_options
    __icav2_handle_flags
}

__comp_current_options() {
    local always="$1"
    if [[ -n $always || ${MYWORDS[$INDEX]} =~ ^- ]]; then

      local options_spec=''
      local j=

      for ((j=0; j<${#FLAGS[@]}; j+=2))
      do
          local name="${FLAGS[$j]}"
          local desc="${FLAGS[$j+1]}"
          options_spec+="$name"$'\t'"$desc"$'\n'
      done

      for ((j=0; j<${#OPTIONS[@]}; j+=2))
      do
          local name="${OPTIONS[$j]}"
          local desc="${OPTIONS[$j+1]}"
          options_spec+="$name"$'\t'"$desc"$'\n'
      done
      __icav2_dynamic_comp 'options' "$options_spec"

      return 1
    else
      return 0
    fi
}


complete -o default -F _icav2 icav2


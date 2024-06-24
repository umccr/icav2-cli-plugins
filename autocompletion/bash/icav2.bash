#!/usr/bin/env bash

# Generated with perl module App::Spec v0.014

_icav2() {

    COMPREPLY=()
    local IFS=$'\n'
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
        __icav2_dynamic_comp 'commands' 'analysisstorages'$'\t''Analysis storages commands'$'\n''bundles'$'\t''Bundles commands'$'\n''config'$'\t''Config actions'$'\n''dataformats'$'\t''Data format commands'$'\n''help'$'\t''Help about any command'$'\n''metadatamodels'$'\t''Metadata model commands'$'\n''pipelines'$'\t''Pipeline commands'$'\n''projectanalyses'$'\t''Project analyses commands'$'\n''projectdata'$'\t''Project Data commands'$'\n''projectpipelines'$'\t''Project pipeline commands'$'\n''projects'$'\t''Project commands'$'\n''projectsamples'$'\t''Project samples commands'$'\n''regions'$'\t''Region commands'$'\n''storagebundles'$'\t''Storage bundle commands'$'\n''storageconfigurations'$'\t''Storage configurations commands'$'\n''tenants'$'\t''Handle tenant switching'$'\n''tokens'$'\t''Tokens commands'$'\n''version'$'\t''The version of this application'

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
      bundles)
        __icav2_handle_options_flags
        case $INDEX in

        1)
            __comp_current_options || return
            __icav2_dynamic_comp 'commands' 'add-bundle-to-project'$'\t''Add a bundle to a project'$'\n''add-data'$'\t''Add data to a bundle'$'\n''add-pipeline'$'\t''Add pipeline to a bundle'$'\n''get'$'\t''Initialise a bundle'$'\n''init'$'\t''Initialise a bundle'$'\n''list'$'\t''List bundles'$'\n''release'$'\t''Release a bundle'

        ;;
        *)
        # subcmds
        case ${MYWORDS[1]} in
          add-bundle-to-project)
            OPTIONS+=('--input-yaml' 'Path to input yaml' '--project' 'Project ID or name')
            __icav2_handle_options_flags
            case ${MYWORDS[$INDEX-1]} in
              --input-yaml)
              ;;
              --project)
                _icav2_bundles_add-bundle-to-project_option_project_completion
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
          add-data)
            OPTIONS+=('--input-yaml' 'Path to bundle yaml' '--data-id' 'ID of data to add to bundle' '--data-uri' 'Data URI to add to bundle')
            __icav2_handle_options_flags
            case ${MYWORDS[$INDEX-1]} in
              --input-yaml)
              ;;
              --data-id)
              ;;
              --data-uri)
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
          add-pipeline)
            OPTIONS+=('--input-yaml' 'Path to bundle yaml' '--pipeline-id' 'ID of pipeline to add to bundle' '--pipeline-code' 'Pipeline code to add to bundle')
            __icav2_handle_options_flags
            case ${MYWORDS[$INDEX-1]} in
              --input-yaml)
              ;;
              --pipeline-id)
              ;;
              --pipeline-code)
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
          get)
            OPTIONS+=('--output-yaml' 'Path to output yaml' '--json' 'Return bundle as json object to stdout')
            __icav2_handle_options_flags
            case ${MYWORDS[$INDEX-1]} in
              --output-yaml)
              ;;
              --json)
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
          init)
            OPTIONS+=('--short-description' 'A short description of the bundle' '--input-yaml' 'Path to bundle yaml' '--region' 'List of regions' '--json' 'Return bundle as json object to stdout')
            __icav2_handle_options_flags
            case ${MYWORDS[$INDEX-1]} in
              --short-description)
              ;;
              --input-yaml)
              ;;
              --region)
                _icav2_bundles_init_option_region_completion
              ;;
              --json)
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
          list)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          release)
            __icav2_handle_options_flags
            case ${MYWORDS[$INDEX-1]} in

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
            __icav2_dynamic_comp 'commands' 'get'$'\t''Get details of a pipeline'$'\n''list'$'\t''List pipelines'$'\n''list-projects'$'\t''List projects a pipeline resides in'$'\n''status-check'$'\t''Check pipeline ownership'

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
          list-projects)
            OPTIONS+=('----json' 'Output in json' '----include-bundle-linked' 'Include projects where the pipeline is linked via a bundle' '----include-hidden-projects' 'Include hidden projects')
            __icav2_handle_options_flags
            case ${MYWORDS[$INDEX-1]} in
              ----json)
              ;;
              ----include-bundle-linked)
              ;;
              ----include-hidden-projects)
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
          status-check)
            OPTIONS+=('----confirm-user-ownership' 'Confirm pipeline is owned by user' '----confirm-tenant-ownership' 'Confirm pipeline is owned by tenant')
            __icav2_handle_options_flags
            case ${MYWORDS[$INDEX-1]} in
              ----confirm-user-ownership)
              ;;
              ----confirm-tenant-ownership)
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
            __icav2_dynamic_comp 'commands' 'create'$'\t''Create a pipeline'$'\n''create-cwl-wes-input-template'$'\t''Create a WES input template for a CWL workflow ready for launch'$'\n''create-cwl-workflow-from-github-release'$'\t''From a github release, deploy a workflow to icav2'$'\n''create-cwl-workflow-from-zip'$'\t''From a zip file, deploy a workflow to icav2'$'\n''input'$'\t''Retrieve input parameters of pipeline'$'\n''link'$'\t''Link pipeline to a project'$'\n''list'$'\t''List of pipelines for a project'$'\n''start'$'\t''Start a pipeline'$'\n''start-cwl-wes'$'\t''Launch an analysis on icav2'$'\n''unlink'$'\t''Unlink pipeline from a project'$'\n''update'

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
          update)
            OPTIONS+=('--force' 'Dont confirm with user')
            __icav2_handle_options_flags
            case ${MYWORDS[$INDEX-1]} in
              --force)
              ;;

            esac
            case $INDEX in
              2)
                  __comp_current_options || return
                    compopt -o filenames
              ;;
              3)
                  __comp_current_options || return
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
            OPTIONS+=('--global' 'Update context in session yaml file')
            __icav2_handle_options_flags
            case ${MYWORDS[$INDEX-1]} in
              --global)
              ;;

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
      tenants)
        __icav2_handle_options_flags
        case $INDEX in

        1)
            __comp_current_options || return
            __icav2_dynamic_comp 'commands' 'enter'$'\t''enter a tenant'$'\n''init'$'\t''initialise a tenant'$'\n''list'$'\t''list tenants'$'\n''set-default-project'$'\t''Set default project for a given tenant'$'\n''set-default-tenant'$'\t''Set the default tenant by running icav2 config set under the hood'

        ;;
        *)
        # subcmds
        case ${MYWORDS[1]} in
          enter)
            OPTIONS+=('--global' 'enter tenant globally')
            __icav2_handle_options_flags
            case ${MYWORDS[$INDEX-1]} in
              --global)
              ;;

            esac
            case $INDEX in
              2)
                  __comp_current_options || return
                    _icav2_tenants_enter_param_tenant_name_completion
              ;;


            *)
                __comp_current_options || return
            ;;
            esac
          ;;
          init)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          list)
            __icav2_handle_options_flags
            __comp_current_options true || return # no subcmds, no params/opts
          ;;
          set-default-project)
            OPTIONS+=('--project_name' 'Name of project')
            __icav2_handle_options_flags
            case ${MYWORDS[$INDEX-1]} in
              --project_name)
              ;;

            esac
            case $INDEX in
              2)
                  __comp_current_options || return
                    _icav2_tenants_set-default-project_param_tenant_name_completion
              ;;


            *)
                __comp_current_options || return
            ;;
            esac
          ;;
          set-default-tenant)
            __icav2_handle_options_flags
            case ${MYWORDS[$INDEX-1]} in

            esac
            case $INDEX in
              2)
                  __comp_current_options || return
                    _icav2_tenants_set-default-tenant_param_tenant_name_completion
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
    cur="$(printf '%q' "$cur")"
    COMPREPLY=($(compgen -P "$prefix" -W "$*" -- "$cur"))
    __ltrim_colon_completions "$prefix$cur"

    # http://stackoverflow.com/questions/7267185/bash-autocompletion-add-description-for-possible-completions
    if [[ ${#COMPREPLY[*]} -eq 1 ]]; then # Only one completion
        COMPREPLY=( "${COMPREPLY[0]%% -- *}" ) # Remove ' -- ' and everything after
        COMPREPLY=( "${COMPREPLY[0]%%+( )}" ) # Remove trailing spaces
    fi
}

_icav2_bundles_init_option_region_completion() {
    local CURRENT_WORD="${words[$cword]}"
    local param_region="$(
curl \
  --fail --silent --location \
  --request "GET" \
  --url "${ICAV2_BASE_URL-https://ica.illumina.com/ica/rest}/api/regions/" \
  --header "Accept: application/vnd.illumina.v3+json" \
  --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}" | \
jq \
  --raw-output \
  '
    .items |
    map(.cityName) |
    .[]
  '
)"
    _icav2_compreply "$param_region"
}
_icav2_projectanalyses_gantt-plot_param_analysis_id_completion() {
    local CURRENT_WORD="${words[$cword]}"
    local param_analysis_id="$(
## CONFIG SETUP ##

# Check tenant
if [[ -n "${ICAV2_TENANT_NAME-}" ]]; then
  :
elif [[ -n "${ICAV2_DEFAULT_TENANT_NAME-}" ]]; then
  ICAV2_TENANT_NAME="${ICAV2_DEFAULT_TENANT_NAME}"
else
  # Get tenant name from cli plugins home
  if [[ -z "${ICAV2_CLI_PLUGINS_HOME}" ]]; then
    # Cannot go any further
    exit
  fi
  if [[ ! -r "${ICAV2_CLI_PLUGINS_HOME}/tenants/default_tenant.txt" ]]; then
    # Cannot go any further
    exit
  fi
  # Read from text file
  ICAV2_TENANT_NAME="$(cat "${ICAV2_CLI_PLUGINS_HOME}/tenants/default_tenant.txt")"
fi

__icav2_server_url="$( \
  yq \
    --unwrapScalar \
    '
      .server-url
    ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/config.yaml"
)"

__icav2_server_url_prefix="$( \
  cut -d'.' -f1 <<< "${__icav2_server_url}"
)"

if [[ -z "${ICAV2_ACCESS_TOKEN-}" ]]; then
  ICAV2_ACCESS_TOKEN="$(yq \
    --unwrapScalar \
    '
      .access-token
    ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/.session.${__icav2_server_url_prefix}.yaml"
  )"
fi


if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  ICAV2_PROJECT_ID="$(yq \
    --unwrapScalar \
      '
        .project-id
      ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/.session.${__icav2_server_url_prefix}.yaml"
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
  ICAV2_ACCESS_TOKEN="$(
    api_key="$( \
      yq \
      --unwrapScalar \
      '
        .x-api-key
      ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/config.yaml"
    )"
    curl --fail --show-error --silent --location \
      --request "POST" \
      --header "Accept: application/vnd.illumina.v3+json" \
      --header "X-API-Key: ${api_key}" \
      --url "https://${__icav2_server_url}/ica/rest/api/tokens" \
      --data ''
  )"

 # Replace token
 ICAV2_ACCESS_TOKEN="${ICAV2_ACCESS_TOKEN}" \
 yq --prettyPrint \
   '
      .access-token = env(ICAV2_ACCESS_TOKEN)
   ' < "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml" > "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml.tmp" && \
   mv "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml.tmp" "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml"
fi

if [[ -z "${ICAV2_BASE_URL-}" ]]; then
  ICAV2_BASE_URL="https://${__icav2_server_url}/ica/rest"
fi

## END CONFIG SETUP ##

## LIST ANALYSIS IDS
page_offset=0
page_size=1000
total_item_count="$( \
  curl \
      --fail \
      --silent \
      --location \
      --request 'GET' \
      --header 'Accept: application/vnd.illumina.v3+json' \
      --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}" \
      --url "${ICAV2_BASE_URL-https://ica.illumina.com/ica/rest}/api/projects/${ICAV2_PROJECT_ID}/analyses?pageOffset=0&pageSize=1" | \
  jq --raw-output '.totalItemCount' \
)"

while :; do
  eval "$( \
    curl \
      --fail \
      --silent \
      --location \
      --request 'GET' \
      --header 'Accept: application/vnd.illumina.v3+json' \
      --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}" \
      --url "${ICAV2_BASE_URL-https://ica.illumina.com/ica/rest}/api/projects/${ICAV2_PROJECT_ID}/analyses?pageOffset=${page_offset}&pageSize=${page_size}&sort=startDate%20desc" | \
    jq --raw-output \
      --arg cols "$(tput cols)" \
      '
        .items |
        (map(.id | length) | max) as $max_id_length |
        (($cols | tonumber) - $max_id_length - 4) as $max_description_length |
        map(
          [
            "printf",
            "%-*s -- %.*s\n",
            $max_id_length, .id,
            $max_description_length, "UserRef: \(.userReference)  Date: \(.startDate)"
          ] |
          @sh
        ) |
        .[]
      '
  )"
    (( page_offset += page_size ))

    if ! (( page_offset < total_item_count )); then
      break
    fi
done
)"
    _icav2_compreply "$param_analysis_id"
}
_icav2_projectanalyses_get-analysis-step-logs_param_analysis_id_completion() {
    local CURRENT_WORD="${words[$cword]}"
    local param_analysis_id="$(
## CONFIG SETUP ##

# Check tenant
if [[ -n "${ICAV2_TENANT_NAME-}" ]]; then
  :
elif [[ -n "${ICAV2_DEFAULT_TENANT_NAME-}" ]]; then
  ICAV2_TENANT_NAME="${ICAV2_DEFAULT_TENANT_NAME}"
else
  # Get tenant name from cli plugins home
  if [[ -z "${ICAV2_CLI_PLUGINS_HOME}" ]]; then
    # Cannot go any further
    exit
  fi
  if [[ ! -r "${ICAV2_CLI_PLUGINS_HOME}/tenants/default_tenant.txt" ]]; then
    # Cannot go any further
    exit
  fi
  # Read from text file
  ICAV2_TENANT_NAME="$(cat "${ICAV2_CLI_PLUGINS_HOME}/tenants/default_tenant.txt")"
fi

__icav2_server_url="$( \
  yq \
    --unwrapScalar \
    '
      .server-url
    ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/config.yaml"
)"

__icav2_server_url_prefix="$( \
  cut -d'.' -f1 <<< "${__icav2_server_url}"
)"

if [[ -z "${ICAV2_ACCESS_TOKEN-}" ]]; then
  ICAV2_ACCESS_TOKEN="$(yq \
    --unwrapScalar \
    '
      .access-token
    ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/.session.${__icav2_server_url_prefix}.yaml"
  )"
fi


if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  ICAV2_PROJECT_ID="$(yq \
    --unwrapScalar \
      '
        .project-id
      ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/.session.${__icav2_server_url_prefix}.yaml"
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
  ICAV2_ACCESS_TOKEN="$(
    api_key="$( \
      yq \
      --unwrapScalar \
      '
        .x-api-key
      ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/config.yaml"
    )"
    curl --fail --show-error --silent --location \
      --request "POST" \
      --header "Accept: application/vnd.illumina.v3+json" \
      --header "X-API-Key: ${api_key}" \
      --url "https://${__icav2_server_url}/ica/rest/api/tokens" \
      --data ''
  )"

 # Replace token
 ICAV2_ACCESS_TOKEN="${ICAV2_ACCESS_TOKEN}" \
 yq --prettyPrint \
   '
      .access-token = env(ICAV2_ACCESS_TOKEN)
   ' < "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml" > "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml.tmp" && \
   mv "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml.tmp" "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml"
fi

if [[ -z "${ICAV2_BASE_URL-}" ]]; then
  ICAV2_BASE_URL="https://${__icav2_server_url}/ica/rest"
fi

## END CONFIG SETUP ##

## LIST ANALYSIS IDS
page_offset=0
page_size=1000
total_item_count="$( \
  curl \
      --fail \
      --silent \
      --location \
      --request 'GET' \
      --header 'Accept: application/vnd.illumina.v3+json' \
      --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}" \
      --url "${ICAV2_BASE_URL-https://ica.illumina.com/ica/rest}/api/projects/${ICAV2_PROJECT_ID}/analyses?pageOffset=0&pageSize=1" | \
  jq --raw-output '.totalItemCount' \
)"

while :; do
  eval "$( \
    curl \
      --fail \
      --silent \
      --location \
      --request 'GET' \
      --header 'Accept: application/vnd.illumina.v3+json' \
      --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}" \
      --url "${ICAV2_BASE_URL-https://ica.illumina.com/ica/rest}/api/projects/${ICAV2_PROJECT_ID}/analyses?pageOffset=${page_offset}&pageSize=${page_size}&sort=startDate%20desc" | \
    jq --raw-output \
      --arg cols "$(tput cols)" \
      '
        .items |
        (map(.id | length) | max) as $max_id_length |
        (($cols | tonumber) - $max_id_length - 4) as $max_description_length |
        map(
          [
            "printf",
            "%-*s -- %.*s\n",
            $max_id_length, .id,
            $max_description_length, "UserRef: \(.userReference)  Date: \(.startDate)"
          ] |
          @sh
        ) |
        .[]
      '
  )"
    (( page_offset += page_size ))

    if ! (( page_offset < total_item_count )); then
      break
    fi
done
)"
    _icav2_compreply "$param_analysis_id"
}
_icav2_projectanalyses_get-cwl-analysis-input-json_param_analysis_id_completion() {
    local CURRENT_WORD="${words[$cword]}"
    local param_analysis_id="$(
## CONFIG SETUP ##

# Check tenant
if [[ -n "${ICAV2_TENANT_NAME-}" ]]; then
  :
elif [[ -n "${ICAV2_DEFAULT_TENANT_NAME-}" ]]; then
  ICAV2_TENANT_NAME="${ICAV2_DEFAULT_TENANT_NAME}"
else
  # Get tenant name from cli plugins home
  if [[ -z "${ICAV2_CLI_PLUGINS_HOME}" ]]; then
    # Cannot go any further
    exit
  fi
  if [[ ! -r "${ICAV2_CLI_PLUGINS_HOME}/tenants/default_tenant.txt" ]]; then
    # Cannot go any further
    exit
  fi
  # Read from text file
  ICAV2_TENANT_NAME="$(cat "${ICAV2_CLI_PLUGINS_HOME}/tenants/default_tenant.txt")"
fi

__icav2_server_url="$( \
  yq \
    --unwrapScalar \
    '
      .server-url
    ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/config.yaml"
)"

__icav2_server_url_prefix="$( \
  cut -d'.' -f1 <<< "${__icav2_server_url}"
)"

if [[ -z "${ICAV2_ACCESS_TOKEN-}" ]]; then
  ICAV2_ACCESS_TOKEN="$(yq \
    --unwrapScalar \
    '
      .access-token
    ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/.session.${__icav2_server_url_prefix}.yaml"
  )"
fi


if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  ICAV2_PROJECT_ID="$(yq \
    --unwrapScalar \
      '
        .project-id
      ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/.session.${__icav2_server_url_prefix}.yaml"
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
  ICAV2_ACCESS_TOKEN="$(
    api_key="$( \
      yq \
      --unwrapScalar \
      '
        .x-api-key
      ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/config.yaml"
    )"
    curl --fail --show-error --silent --location \
      --request "POST" \
      --header "Accept: application/vnd.illumina.v3+json" \
      --header "X-API-Key: ${api_key}" \
      --url "https://${__icav2_server_url}/ica/rest/api/tokens" \
      --data ''
  )"

 # Replace token
 ICAV2_ACCESS_TOKEN="${ICAV2_ACCESS_TOKEN}" \
 yq --prettyPrint \
   '
      .access-token = env(ICAV2_ACCESS_TOKEN)
   ' < "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml" > "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml.tmp" && \
   mv "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml.tmp" "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml"
fi

if [[ -z "${ICAV2_BASE_URL-}" ]]; then
  ICAV2_BASE_URL="https://${__icav2_server_url}/ica/rest"
fi

## END CONFIG SETUP ##

## LIST ANALYSIS IDS
page_offset=0
page_size=1000
total_item_count="$( \
  curl \
      --fail \
      --silent \
      --location \
      --request 'GET' \
      --header 'Accept: application/vnd.illumina.v3+json' \
      --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}" \
      --url "${ICAV2_BASE_URL-https://ica.illumina.com/ica/rest}/api/projects/${ICAV2_PROJECT_ID}/analyses?pageOffset=0&pageSize=1" | \
  jq --raw-output '.totalItemCount' \
)"

while :; do
  eval "$( \
    curl \
      --fail \
      --silent \
      --location \
      --request 'GET' \
      --header 'Accept: application/vnd.illumina.v3+json' \
      --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}" \
      --url "${ICAV2_BASE_URL-https://ica.illumina.com/ica/rest}/api/projects/${ICAV2_PROJECT_ID}/analyses?pageOffset=${page_offset}&pageSize=${page_size}&sort=startDate%20desc" | \
    jq --raw-output \
      --arg cols "$(tput cols)" \
      '
        .items |
        (map(.id | length) | max) as $max_id_length |
        (($cols | tonumber) - $max_id_length - 4) as $max_description_length |
        map(
          [
            "printf",
            "%-*s -- %.*s\n",
            $max_id_length, .id,
            $max_description_length, "UserRef: \(.userReference)  Date: \(.startDate)"
          ] |
          @sh
        ) |
        .[]
      '
  )"
    (( page_offset += page_size ))

    if ! (( page_offset < total_item_count )); then
      break
    fi
done
)"
    _icav2_compreply "$param_analysis_id"
}
_icav2_projectanalyses_get-cwl-analysis-output-json_param_analysis_id_completion() {
    local CURRENT_WORD="${words[$cword]}"
    local param_analysis_id="$(
## CONFIG SETUP ##

# Check tenant
if [[ -n "${ICAV2_TENANT_NAME-}" ]]; then
  :
elif [[ -n "${ICAV2_DEFAULT_TENANT_NAME-}" ]]; then
  ICAV2_TENANT_NAME="${ICAV2_DEFAULT_TENANT_NAME}"
else
  # Get tenant name from cli plugins home
  if [[ -z "${ICAV2_CLI_PLUGINS_HOME}" ]]; then
    # Cannot go any further
    exit
  fi
  if [[ ! -r "${ICAV2_CLI_PLUGINS_HOME}/tenants/default_tenant.txt" ]]; then
    # Cannot go any further
    exit
  fi
  # Read from text file
  ICAV2_TENANT_NAME="$(cat "${ICAV2_CLI_PLUGINS_HOME}/tenants/default_tenant.txt")"
fi

__icav2_server_url="$( \
  yq \
    --unwrapScalar \
    '
      .server-url
    ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/config.yaml"
)"

__icav2_server_url_prefix="$( \
  cut -d'.' -f1 <<< "${__icav2_server_url}"
)"

if [[ -z "${ICAV2_ACCESS_TOKEN-}" ]]; then
  ICAV2_ACCESS_TOKEN="$(yq \
    --unwrapScalar \
    '
      .access-token
    ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/.session.${__icav2_server_url_prefix}.yaml"
  )"
fi


if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  ICAV2_PROJECT_ID="$(yq \
    --unwrapScalar \
      '
        .project-id
      ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/.session.${__icav2_server_url_prefix}.yaml"
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
  ICAV2_ACCESS_TOKEN="$(
    api_key="$( \
      yq \
      --unwrapScalar \
      '
        .x-api-key
      ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/config.yaml"
    )"
    curl --fail --show-error --silent --location \
      --request "POST" \
      --header "Accept: application/vnd.illumina.v3+json" \
      --header "X-API-Key: ${api_key}" \
      --url "https://${__icav2_server_url}/ica/rest/api/tokens" \
      --data ''
  )"

 # Replace token
 ICAV2_ACCESS_TOKEN="${ICAV2_ACCESS_TOKEN}" \
 yq --prettyPrint \
   '
      .access-token = env(ICAV2_ACCESS_TOKEN)
   ' < "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml" > "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml.tmp" && \
   mv "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml.tmp" "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml"
fi

if [[ -z "${ICAV2_BASE_URL-}" ]]; then
  ICAV2_BASE_URL="https://${__icav2_server_url}/ica/rest"
fi

## END CONFIG SETUP ##

## LIST ANALYSIS IDS
page_offset=0
page_size=1000
total_item_count="$( \
  curl \
      --fail \
      --silent \
      --location \
      --request 'GET' \
      --header 'Accept: application/vnd.illumina.v3+json' \
      --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}" \
      --url "${ICAV2_BASE_URL-https://ica.illumina.com/ica/rest}/api/projects/${ICAV2_PROJECT_ID}/analyses?pageOffset=0&pageSize=1" | \
  jq --raw-output '.totalItemCount' \
)"

while :; do
  eval "$( \
    curl \
      --fail \
      --silent \
      --location \
      --request 'GET' \
      --header 'Accept: application/vnd.illumina.v3+json' \
      --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}" \
      --url "${ICAV2_BASE_URL-https://ica.illumina.com/ica/rest}/api/projects/${ICAV2_PROJECT_ID}/analyses?pageOffset=${page_offset}&pageSize=${page_size}&sort=startDate%20desc" | \
    jq --raw-output \
      --arg cols "$(tput cols)" \
      '
        .items |
        (map(.id | length) | max) as $max_id_length |
        (($cols | tonumber) - $max_id_length - 4) as $max_description_length |
        map(
          [
            "printf",
            "%-*s -- %.*s\n",
            $max_id_length, .id,
            $max_description_length, "UserRef: \(.userReference)  Date: \(.startDate)"
          ] |
          @sh
        ) |
        .[]
      '
  )"
    (( page_offset += page_size ))

    if ! (( page_offset < total_item_count )); then
      break
    fi
done
)"
    _icav2_compreply "$param_analysis_id"
}
_icav2_projectanalyses_list-analysis-steps_param_analysis_id_completion() {
    local CURRENT_WORD="${words[$cword]}"
    local param_analysis_id="$(
## CONFIG SETUP ##

# Check tenant
if [[ -n "${ICAV2_TENANT_NAME-}" ]]; then
  :
elif [[ -n "${ICAV2_DEFAULT_TENANT_NAME-}" ]]; then
  ICAV2_TENANT_NAME="${ICAV2_DEFAULT_TENANT_NAME}"
else
  # Get tenant name from cli plugins home
  if [[ -z "${ICAV2_CLI_PLUGINS_HOME}" ]]; then
    # Cannot go any further
    exit
  fi
  if [[ ! -r "${ICAV2_CLI_PLUGINS_HOME}/tenants/default_tenant.txt" ]]; then
    # Cannot go any further
    exit
  fi
  # Read from text file
  ICAV2_TENANT_NAME="$(cat "${ICAV2_CLI_PLUGINS_HOME}/tenants/default_tenant.txt")"
fi

__icav2_server_url="$( \
  yq \
    --unwrapScalar \
    '
      .server-url
    ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/config.yaml"
)"

__icav2_server_url_prefix="$( \
  cut -d'.' -f1 <<< "${__icav2_server_url}"
)"

if [[ -z "${ICAV2_ACCESS_TOKEN-}" ]]; then
  ICAV2_ACCESS_TOKEN="$(yq \
    --unwrapScalar \
    '
      .access-token
    ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/.session.${__icav2_server_url_prefix}.yaml"
  )"
fi


if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  ICAV2_PROJECT_ID="$(yq \
    --unwrapScalar \
      '
        .project-id
      ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/.session.${__icav2_server_url_prefix}.yaml"
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
  ICAV2_ACCESS_TOKEN="$(
    api_key="$( \
      yq \
      --unwrapScalar \
      '
        .x-api-key
      ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/config.yaml"
    )"
    curl --fail --show-error --silent --location \
      --request "POST" \
      --header "Accept: application/vnd.illumina.v3+json" \
      --header "X-API-Key: ${api_key}" \
      --url "https://${__icav2_server_url}/ica/rest/api/tokens" \
      --data ''
  )"

 # Replace token
 ICAV2_ACCESS_TOKEN="${ICAV2_ACCESS_TOKEN}" \
 yq --prettyPrint \
   '
      .access-token = env(ICAV2_ACCESS_TOKEN)
   ' < "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml" > "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml.tmp" && \
   mv "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml.tmp" "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml"
fi

if [[ -z "${ICAV2_BASE_URL-}" ]]; then
  ICAV2_BASE_URL="https://${__icav2_server_url}/ica/rest"
fi

## END CONFIG SETUP ##

## LIST ANALYSIS IDS
page_offset=0
page_size=1000
total_item_count="$( \
  curl \
      --fail \
      --silent \
      --location \
      --request 'GET' \
      --header 'Accept: application/vnd.illumina.v3+json' \
      --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}" \
      --url "${ICAV2_BASE_URL-https://ica.illumina.com/ica/rest}/api/projects/${ICAV2_PROJECT_ID}/analyses?pageOffset=0&pageSize=1" | \
  jq --raw-output '.totalItemCount' \
)"

while :; do
  eval "$( \
    curl \
      --fail \
      --silent \
      --location \
      --request 'GET' \
      --header 'Accept: application/vnd.illumina.v3+json' \
      --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}" \
      --url "${ICAV2_BASE_URL-https://ica.illumina.com/ica/rest}/api/projects/${ICAV2_PROJECT_ID}/analyses?pageOffset=${page_offset}&pageSize=${page_size}&sort=startDate%20desc" | \
    jq --raw-output \
      --arg cols "$(tput cols)" \
      '
        .items |
        (map(.id | length) | max) as $max_id_length |
        (($cols | tonumber) - $max_id_length - 4) as $max_description_length |
        map(
          [
            "printf",
            "%-*s -- %.*s\n",
            $max_id_length, .id,
            $max_description_length, "UserRef: \(.userReference)  Date: \(.startDate)"
          ] |
          @sh
        ) |
        .[]
      '
  )"
    (( page_offset += page_size ))

    if ! (( page_offset < total_item_count )); then
      break
    fi
done
)"
    _icav2_compreply "$param_analysis_id"
}
_icav2_projectdata_create-download-script_param_data_path_completion() {
    local CURRENT_WORD="${words[$cword]}"
    local param_data_path="$(
## CONFIG SETUP ##

# Check tenant
if [[ -n "${ICAV2_TENANT_NAME-}" ]]; then
  :
elif [[ -n "${ICAV2_DEFAULT_TENANT_NAME-}" ]]; then
  ICAV2_TENANT_NAME="${ICAV2_DEFAULT_TENANT_NAME}"
else
  # Get tenant name from cli plugins home
  if [[ -z "${ICAV2_CLI_PLUGINS_HOME}" ]]; then
    # Cannot go any further
    exit
  fi
  if [[ ! -r "${ICAV2_CLI_PLUGINS_HOME}/tenants/default_tenant.txt" ]]; then
    # Cannot go any further
    exit
  fi
  # Read from text file
  ICAV2_TENANT_NAME="$(cat "${ICAV2_CLI_PLUGINS_HOME}/tenants/default_tenant.txt")"
fi

__icav2_server_url="$( \
  yq \
    --unwrapScalar \
    '
      .server-url
    ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/config.yaml"
)"

__icav2_server_url_prefix="$( \
  cut -d'.' -f1 <<< "${__icav2_server_url}"
)"

if [[ -z "${ICAV2_ACCESS_TOKEN-}" ]]; then
  ICAV2_ACCESS_TOKEN="$(yq \
    --unwrapScalar \
    '
      .access-token
    ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/.session.${__icav2_server_url_prefix}.yaml"
  )"
fi


if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  ICAV2_PROJECT_ID="$(yq \
    --unwrapScalar \
      '
        .project-id
      ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/.session.${__icav2_server_url_prefix}.yaml"
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
  ICAV2_ACCESS_TOKEN="$(
    api_key="$( \
      yq \
      --unwrapScalar \
      '
        .x-api-key
      ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/config.yaml"
    )"
    curl --fail --show-error --silent --location \
      --request "POST" \
      --header "Accept: application/vnd.illumina.v3+json" \
      --header "X-API-Key: ${api_key}" \
      --url "https://${__icav2_server_url}/ica/rest/api/tokens" \
      --data ''
  )"

 # Replace token
 ICAV2_ACCESS_TOKEN="${ICAV2_ACCESS_TOKEN}" \
 yq --prettyPrint \
   '
      .access-token = env(ICAV2_ACCESS_TOKEN)
   ' < "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml" > "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml.tmp" && \
   mv "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml.tmp" "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml"
fi

if [[ -z "${ICAV2_BASE_URL-}" ]]; then
  ICAV2_BASE_URL="https://${__icav2_server_url}/ica/rest"
fi

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
        "pageSize": $page_size,
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
  --url "${ICAV2_BASE_URL-https://ica.illumina.com/ica/rest}/api/projects/${ICAV2_PROJECT_ID}/data?${params}" | \
jq --raw-output \
  '
    .items |
    sort_by(.data.details.path | ascii_downcase) |
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

# Check tenant
if [[ -n "${ICAV2_TENANT_NAME-}" ]]; then
  :
elif [[ -n "${ICAV2_DEFAULT_TENANT_NAME-}" ]]; then
  ICAV2_TENANT_NAME="${ICAV2_DEFAULT_TENANT_NAME}"
else
  # Get tenant name from cli plugins home
  if [[ -z "${ICAV2_CLI_PLUGINS_HOME}" ]]; then
    # Cannot go any further
    exit
  fi
  if [[ ! -r "${ICAV2_CLI_PLUGINS_HOME}/tenants/default_tenant.txt" ]]; then
    # Cannot go any further
    exit
  fi
  # Read from text file
  ICAV2_TENANT_NAME="$(cat "${ICAV2_CLI_PLUGINS_HOME}/tenants/default_tenant.txt")"
fi

__icav2_server_url="$( \
  yq \
    --unwrapScalar \
    '
      .server-url
    ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/config.yaml"
)"

__icav2_server_url_prefix="$( \
  cut -d'.' -f1 <<< "${__icav2_server_url}"
)"

if [[ -z "${ICAV2_ACCESS_TOKEN-}" ]]; then
  ICAV2_ACCESS_TOKEN="$(yq \
    --unwrapScalar \
    '
      .access-token
    ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/.session.${__icav2_server_url_prefix}.yaml"
  )"
fi


if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  ICAV2_PROJECT_ID="$(yq \
    --unwrapScalar \
      '
        .project-id
      ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/.session.${__icav2_server_url_prefix}.yaml"
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
  ICAV2_ACCESS_TOKEN="$(
    api_key="$( \
      yq \
      --unwrapScalar \
      '
        .x-api-key
      ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/config.yaml"
    )"
    curl --fail --show-error --silent --location \
      --request "POST" \
      --header "Accept: application/vnd.illumina.v3+json" \
      --header "X-API-Key: ${api_key}" \
      --url "https://${__icav2_server_url}/ica/rest/api/tokens" \
      --data ''
  )"

 # Replace token
 ICAV2_ACCESS_TOKEN="${ICAV2_ACCESS_TOKEN}" \
 yq --prettyPrint \
   '
      .access-token = env(ICAV2_ACCESS_TOKEN)
   ' < "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml" > "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml.tmp" && \
   mv "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml.tmp" "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml"
fi

if [[ -z "${ICAV2_BASE_URL-}" ]]; then
  ICAV2_BASE_URL="https://${__icav2_server_url}/ica/rest"
fi

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
        "pageSize": $page_size,
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
  --url "${ICAV2_BASE_URL-https://ica.illumina.com/ica/rest}/api/projects/${ICAV2_PROJECT_ID}/data?${params}" | \
jq --raw-output \
  '
    .items |
    sort_by(.data.details.path | ascii_downcase) |
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

# Check tenant
if [[ -n "${ICAV2_TENANT_NAME-}" ]]; then
  :
elif [[ -n "${ICAV2_DEFAULT_TENANT_NAME-}" ]]; then
  ICAV2_TENANT_NAME="${ICAV2_DEFAULT_TENANT_NAME}"
else
  # Get tenant name from cli plugins home
  if [[ -z "${ICAV2_CLI_PLUGINS_HOME}" ]]; then
    # Cannot go any further
    exit
  fi
  if [[ ! -r "${ICAV2_CLI_PLUGINS_HOME}/tenants/default_tenant.txt" ]]; then
    # Cannot go any further
    exit
  fi
  # Read from text file
  ICAV2_TENANT_NAME="$(cat "${ICAV2_CLI_PLUGINS_HOME}/tenants/default_tenant.txt")"
fi

__icav2_server_url="$( \
  yq \
    --unwrapScalar \
    '
      .server-url
    ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/config.yaml"
)"

__icav2_server_url_prefix="$( \
  cut -d'.' -f1 <<< "${__icav2_server_url}"
)"

if [[ -z "${ICAV2_ACCESS_TOKEN-}" ]]; then
  ICAV2_ACCESS_TOKEN="$(yq \
    --unwrapScalar \
    '
      .access-token
    ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/.session.${__icav2_server_url_prefix}.yaml"
  )"
fi


if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  ICAV2_PROJECT_ID="$(yq \
    --unwrapScalar \
      '
        .project-id
      ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/.session.${__icav2_server_url_prefix}.yaml"
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
  ICAV2_ACCESS_TOKEN="$(
    api_key="$( \
      yq \
      --unwrapScalar \
      '
        .x-api-key
      ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/config.yaml"
    )"
    curl --fail --show-error --silent --location \
      --request "POST" \
      --header "Accept: application/vnd.illumina.v3+json" \
      --header "X-API-Key: ${api_key}" \
      --url "https://${__icav2_server_url}/ica/rest/api/tokens" \
      --data ''
  )"

 # Replace token
 ICAV2_ACCESS_TOKEN="${ICAV2_ACCESS_TOKEN}" \
 yq --prettyPrint \
   '
      .access-token = env(ICAV2_ACCESS_TOKEN)
   ' < "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml" > "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml.tmp" && \
   mv "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml.tmp" "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml"
fi

if [[ -z "${ICAV2_BASE_URL-}" ]]; then
  ICAV2_BASE_URL="https://${__icav2_server_url}/ica/rest"
fi

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
        "pageSize": $page_size,
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
  --url "${ICAV2_BASE_URL-https://ica.illumina.com/ica/rest}/api/projects/${ICAV2_PROJECT_ID}/data?${params}" | \
jq --raw-output \
  '
    .items |
    sort_by(.data.details.path | ascii_downcase) |
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

# Check tenant
if [[ -n "${ICAV2_TENANT_NAME-}" ]]; then
  :
elif [[ -n "${ICAV2_DEFAULT_TENANT_NAME-}" ]]; then
  ICAV2_TENANT_NAME="${ICAV2_DEFAULT_TENANT_NAME}"
else
  # Get tenant name from cli plugins home
  if [[ -z "${ICAV2_CLI_PLUGINS_HOME}" ]]; then
    # Cannot go any further
    exit
  fi
  if [[ ! -r "${ICAV2_CLI_PLUGINS_HOME}/tenants/default_tenant.txt" ]]; then
    # Cannot go any further
    exit
  fi
  # Read from text file
  ICAV2_TENANT_NAME="$(cat "${ICAV2_CLI_PLUGINS_HOME}/tenants/default_tenant.txt")"
fi

__icav2_server_url="$( \
  yq \
    --unwrapScalar \
    '
      .server-url
    ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/config.yaml"
)"

__icav2_server_url_prefix="$( \
  cut -d'.' -f1 <<< "${__icav2_server_url}"
)"

if [[ -z "${ICAV2_ACCESS_TOKEN-}" ]]; then
  ICAV2_ACCESS_TOKEN="$(yq \
    --unwrapScalar \
    '
      .access-token
    ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/.session.${__icav2_server_url_prefix}.yaml"
  )"
fi


if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  ICAV2_PROJECT_ID="$(yq \
    --unwrapScalar \
      '
        .project-id
      ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/.session.${__icav2_server_url_prefix}.yaml"
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
  ICAV2_ACCESS_TOKEN="$(
    api_key="$( \
      yq \
      --unwrapScalar \
      '
        .x-api-key
      ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/config.yaml"
    )"
    curl --fail --show-error --silent --location \
      --request "POST" \
      --header "Accept: application/vnd.illumina.v3+json" \
      --header "X-API-Key: ${api_key}" \
      --url "https://${__icav2_server_url}/ica/rest/api/tokens" \
      --data ''
  )"

 # Replace token
 ICAV2_ACCESS_TOKEN="${ICAV2_ACCESS_TOKEN}" \
 yq --prettyPrint \
   '
      .access-token = env(ICAV2_ACCESS_TOKEN)
   ' < "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml" > "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml.tmp" && \
   mv "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml.tmp" "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml"
fi

if [[ -z "${ICAV2_BASE_URL-}" ]]; then
  ICAV2_BASE_URL="https://${__icav2_server_url}/ica/rest"
fi

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
        "pageSize": $page_size,
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
  --url "${ICAV2_BASE_URL-https://ica.illumina.com/ica/rest}/api/projects/${ICAV2_PROJECT_ID}/data?${params}" | \
jq --raw-output \
  '
    .items |
    sort_by(.data.details.path | ascii_downcase) |
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

# Check tenant
if [[ -n "${ICAV2_TENANT_NAME-}" ]]; then
  :
elif [[ -n "${ICAV2_DEFAULT_TENANT_NAME-}" ]]; then
  ICAV2_TENANT_NAME="${ICAV2_DEFAULT_TENANT_NAME}"
else
  # Get tenant name from cli plugins home
  if [[ -z "${ICAV2_CLI_PLUGINS_HOME}" ]]; then
    # Cannot go any further
    exit
  fi
  if [[ ! -r "${ICAV2_CLI_PLUGINS_HOME}/tenants/default_tenant.txt" ]]; then
    # Cannot go any further
    exit
  fi
  # Read from text file
  ICAV2_TENANT_NAME="$(cat "${ICAV2_CLI_PLUGINS_HOME}/tenants/default_tenant.txt")"
fi

__icav2_server_url="$( \
  yq \
    --unwrapScalar \
    '
      .server-url
    ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/config.yaml"
)"

__icav2_server_url_prefix="$( \
  cut -d'.' -f1 <<< "${__icav2_server_url}"
)"

if [[ -z "${ICAV2_ACCESS_TOKEN-}" ]]; then
  ICAV2_ACCESS_TOKEN="$(yq \
    --unwrapScalar \
    '
      .access-token
    ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/.session.${__icav2_server_url_prefix}.yaml"
  )"
fi


if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  ICAV2_PROJECT_ID="$(yq \
    --unwrapScalar \
      '
        .project-id
      ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/.session.${__icav2_server_url_prefix}.yaml"
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
  ICAV2_ACCESS_TOKEN="$(
    api_key="$( \
      yq \
      --unwrapScalar \
      '
        .x-api-key
      ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/config.yaml"
    )"
    curl --fail --show-error --silent --location \
      --request "POST" \
      --header "Accept: application/vnd.illumina.v3+json" \
      --header "X-API-Key: ${api_key}" \
      --url "https://${__icav2_server_url}/ica/rest/api/tokens" \
      --data ''
  )"

 # Replace token
 ICAV2_ACCESS_TOKEN="${ICAV2_ACCESS_TOKEN}" \
 yq --prettyPrint \
   '
      .access-token = env(ICAV2_ACCESS_TOKEN)
   ' < "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml" > "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml.tmp" && \
   mv "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml.tmp" "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml"
fi

if [[ -z "${ICAV2_BASE_URL-}" ]]; then
  ICAV2_BASE_URL="https://${__icav2_server_url}/ica/rest"
fi

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
        "pageSize": $page_size,
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
  --url "${ICAV2_BASE_URL-https://ica.illumina.com/ica/rest}/api/projects/${ICAV2_PROJECT_ID}/data?${params}" | \
jq --raw-output \
  '
    .items |
    sort_by(.data.details.path | ascii_downcase) |
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

# Check tenant
if [[ -n "${ICAV2_TENANT_NAME-}" ]]; then
  :
elif [[ -n "${ICAV2_DEFAULT_TENANT_NAME-}" ]]; then
  ICAV2_TENANT_NAME="${ICAV2_DEFAULT_TENANT_NAME}"
else
  # Get tenant name from cli plugins home
  if [[ -z "${ICAV2_CLI_PLUGINS_HOME}" ]]; then
    # Cannot go any further
    exit
  fi
  if [[ ! -r "${ICAV2_CLI_PLUGINS_HOME}/tenants/default_tenant.txt" ]]; then
    # Cannot go any further
    exit
  fi
  # Read from text file
  ICAV2_TENANT_NAME="$(cat "${ICAV2_CLI_PLUGINS_HOME}/tenants/default_tenant.txt")"
fi

__icav2_server_url="$( \
  yq \
    --unwrapScalar \
    '
      .server-url
    ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/config.yaml"
)"

__icav2_server_url_prefix="$( \
  cut -d'.' -f1 <<< "${__icav2_server_url}"
)"

if [[ -z "${ICAV2_ACCESS_TOKEN-}" ]]; then
  ICAV2_ACCESS_TOKEN="$(yq \
    --unwrapScalar \
    '
      .access-token
    ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/.session.${__icav2_server_url_prefix}.yaml"
  )"
fi


if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  ICAV2_PROJECT_ID="$(yq \
    --unwrapScalar \
      '
        .project-id
      ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/.session.${__icav2_server_url_prefix}.yaml"
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
  ICAV2_ACCESS_TOKEN="$(
    api_key="$( \
      yq \
      --unwrapScalar \
      '
        .x-api-key
      ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/config.yaml"
    )"
    curl --fail --show-error --silent --location \
      --request "POST" \
      --header "Accept: application/vnd.illumina.v3+json" \
      --header "X-API-Key: ${api_key}" \
      --url "https://${__icav2_server_url}/ica/rest/api/tokens" \
      --data ''
  )"

 # Replace token
 ICAV2_ACCESS_TOKEN="${ICAV2_ACCESS_TOKEN}" \
 yq --prettyPrint \
   '
      .access-token = env(ICAV2_ACCESS_TOKEN)
   ' < "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml" > "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml.tmp" && \
   mv "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml.tmp" "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml"
fi

if [[ -z "${ICAV2_BASE_URL-}" ]]; then
  ICAV2_BASE_URL="https://${__icav2_server_url}/ica/rest"
fi

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
        "pageSize": $page_size,
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
  --url "${ICAV2_BASE_URL-https://ica.illumina.com/ica/rest}/api/projects/${ICAV2_PROJECT_ID}/data?${params}" | \
jq --raw-output \
  '
    .items |
    sort_by(.data.details.path | ascii_downcase) |
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

# Check tenant
if [[ -n "${ICAV2_TENANT_NAME-}" ]]; then
  :
elif [[ -n "${ICAV2_DEFAULT_TENANT_NAME-}" ]]; then
  ICAV2_TENANT_NAME="${ICAV2_DEFAULT_TENANT_NAME}"
else
  # Get tenant name from cli plugins home
  if [[ -z "${ICAV2_CLI_PLUGINS_HOME}" ]]; then
    # Cannot go any further
    exit
  fi
  if [[ ! -r "${ICAV2_CLI_PLUGINS_HOME}/tenants/default_tenant.txt" ]]; then
    # Cannot go any further
    exit
  fi
  # Read from text file
  ICAV2_TENANT_NAME="$(cat "${ICAV2_CLI_PLUGINS_HOME}/tenants/default_tenant.txt")"
fi

__icav2_server_url="$( \
  yq \
    --unwrapScalar \
    '
      .server-url
    ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/config.yaml"
)"

__icav2_server_url_prefix="$( \
  cut -d'.' -f1 <<< "${__icav2_server_url}"
)"

if [[ -z "${ICAV2_ACCESS_TOKEN-}" ]]; then
  ICAV2_ACCESS_TOKEN="$(yq \
    --unwrapScalar \
    '
      .access-token
    ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/.session.${__icav2_server_url_prefix}.yaml"
  )"
fi


if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  ICAV2_PROJECT_ID="$(yq \
    --unwrapScalar \
      '
        .project-id
      ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/.session.${__icav2_server_url_prefix}.yaml"
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
  ICAV2_ACCESS_TOKEN="$(
    api_key="$( \
      yq \
      --unwrapScalar \
      '
        .x-api-key
      ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/config.yaml"
    )"
    curl --fail --show-error --silent --location \
      --request "POST" \
      --header "Accept: application/vnd.illumina.v3+json" \
      --header "X-API-Key: ${api_key}" \
      --url "https://${__icav2_server_url}/ica/rest/api/tokens" \
      --data ''
  )"

 # Replace token
 ICAV2_ACCESS_TOKEN="${ICAV2_ACCESS_TOKEN}" \
 yq --prettyPrint \
   '
      .access-token = env(ICAV2_ACCESS_TOKEN)
   ' < "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml" > "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml.tmp" && \
   mv "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml.tmp" "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml"
fi

if [[ -z "${ICAV2_BASE_URL-}" ]]; then
  ICAV2_BASE_URL="https://${__icav2_server_url}/ica/rest"
fi

## END CONFIG SETUP ##
eval "$(\
  curl   \
    --fail   \
    --silent   \
    --location   \
    --request 'GET'   \
    --header 'Accept: application/vnd.illumina.v3+json'   \
    --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}"   \
    --url "${ICAV2_BASE_URL-https://ica.illumina.com/ica/rest}/api/projects/${ICAV2_PROJECT_ID}/pipelines" | \
  jq \
    --raw-output \
    --arg cols "$(tput cols)"\
     '
      .items |
      (map(.pipeline.id | length) | max) as $max_pipeline_id |
      (($cols | tonumber) - $max_pipeline_id - 4) as $max_description_length |
      map(
        [
          "printf",
          "%-*s -- %.*s\n",
          $max_pipeline_id, .pipeline.id,
          $max_description_length, "Code: \(.pipeline.code) Date: \(.pipeline.timeCreated) Description: \(.pipeline.description)"
        ] |
        @sh
      )
      |
      .[]
    ' \
)"
)"
    _icav2_compreply "$param_pipeline_id"
}
_icav2_projectpipelines_create-cwl-wes-input-template_option_pipeline_code_completion() {
    local CURRENT_WORD="${words[$cword]}"
    local param_pipeline_code="$(
## CONFIG SETUP ##

# Check tenant
if [[ -n "${ICAV2_TENANT_NAME-}" ]]; then
  :
elif [[ -n "${ICAV2_DEFAULT_TENANT_NAME-}" ]]; then
  ICAV2_TENANT_NAME="${ICAV2_DEFAULT_TENANT_NAME}"
else
  # Get tenant name from cli plugins home
  if [[ -z "${ICAV2_CLI_PLUGINS_HOME}" ]]; then
    # Cannot go any further
    exit
  fi
  if [[ ! -r "${ICAV2_CLI_PLUGINS_HOME}/tenants/default_tenant.txt" ]]; then
    # Cannot go any further
    exit
  fi
  # Read from text file
  ICAV2_TENANT_NAME="$(cat "${ICAV2_CLI_PLUGINS_HOME}/tenants/default_tenant.txt")"
fi

__icav2_server_url="$( \
  yq \
    --unwrapScalar \
    '
      .server-url
    ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/config.yaml"
)"

__icav2_server_url_prefix="$( \
  cut -d'.' -f1 <<< "${__icav2_server_url}"
)"

if [[ -z "${ICAV2_ACCESS_TOKEN-}" ]]; then
  ICAV2_ACCESS_TOKEN="$(yq \
    --unwrapScalar \
    '
      .access-token
    ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/.session.${__icav2_server_url_prefix}.yaml"
  )"
fi


if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  ICAV2_PROJECT_ID="$(yq \
    --unwrapScalar \
      '
        .project-id
      ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/.session.${__icav2_server_url_prefix}.yaml"
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
  ICAV2_ACCESS_TOKEN="$(
    api_key="$( \
      yq \
      --unwrapScalar \
      '
        .x-api-key
      ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/config.yaml"
    )"
    curl --fail --show-error --silent --location \
      --request "POST" \
      --header "Accept: application/vnd.illumina.v3+json" \
      --header "X-API-Key: ${api_key}" \
      --url "https://${__icav2_server_url}/ica/rest/api/tokens" \
      --data ''
  )"

 # Replace token
 ICAV2_ACCESS_TOKEN="${ICAV2_ACCESS_TOKEN}" \
 yq --prettyPrint \
   '
      .access-token = env(ICAV2_ACCESS_TOKEN)
   ' < "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml" > "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml.tmp" && \
   mv "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml.tmp" "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml"
fi

if [[ -z "${ICAV2_BASE_URL-}" ]]; then
  ICAV2_BASE_URL="https://${__icav2_server_url}/ica/rest"
fi

## END CONFIG SETUP ##

## INVOKE PROJECT PIPELINE ##

# No pagination while :; do
eval "$(\
  curl   \
    --fail   \
    --silent   \
    --location   \
    --request 'GET'   \
    --header 'Accept: application/vnd.illumina.v3+json'   \
    --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}"   \
    --url "${ICAV2_BASE_URL-https://ica.illumina.com/ica/rest}/api/projects/${ICAV2_PROJECT_ID}/pipelines" | \
  jq \
    --raw-output \
    --arg cols "$(tput cols)" \
     '
      .items |
      (map(.pipeline.code | length) | max) as $max_pipeline_code |
      (($cols | tonumber) - $max_pipeline_code - 4) as $max_description_length |
      map(
        [
          "printf",
          "%-*s -- %.*s\n",
          $max_pipeline_code, .pipeline.code,
          $max_description_length, "Date=\(.pipeline.timeCreated) Description=\(.pipeline.description)"
        ] |
        @sh
      )
      |
      .[]
    ' \
)"
)"
    _icav2_compreply "$param_pipeline_code"
}
_icav2_projectpipelines_create-cwl-wes-input-template_option_output_parent_folder_path_completion() {
    local CURRENT_WORD="${words[$cword]}"
    local param_output_parent_folder_path="$(
## CONFIG SETUP ##

# Check tenant
if [[ -n "${ICAV2_TENANT_NAME-}" ]]; then
  :
elif [[ -n "${ICAV2_DEFAULT_TENANT_NAME-}" ]]; then
  ICAV2_TENANT_NAME="${ICAV2_DEFAULT_TENANT_NAME}"
else
  # Get tenant name from cli plugins home
  if [[ -z "${ICAV2_CLI_PLUGINS_HOME}" ]]; then
    # Cannot go any further
    exit
  fi
  if [[ ! -r "${ICAV2_CLI_PLUGINS_HOME}/tenants/default_tenant.txt" ]]; then
    # Cannot go any further
    exit
  fi
  # Read from text file
  ICAV2_TENANT_NAME="$(cat "${ICAV2_CLI_PLUGINS_HOME}/tenants/default_tenant.txt")"
fi

__icav2_server_url="$( \
  yq \
    --unwrapScalar \
    '
      .server-url
    ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/config.yaml"
)"

__icav2_server_url_prefix="$( \
  cut -d'.' -f1 <<< "${__icav2_server_url}"
)"

if [[ -z "${ICAV2_ACCESS_TOKEN-}" ]]; then
  ICAV2_ACCESS_TOKEN="$(yq \
    --unwrapScalar \
    '
      .access-token
    ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/.session.${__icav2_server_url_prefix}.yaml"
  )"
fi


if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  ICAV2_PROJECT_ID="$(yq \
    --unwrapScalar \
      '
        .project-id
      ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/.session.${__icav2_server_url_prefix}.yaml"
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
  ICAV2_ACCESS_TOKEN="$(
    api_key="$( \
      yq \
      --unwrapScalar \
      '
        .x-api-key
      ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/config.yaml"
    )"
    curl --fail --show-error --silent --location \
      --request "POST" \
      --header "Accept: application/vnd.illumina.v3+json" \
      --header "X-API-Key: ${api_key}" \
      --url "https://${__icav2_server_url}/ica/rest/api/tokens" \
      --data ''
  )"

 # Replace token
 ICAV2_ACCESS_TOKEN="${ICAV2_ACCESS_TOKEN}" \
 yq --prettyPrint \
   '
      .access-token = env(ICAV2_ACCESS_TOKEN)
   ' < "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml" > "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml.tmp" && \
   mv "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml.tmp" "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml"
fi

if [[ -z "${ICAV2_BASE_URL-}" ]]; then
  ICAV2_BASE_URL="https://${__icav2_server_url}/ica/rest"
fi

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
        "pageSize": $page_size,
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
  --url "${ICAV2_BASE_URL-https://ica.illumina.com/ica/rest}/api/projects/${ICAV2_PROJECT_ID}/data?${params}" | \
jq --raw-output \
  '
    .items |
    sort_by(.data.details.path | ascii_downcase) |
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

# Check tenant
if [[ -n "${ICAV2_TENANT_NAME-}" ]]; then
  :
elif [[ -n "${ICAV2_DEFAULT_TENANT_NAME-}" ]]; then
  ICAV2_TENANT_NAME="${ICAV2_DEFAULT_TENANT_NAME}"
else
  # Get tenant name from cli plugins home
  if [[ -z "${ICAV2_CLI_PLUGINS_HOME}" ]]; then
    # Cannot go any further
    exit
  fi
  if [[ ! -r "${ICAV2_CLI_PLUGINS_HOME}/tenants/default_tenant.txt" ]]; then
    # Cannot go any further
    exit
  fi
  # Read from text file
  ICAV2_TENANT_NAME="$(cat "${ICAV2_CLI_PLUGINS_HOME}/tenants/default_tenant.txt")"
fi

__icav2_server_url="$( \
  yq \
    --unwrapScalar \
    '
      .server-url
    ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/config.yaml"
)"

__icav2_server_url_prefix="$( \
  cut -d'.' -f1 <<< "${__icav2_server_url}"
)"

if [[ -z "${ICAV2_ACCESS_TOKEN-}" ]]; then
  ICAV2_ACCESS_TOKEN="$(yq \
    --unwrapScalar \
    '
      .access-token
    ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/.session.${__icav2_server_url_prefix}.yaml"
  )"
fi


if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  ICAV2_PROJECT_ID="$(yq \
    --unwrapScalar \
      '
        .project-id
      ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/.session.${__icav2_server_url_prefix}.yaml"
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
  ICAV2_ACCESS_TOKEN="$(
    api_key="$( \
      yq \
      --unwrapScalar \
      '
        .x-api-key
      ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/config.yaml"
    )"
    curl --fail --show-error --silent --location \
      --request "POST" \
      --header "Accept: application/vnd.illumina.v3+json" \
      --header "X-API-Key: ${api_key}" \
      --url "https://${__icav2_server_url}/ica/rest/api/tokens" \
      --data ''
  )"

 # Replace token
 ICAV2_ACCESS_TOKEN="${ICAV2_ACCESS_TOKEN}" \
 yq --prettyPrint \
   '
      .access-token = env(ICAV2_ACCESS_TOKEN)
   ' < "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml" > "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml.tmp" && \
   mv "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml.tmp" "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml"
fi

if [[ -z "${ICAV2_BASE_URL-}" ]]; then
  ICAV2_BASE_URL="https://${__icav2_server_url}/ica/rest"
fi

## END CONFIG SETUP ##
eval "$(\
  curl   \
    --fail   \
    --silent   \
    --location   \
    --request 'GET'   \
    --header 'Accept: application/vnd.illumina.v3+json'   \
    --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}"   \
    --url "${ICAV2_BASE_URL-https://ica.illumina.com/ica/rest}/api/projects/${ICAV2_PROJECT_ID}/pipelines" | \
  jq \
    --raw-output \
    --arg cols "$(tput cols)"\
     '
      .items |
      (map(.pipeline.id | length) | max) as $max_pipeline_id |
      (($cols | tonumber) - $max_pipeline_id - 4) as $max_description_length |
      map(
        [
          "printf",
          "%-*s -- %.*s\n",
          $max_pipeline_id, .pipeline.id,
          $max_description_length, "Code: \(.pipeline.code) Date: \(.pipeline.timeCreated) Description: \(.pipeline.description)"
        ] |
        @sh
      )
      |
      .[]
    ' \
)"
)"
    _icav2_compreply "$param_pipeline_id"
}
_icav2_projectpipelines_start-cwl-wes_option_pipeline_code_completion() {
    local CURRENT_WORD="${words[$cword]}"
    local param_pipeline_code="$(
## CONFIG SETUP ##

# Check tenant
if [[ -n "${ICAV2_TENANT_NAME-}" ]]; then
  :
elif [[ -n "${ICAV2_DEFAULT_TENANT_NAME-}" ]]; then
  ICAV2_TENANT_NAME="${ICAV2_DEFAULT_TENANT_NAME}"
else
  # Get tenant name from cli plugins home
  if [[ -z "${ICAV2_CLI_PLUGINS_HOME}" ]]; then
    # Cannot go any further
    exit
  fi
  if [[ ! -r "${ICAV2_CLI_PLUGINS_HOME}/tenants/default_tenant.txt" ]]; then
    # Cannot go any further
    exit
  fi
  # Read from text file
  ICAV2_TENANT_NAME="$(cat "${ICAV2_CLI_PLUGINS_HOME}/tenants/default_tenant.txt")"
fi

__icav2_server_url="$( \
  yq \
    --unwrapScalar \
    '
      .server-url
    ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/config.yaml"
)"

__icav2_server_url_prefix="$( \
  cut -d'.' -f1 <<< "${__icav2_server_url}"
)"

if [[ -z "${ICAV2_ACCESS_TOKEN-}" ]]; then
  ICAV2_ACCESS_TOKEN="$(yq \
    --unwrapScalar \
    '
      .access-token
    ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/.session.${__icav2_server_url_prefix}.yaml"
  )"
fi


if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  ICAV2_PROJECT_ID="$(yq \
    --unwrapScalar \
      '
        .project-id
      ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/.session.${__icav2_server_url_prefix}.yaml"
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
  ICAV2_ACCESS_TOKEN="$(
    api_key="$( \
      yq \
      --unwrapScalar \
      '
        .x-api-key
      ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/config.yaml"
    )"
    curl --fail --show-error --silent --location \
      --request "POST" \
      --header "Accept: application/vnd.illumina.v3+json" \
      --header "X-API-Key: ${api_key}" \
      --url "https://${__icav2_server_url}/ica/rest/api/tokens" \
      --data ''
  )"

 # Replace token
 ICAV2_ACCESS_TOKEN="${ICAV2_ACCESS_TOKEN}" \
 yq --prettyPrint \
   '
      .access-token = env(ICAV2_ACCESS_TOKEN)
   ' < "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml" > "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml.tmp" && \
   mv "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml.tmp" "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml"
fi

if [[ -z "${ICAV2_BASE_URL-}" ]]; then
  ICAV2_BASE_URL="https://${__icav2_server_url}/ica/rest"
fi

## END CONFIG SETUP ##

## INVOKE PROJECT PIPELINE ##

# No pagination while :; do
eval "$(\
  curl   \
    --fail   \
    --silent   \
    --location   \
    --request 'GET'   \
    --header 'Accept: application/vnd.illumina.v3+json'   \
    --header "Authorization: Bearer ${ICAV2_ACCESS_TOKEN}"   \
    --url "${ICAV2_BASE_URL-https://ica.illumina.com/ica/rest}/api/projects/${ICAV2_PROJECT_ID}/pipelines" | \
  jq \
    --raw-output \
    --arg cols "$(tput cols)" \
     '
      .items |
      (map(.pipeline.code | length) | max) as $max_pipeline_code |
      (($cols | tonumber) - $max_pipeline_code - 4) as $max_description_length |
      map(
        [
          "printf",
          "%-*s -- %.*s\n",
          $max_pipeline_code, .pipeline.code,
          $max_description_length, "Date=\(.pipeline.timeCreated) Description=\(.pipeline.description)"
        ] |
        @sh
      )
      |
      .[]
    ' \
)"
)"
    _icav2_compreply "$param_pipeline_code"
}
_icav2_projectpipelines_start-cwl-wes_option_output_parent_folder_path_completion() {
    local CURRENT_WORD="${words[$cword]}"
    local param_output_parent_folder_path="$(
## CONFIG SETUP ##

# Check tenant
if [[ -n "${ICAV2_TENANT_NAME-}" ]]; then
  :
elif [[ -n "${ICAV2_DEFAULT_TENANT_NAME-}" ]]; then
  ICAV2_TENANT_NAME="${ICAV2_DEFAULT_TENANT_NAME}"
else
  # Get tenant name from cli plugins home
  if [[ -z "${ICAV2_CLI_PLUGINS_HOME}" ]]; then
    # Cannot go any further
    exit
  fi
  if [[ ! -r "${ICAV2_CLI_PLUGINS_HOME}/tenants/default_tenant.txt" ]]; then
    # Cannot go any further
    exit
  fi
  # Read from text file
  ICAV2_TENANT_NAME="$(cat "${ICAV2_CLI_PLUGINS_HOME}/tenants/default_tenant.txt")"
fi

__icav2_server_url="$( \
  yq \
    --unwrapScalar \
    '
      .server-url
    ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/config.yaml"
)"

__icav2_server_url_prefix="$( \
  cut -d'.' -f1 <<< "${__icav2_server_url}"
)"

if [[ -z "${ICAV2_ACCESS_TOKEN-}" ]]; then
  ICAV2_ACCESS_TOKEN="$(yq \
    --unwrapScalar \
    '
      .access-token
    ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/.session.${__icav2_server_url_prefix}.yaml"
  )"
fi


if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  ICAV2_PROJECT_ID="$(yq \
    --unwrapScalar \
      '
        .project-id
      ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/.session.${__icav2_server_url_prefix}.yaml"
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
  ICAV2_ACCESS_TOKEN="$(
    api_key="$( \
      yq \
      --unwrapScalar \
      '
        .x-api-key
      ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/config.yaml"
    )"
    curl --fail --show-error --silent --location \
      --request "POST" \
      --header "Accept: application/vnd.illumina.v3+json" \
      --header "X-API-Key: ${api_key}" \
      --url "https://${__icav2_server_url}/ica/rest/api/tokens" \
      --data ''
  )"

 # Replace token
 ICAV2_ACCESS_TOKEN="${ICAV2_ACCESS_TOKEN}" \
 yq --prettyPrint \
   '
      .access-token = env(ICAV2_ACCESS_TOKEN)
   ' < "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml" > "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml.tmp" && \
   mv "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml.tmp" "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml"
fi

if [[ -z "${ICAV2_BASE_URL-}" ]]; then
  ICAV2_BASE_URL="https://${__icav2_server_url}/ica/rest"
fi

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
        "pageSize": $page_size,
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
  --url "${ICAV2_BASE_URL-https://ica.illumina.com/ica/rest}/api/projects/${ICAV2_PROJECT_ID}/data?${params}" | \
jq --raw-output \
  '
    .items |
    sort_by(.data.details.path | ascii_downcase) |
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

# Check tenant
if [[ -n "${ICAV2_TENANT_NAME-}" ]]; then
  :
elif [[ -n "${ICAV2_DEFAULT_TENANT_NAME-}" ]]; then
  ICAV2_TENANT_NAME="${ICAV2_DEFAULT_TENANT_NAME}"
else
  # Get tenant name from cli plugins home
  if [[ -z "${ICAV2_CLI_PLUGINS_HOME}" ]]; then
    # Cannot go any further
    exit
  fi
  if [[ ! -r "${ICAV2_CLI_PLUGINS_HOME}/tenants/default_tenant.txt" ]]; then
    # Cannot go any further
    exit
  fi
  # Read from text file
  ICAV2_TENANT_NAME="$(cat "${ICAV2_CLI_PLUGINS_HOME}/tenants/default_tenant.txt")"
fi

__icav2_server_url="$( \
  yq \
    --unwrapScalar \
    '
      .server-url
    ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/config.yaml"
)"

__icav2_server_url_prefix="$( \
  cut -d'.' -f1 <<< "${__icav2_server_url}"
)"

if [[ -z "${ICAV2_ACCESS_TOKEN-}" ]]; then
  ICAV2_ACCESS_TOKEN="$(yq \
    --unwrapScalar \
    '
      .access-token
    ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/.session.${__icav2_server_url_prefix}.yaml"
  )"
fi


if [[ -z "${ICAV2_PROJECT_ID-}" ]]; then
  ICAV2_PROJECT_ID="$(yq \
    --unwrapScalar \
      '
        .project-id
      ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/.session.${__icav2_server_url_prefix}.yaml"
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
  ICAV2_ACCESS_TOKEN="$(
    api_key="$( \
      yq \
      --unwrapScalar \
      '
        .x-api-key
      ' < "${ICAV2_CLI_PLUGINS_HOME}/tenants/${ICAV2_TENANT_NAME}/config.yaml"
    )"
    curl --fail --show-error --silent --location \
      --request "POST" \
      --header "Accept: application/vnd.illumina.v3+json" \
      --header "X-API-Key: ${api_key}" \
      --url "https://${__icav2_server_url}/ica/rest/api/tokens" \
      --data ''
  )"

 # Replace token
 ICAV2_ACCESS_TOKEN="${ICAV2_ACCESS_TOKEN}" \
 yq --prettyPrint \
   '
      .access-token = env(ICAV2_ACCESS_TOKEN)
   ' < "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml" > "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml.tmp" && \
   mv "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml.tmp" "${HOME}/.icav2/.session.${__icav2_server_url_prefix}.yaml"
fi

if [[ -z "${ICAV2_BASE_URL-}" ]]; then
  ICAV2_BASE_URL="https://${__icav2_server_url}/ica/rest"
fi

## END CONFIG SETUP ##

ATTRIBUTE_NAME="name"

## INVOKE PROJECT FUNCTION ##

curl \
  --fail --silent --location \
  --request "GET" \
  --url "${ICAV2_BASE_URL-https://ica.illumina.com/ica/rest}/api/projects?includeHiddenProjects=false&pageSize=100" \
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
_icav2_tenants_enter_param_tenant_name_completion() {
    local CURRENT_WORD="${words[$cword]}"
    local param_tenant_name="$(
find "${ICAV2_CLI_PLUGINS_HOME}/tenants/" -mindepth 1 -maxdepth 1 -type d -exec basename {} \;
)"
    _icav2_compreply "$param_tenant_name"
}
_icav2_tenants_set-default-project_param_tenant_name_completion() {
    local CURRENT_WORD="${words[$cword]}"
    local param_tenant_name="$(
find "${ICAV2_CLI_PLUGINS_HOME}/tenants/" -mindepth 1 -maxdepth 1 -type d -exec basename {} \;
)"
    _icav2_compreply "$param_tenant_name"
}
_icav2_tenants_set-default-tenant_param_tenant_name_completion() {
    local CURRENT_WORD="${words[$cword]}"
    local param_tenant_name="$(
find "${ICAV2_CLI_PLUGINS_HOME}/tenants/" -mindepth 1 -maxdepth 1 -type d -exec basename {} \;
)"
    _icav2_compreply "$param_tenant_name"
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


complete -o default -o nosort -F _icav2 icav2


# ICAv2 CLI Plugins

> I'm sorry I couldn't think of a superhero pun for this repository

This plugin contains the following extensions to the icav2 cli. 

Much of this is inspired from the [ica-ica-lazy repo][ica_ica_lazy].  

Autocompletion features are courtesy of the [app-spec project][app_spec_project]

Please refer to [wiki page][wiki_page] for [installation][installation_wiki_page] and [usage][wiki_page].

## Features

### icav2 projectdata extensions

#### icav2 projectdata ls

> Inspired by [gds-ls][gds_ls]  
> List all files and folders in directory

* Autocompletion: :white_check_mark:

See more in [project data wiki][project_data_wiki_ls]

#### icav2 projectdata view

> Inspired by [gds-view][gds_view]  
> View a file in stdout

* Autocompletion: :white_check_mark:

See more in [project data wiki][project_data_wiki_view]

#### icav2 projectdata s3-sync-download

> Inspired by [gds-sync-download][gds_sync_download]  
> Sync files from icav2 to local project with an aws s3 sync command

* Autocompletion :white_check_mark:

See more in [project data wiki][project_data_wiki_s3_sync_download]

#### icav2 projectdata s3-sync-upload

> Inspired by [gds-sync-upload][gds_sync_upload]  
> Sync files from local to icav2 with an aws s3 sync command

* Autocompletion :white_check_mark:

See more in [project data wiki][project_data_wiki_s3_sync_upload]

### icav2 projectpipelines extensions

#### icav2 projectpipelines create-workflow-from-zip

> Create a pipeline in an icav2 project from a zipped up CWL directory

* Autocompletion :white_check_mark:

See more in [project pipelines wiki][project_pipelines_create_workflow_from_zip]

#### icav2 projectpipelines create-workflow-from-github-release

> Create a pipeline in an icav2 project from a GitHub release

* Autocompletion :white_check_mark:

See more in [project pipelines wiki][project_pipelines_create_workflow_from_github_release]


#### icav2 projectpipelines create-wes-input-template

> Inspired by [cwl-ica-create-workflow-submission-template][cwl_ica_create_workflow_submission_template]
> Create a WES input template ready for launch in ICAv2

* Autocompletion :white_check_mark:

See more in [project pipelines wiki][project_pipelines_create_wes_input_template]


#### icav2 projectpipelines start-cwl-wes

> Launch a CWL Workflow from a wes template

* Autocompletion :white_check_mark:

See more in [project pipelines wiki][project_pipelines_start_cwl_wes]


### icav2 projectanalyses extensions

#### icav2 projectanalyses get-cwl-analysis-input-json 

> Collect inputjson used by an analyses

* Autocompletion :white_check_mark:

See more in [project analyses wiki][project_analyses_wiki_get_cwl_anlysis_input_json]


#### icav2 projectanalyses get-cwl-analysis-output-json

> Collect outputjson used by an analyses

* Autocompletion :white_check_mark:

See more in [project analyses wiki][project_analyses_wiki_get_cwl_anlysis_output_json]

#### icav2 projectanalyses list-analysis-steps

> Inspired by [ica-get-tasks-from-workflow-history][ica_get_tasks_from_workflow_history]  
> Collect all steps in a workflow run, useful for debugging


* Autocompletion :white_check_mark:

See more in [project analyses wiki][project_analyses_wiki_list_analyses_steps]

#### icav2 projectanalyses get-analysis-step-logs

> Get logs of a step id for a workflow

* Autocompletion :white_check_mark:

See more in [project analyses wiki][project_analyses_wiki_get_analyses_step_logs]

## Coming soon

### icav2 projectdata find

> Inspired by [gds-find][gds_find]  
> Mimics the gnutls find command with --maxdepth, --mindepth, --type and --name parameters available

* Autocompletion: :construction:

### icav2 projectdata create-download-script

> Inspired by [gds-create-download-script][gds_create_download_script]    
> Create a download script with a list of encoded presigned urls for a given directory.

* Autocompletion :construction:

[gds_ls]: https://github.com/umccr/ica-ica-lazy/wiki/Data_Traversal#gds-ls
[gds_view]: https://github.com/umccr/ica-ica-lazy/wiki/Data_Traversal#gds-view
[gds_sync_download]: https://github.com/umccr/ica-ica-lazy/wiki/Syncing_Directories#gds-sync-download
[gds_sync_upload]: https://github.com/umccr/ica-ica-lazy/wiki/Syncing_Directories#gds-sync-upload
[gds_find]: https://github.com/umccr/ica-ica-lazy/wiki/Data_Traversal#gds-find
[gds_create_download_script]: https://github.com/umccr/ica-ica-lazy/wiki/Syncing_Directories#gds-create-download-script

[app_spec_project]: https://github.com/perlpunk/App-Spec-p5
[ica_ica_lazy]: https://github.com/umccr/ica-ica-lazy

[ica_get_tasks_from_workflow_history]: https://github.com/umccr/ica-ica-lazy/wiki/Extras#ica-get-tasks-from-workflow-history

[cwl_ica_create_workflow_submission_template]: https://github.com/umccr/cwl-ica/wiki/Stories#step-3-replicating-the-workflow

[wiki_page]: https://github.com/umccr/icav2-cli-plugins/wiki

[installation_wiki_page]: https://github.com/umccr/icav2-cli-plugins/wiki#installation

[project_data_wiki_ls]: https://github.com/umccr/icav2-cli-plugins/wiki/ProjectData#ls

[project_data_wiki_view]: https://github.com/umccr/icav2-cli-plugins/wiki/ProjectData#view
[project_data_wiki_s3_sync_download]: https://github.com/umccr/icav2-cli-plugins/wiki/ProjectData#s3-sync-commands
[project_data_wiki_s3_sync_upload]: https://github.com/umccr/icav2-cli-plugins/wiki/ProjectData#s3-sync-commands

[project_pipelines_create_workflow_from_zip]: https://github.com/umccr/icav2-cli-plugins/wiki/ProjectPipelines#create-cwl-workflow-from-zip
[project_pipelines_create_workflow_from_github_release]: https://github.com/umccr/icav2-cli-plugins/wiki/ProjectPipelines#create-cwl-workflow-from-github-release
[project_pipelines_create_wes_input_template]: https://github.com/umccr/icav2-cli-plugins/wiki/ProjectPipelines#create-cwl-wes-input-template
[project_pipelines_start_cwl_wes]: https://github.com/umccr/icav2-cli-plugins/wiki/ProjectPipelines#start-cwl-wes

[project_analyses_wiki_get_cwl_anlysis_input_json]: https://github.com/umccr/icav2-cli-plugins/wiki/ProjectAnalyses#get-cwl-analysis-input-json
[project_analyses_wiki_get_cwl_anlysis_output_json]: https://github.com/umccr/icav2-cli-plugins/wiki/ProjectAnalyses#get-cwl-analysis-output-json
[project_analyses_wiki_list_analyses_steps]: https://github.com/umccr/icav2-cli-plugins/wiki/ProjectAnalyses#list-analysis-steps
[project_analyses_wiki_get_analyses_step_logs]: https://github.com/umccr/icav2-cli-plugins/wiki/ProjectAnalyses#get-analysis-step-logs

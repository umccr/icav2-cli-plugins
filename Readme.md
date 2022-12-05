# ICAv2 CLI Plugins

> I'm sorry I couldn't think of a superhero pun for this repository

This plugin contains the following extensions to the icav2 cli. 

Much of this is inspired from the [ica-ica-lazy repo][ica_ica_lazy].  

Autocompletion features are courtesy of the [app-spec project][app_spec_project]

## Installation

Run the install script and follow the prompts.  

You will need to place a few lines in your .rc file as specified in the installation script.  

You can validate your installation by running 

```
type icav2 | head -n1
```

Which should return 
```text
icav2 is a function
```

## Features

### icav2 projectdata extensions

#### icav2 projectdata ls

> Inspired by [gds-ls][gds_ls]
> List all files and folders in directory

* Autocompletion: :white_check_mark:

#### icav2 projectdata view

> Inspired by [gds-view][gds_view]
> View a file in stdout


#### icav2 projectdata s3-sync-download

> Inspired by [gds-sync-download][gds_sync_download]
> Sync files from icav2 to local project with an aws s3 sync command

* Autocompletion :white_check_mark:

#### icav2 projectdata s3-sync-upload

> Inspired by [gds-sync-upload][gds_sync_upload]
> Sync files from local to icav2 with an aws s3 sync command

* Autocompletion :white_check_mark:

### icav2 projectpipelines extensions

#### icav2 projectpipelines create-workflow-from-zip

> Create a pipeline in an icav2 project from a zipped up CWL directory

* Autocompletion :white_check_mark:


#### icav2 projectpipelines create-wes-input-template

> Inspired by [cwl-ica-create-workflow-submission-template][cwl_ica_create_workflow_submission_template]
> Create a WES input template ready for launch in ICAv2

* Autocompletion :white_check_mark:

#### icav2 projectpipelines start-cwl-wes

> Launch a CWL Workflow from a wes template

* Autocompletion :white_check_mark:


### icav2 projectanalyses extensions

#### icav2 projectanalyses list-analysis-steps

> Inspired by [ica-get-tasks-from-workflow-history][ica_get_tasks_from_workflow_history]
> Collect all steps in a workflow run, useful for debugging

* Autocompletion :white_check_mark:

#### icav2 projectanalyses get-cwl-analysis-input-json 

> Collect inputjson used by an analyses

* Autocompletion :white_check_mark:

#### icav2 projectanalyses get-cwl-analysis-output-json

> Collect outputjson used by an analyses

* Autocompletion :white_check_mark:

#### icav2 projectanalyses get-analysis-step-logs

> Get logs of a step id for a workflow

* Autocompletion :white_check_mark:


## Coming soon

### icav2 projectdata find

> Inspired by [gds-find][gds_find]
> Mocks the gnutls find command with --maxdepth, --mindepth, --type and --name parameters available

* Autocompletion: :construction:

[gds_ls]: https://github.com/umccr/ica-ica-lazy/wiki/Data_Traversal#gds-ls
[gds_view]: https://github.com/umccr/ica-ica-lazy/wiki/Data_Traversal#gds-view
[gds_sync_download]: https://github.com/umccr/ica-ica-lazy/wiki/Syncing_Directories#gds-sync-download
[gds_sync_upload]: https://github.com/umccr/ica-ica-lazy/wiki/Syncing_Directories#gds-sync-upload

[app_spec_project]: https://github.com/perlpunk/App-Spec-p5
[ica_ica_lazy]: https://github.com/umccr/ica-ica-lazy

[ica_get_tasks_from_workflow_history]: https://github.com/umccr/ica-ica-lazy/wiki/Extras#ica-get-tasks-from-workflow-history

[cwl_ica_create_workflow_submission_template]: https://github.com/umccr/cwl-ica/wiki/Stories#step-3-replicating-the-workflow
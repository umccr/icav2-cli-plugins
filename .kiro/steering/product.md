# Product Overview

icav2-cli-plugins is a Python CLI extension that adds subcommands to the Illumina Connected Analytics v2 (ICAv2) command-line interface. It is developed by UMCCR (University of Melbourne Centre for Cancer Research).

## Purpose

Extends the official `icav2` CLI with higher-level operations for:

- **Bundles** – create, manage, release, and attach data/pipelines to bundles
- **Project Data** – ls, find, view, cp, mv, mkdir, s3-sync-download/upload, create-download-script
- **Project Pipelines** – create workflows from zip/GitHub, generate WES input templates, launch CWL workflows, release pipelines
- **Project Analyses** – inspect analysis I/O JSON, list/log steps, generate Gantt charts
- **Tenants** – register, list, enter, and set defaults for multi-tenant environments
- **Pipelines** – general pipeline management utilities

## Key Concepts

- Wraps the ICAv2 REST API via the `wrapica` library and `libica` SDK
- Supports CWL and Nextflow pipeline formats
- Provides shell autocompletion (bash and zsh) via the app-spec project
- Installs into `~/.icav2-cli-plugins/` with its own Python virtualenv
- Operates within a project context set via environment variables or session files

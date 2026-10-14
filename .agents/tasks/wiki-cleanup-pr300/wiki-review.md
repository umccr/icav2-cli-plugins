# Wiki cleanup for PR #300 tenant→profile migration and GIF removal

The change cleans up the `icav2-cli-plugins.wiki` to reflect PR #300: it rewrites context-handling docs around the profile-based configuration (`icav2 configure set/list/generate-keys`), marks `icav2 projects enter` as deprecated and non-functional, renames the CWL/WES command set (`create-cwl-workflow-*` → `create-cwl-pipeline-*`, `create-cwl-wes-input-template` → `create-wes-input-template`, `start-cwl-wes` → `start-wes`) along with their flags, and removes embedded GIFs in favour of reproducible command + output examples. Most of the GIF removal and command rewrites are strong and verified against the live subcommand docstrings. The gap is completeness: three command pages still carry `### GIF Example` headings and TOC links that were left untouched.

Watch for: residual `### GIF Example` sections and `#gif-example` TOC links in `ProjectData.md`, `ProjectAnalyses.md`, and `Bundles.md` (confirmed) — the user asked to remove *all* GIFs, and these vestigial GIF scaffolding sections remain. A local wiki commit sits ahead of `origin/master` (confirmed), though nothing is pushed.

**Verdict**: NEEDS_CHANGES

## High-level view

The profile migration is the core of the change and it is handled well. `ContextHandling.md` is rewritten from a `projects enter` wrapper guide into a profile-resolution guide, with a precedence table (`--profile` > `ICAV2_PROFILE` > `ICAV2_TENANT_NAME` backward-compat > `[default]`) that matches the resolution order described for #300. The deprecation claim is accurate: the plugin's `projects` SuperCommand no longer implements `enter`, so stating it is "no longer functional" is correct.

The command and flag renames are verified against the real post-#300 docstrings, not guessed from GIF filenames. `create-wes-input-template`, `start-wes`, `create-cwl-pipeline-from-github-release`, and the flag moves (`--pipeline`, `--analysis-output`, `--create-analysis-json-output-path`) all match `src/icav2_cli_plugins/subcommands/projectpipelines/`. The stale `autocompletion/specs/icav2.yaml` still shows the old `create-cwl-wes-input-template` name, but the docstrings are the ground truth and the wiki followed them correctly.

GIF removal is complete where it was done: `ProjectPipelines.md`, `ContextHandling.md`, `Home.md`, and `pipeline-deployments-via-github.md` have every GIF embed and `:construction:` GIF-Example placeholder replaced or deleted, TOC entries updated, and real reproducible examples with representative console output added. All nine `.gif` binaries and the `gifs/` directory are gone. But `ProjectData.md`, `ProjectAnalyses.md`, and `Bundles.md` were never touched and still contain `### GIF Example` headings plus matching `#gif-example` TOC anchors — twelve such references in total. These were `:construction:` placeholders rather than live images, so nothing renders broken, but they are exactly the GIF scaffolding the user asked to remove.

Legacy tenant handling is correct. No page instructs users to adopt the tenant workflow as the supported path; the only remaining `tenants` instruction lives in a clearly-labelled "Migrating from legacy tenants" section in `Configuration.md`, framed as a migration-from path with the profile system marked recommended. Other `tenant` mentions are deliberate conceptual context (the AWS org/account analogy, bundles belonging to a tenant, the `ICAV2_TENANT_NAME` backward-compat note). Sidebar and heading structure are preserved, and the source repo is clean.

<details>
<summary>Issues (3)</summary>

1. **Residual GIF Example sections** — `ProjectData.md` (2), `ProjectAnalyses.md` (2), and `Bundles.md` (7) still have `### GIF Example` headings plus matching `#gif-example` TOC links. Remove the headings and TOC entries; where a reproducible example adds value (e.g. the s3-sync and ls flows), replace with a real command + output as was done on the other pages.
2. **projectdata cp/mkdir undocumented** — `cp` and `mkdir` exist as real subcommands in source but `ProjectData.md` documents neither. Informational: outside the explicit #300 asks (GIF removal + tenant cleanup), so non-blocking, but worth capturing if the page is being revised anyway.
3. **Local wiki commit ahead of origin** — commit `9213afa` sits on `master` unpushed. Not pushed so the public wiki is unaffected, but the task constraint was "no commits to the wiki"; confirm whether this commit should be reset back into the working tree.

</details>

<details>
<summary>Details</summary>

## Residual GIF Example scaffolding on three pages

`ProjectPipelines.md` shows how the removal was meant to go: `### GIF Example` headings and their `:construction:`/`![...](gifs/...)` bodies were deleted, the TOC `#gif-example` anchors removed, and in their place reproducible examples were added — `create-wes-input-template` with a filled-in launch YAML, and `start-wes` with a command that captures `analysis_id` plus representative log output.

Three pages did not get this treatment:

```
ProjectData.md      line 232  ### GIF Example (:construction:)   + TOC #gif-example
ProjectData.md      line 409  ### GIF Example (:construction:)   + TOC #gif-example-1
ProjectAnalyses.md  line  83  ### GIF Example (:construction:)   + TOC #gif-example
ProjectAnalyses.md  line 118  ### GIF Example (:construction:)   + TOC #gif-example-1
Bundles.md          7x        ### GIF Example (:construction:)   + 7x TOC #gif-example*
```

These were already `:construction:` placeholders in `origin/master` (verified with `git show origin/master:commands/ProjectData.md`), and the matching `gifs/` binaries they would have referenced were never embedded in these three markdown files. So nothing renders as a broken image. The problem is faithfulness to the request: the user said "remove all GIFs ... replace these with reproducible code examples", and twelve `### GIF Example` headings with their TOC anchors survive. At minimum the headings and TOC links should be dropped; the s3-sync-upload/download and `ls` flows in `ProjectData.md` are good candidates for the same reproducible-example treatment the pipelines page received.

## Profile migration and projects-enter deprecation

`ContextHandling.md` is reframed from a `projects enter` wrapper page into a profile guide: how context resolves (per-invocation profile load from `~/.icav2-cli-plugins/config` instead of mutating a shared session file), how to configure a profile, and how to select one per-command (`--profile`) or per-terminal (`ICAV2_PROFILE`). The resolution-precedence table reads `--profile` > `ICAV2_PROFILE` > `ICAV2_TENANT_NAME` (backward-compat, treated as a profile name) > `[default]`, with the note that `ICAV2_ACCESS_TOKEN`/`ICAV2_PROJECT_ID`/`ICAV2_BASE_URL` override the selected profile's values.

The deprecation statement is accurate: `src/icav2_cli_plugins/subcommands/projects/__init__.py` now only handles `create`/`get`/`list` (delegated to the native binary) and no longer implements or masks `enter`, so "deprecated and no longer functional" is a correct description of the plugin behaviour. The profile commands documented — `configure set`, `configure list`, `configure generate-keys` — all exist in `src/icav2_cli_plugins/subcommands/configure/`, and the generate-keys/encryption detail matches `configure_generate_keys.py`.

## Command and flag renames verified against docstrings

Every rename in `ProjectPipelines.md` and `pipeline-deployments-via-github.md` was checked against the live docstrings rather than inferred from old GIF filenames:

- `create-cwl-pipeline-from-github-release` — matches `create_cwl_pipeline_from_github_release.py`.
- `create-wes-input-template` with `--pipeline`, `--analysis-output`, `--ica-logs`, `--cache`, `--analysis-storage`, `--idempotency-key`, `--output-template-yaml-path` — matches `create_wes_input_template.py` usage/options.
- `start-wes` with `--launch-yaml`, `--pipeline`, `--analysis-output`, `--create-analysis-json-output-path`, `--json` — matches `launch_wes.py`.
- The main-usage command list on the pipelines page was expanded to match `projectpipelines/__init__.py` (adds the nextflow create variants, `update`, `download`, `release`).

The `autocompletion/specs/icav2.yaml` app-spec is stale (still lists `create-cwl-wes-input-template`), but the task designates the subcommand docstrings as ground truth and the wiki tracks the docstrings, so this is correct.

## Legacy tenant handling kept as migration context only

No page instructs users to use `tenants register`/`enter`/`init` as a supported workflow. The remaining tenant references are:

- `Configuration.md` "Migrating from legacy tenants" — frames `icav2 tenants init` strictly as the thing you migrated *from*, marks the profile system recommended, documents the `ICAV2_TENANT_NAME`→profile backward-compat lookup, and notes the legacy directory is not auto-removed.
- `Installation.md` — migration prompt note, legacy directory preserved.
- `ContextHandling.md` — the AWS org/account analogy explaining that a profile sits at the project level, not the tenant level; deliberate conceptual context.
- `stories/creating-bundles-in-icav2.md` — "Bundles ... belong to a single ICAv2 tenant", a factual statement about bundle scope.

This satisfies the requirement that the profile workflow is the single supported path and any tenant mention is deliberate migration/conceptual context. (The source still ships a `tenants` subcommand group, so these references are not describing removed functionality.)

## Constraints: markdown, structure, source, commits

Changes are markdown-only. The `_Sidebar.md` links to pages (not removed anchors) and was correctly left unmodified. Heading hierarchy is preserved on the rewritten pages. The source repo (`icav2-cli-plugins`) is clean — untouched. The nine `.gif` binaries and the `gifs/` directory are deleted; `find . -name '*.gif'` returns nothing.

One deviation from the stated constraints: the wiki has a local commit `9213afa` ("docs: mark 'projects enter' deprecated and document profile-based context") sitting ahead of `origin/master`. The bulk of the current cleanup (the GIF removal in `ProjectPipelines.md` and the `Configuration.md`/`Home.md`/`ContextHandling.md`/bundles-story tweaks) is in the uncommitted working tree, which does respect the no-commit constraint for the main deliverable. Nothing is pushed, so the public wiki is unaffected, but the committed state should be confirmed against the "no commits to the wiki" constraint.

</details>

<details>
<summary>File map</summary>

- `commands/ProjectPipelines.md` — (uncommitted) full rewrite: command/flag renames, GIF Example sections removed, reproducible examples added, main-usage list synced to source.
- `commands/ContextHandling.md` — (committed + uncommitted) reframed from `projects enter` wrapper to profile guide; resolution precedence table; "Switching between contexts" with AWS analogy.
- `Home.md` — (committed + uncommitted) profile note, `projects enter` deprecated, command rename.
- `Configuration.md` — (uncommitted) profile-per-context wording; legacy-tenant migration section retained as migration-from guidance.
- `stories/pipeline-deployments-via-github.md` — (committed) profile-based context setup, command/flag renames.
- `stories/creating-bundles-in-icav2.md` — (uncommitted) tenant wording clarified as factual bundle scope.
- `gifs/*.gif` (9 files) — (committed) deleted; `gifs/` directory removed.
- `commands/ProjectData.md`, `commands/ProjectAnalyses.md`, `commands/Bundles.md` — NOT changed; still carry `### GIF Example` headings and `#gif-example` TOC links (the finding).

Full diff: `git -C /home/alexiswl/GitHub/UMCCR/icav2-cli-plugins.wiki diff origin/master` plus the uncommitted working tree.

</details>

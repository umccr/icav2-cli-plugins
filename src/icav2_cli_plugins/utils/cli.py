#!/usr/bin/env python3

"""icav2-cli-plugins ::: a suite of additional cli additions to extend the existing icav2 cli

Usage:
    icav2-cli-plugins [options] <command> [<subcommand>] [<args>...]

Options:
    --profile <profile_name>            Select a named profile from the config file
    --debug                             Set the log level to debug

Command:

    help                                Print help and exit
    version                             Print version and exit

    ######################
    Configure
    ######################
    configure                           Manage CLI profiles and configuration

    ######################
    Bundles
    ######################
    bundles                             Collection of subfunctions relating to bundles

    ######################
    Pipelines
    ######################
    pipelines                           Collection of subfunctions relating to pipelines

    ######################
    Project Analyses
    ######################
    projectanalyses                     Collection of subfunctions relating to analyses on project pipeline

    ##########################
    Project Data
    ##########################
    projectdata                         Collection of subfunctions relating to accessing project data

    ##########################
    Project Pipelines
    ##########################
    projectpipelines                    Collection of subfunctions relating to creating / deploying pipelines

    ######################
    Tenants
    #######################
    tenants                             Collection of tenant handling scripts
"""

# Only lightweight imports at module level — no heavy libraries
from docopt import docopt
import sys
import os

# Version is just a string in utils/__init__.py (no heavy imports triggered)
from . import version
from .logger import set_basic_logger

# Set logger
logger = set_basic_logger()

# Lazy import mapping: command name -> module path
COMMAND_MODULE_MAP = {
    "bundles": "icav2_cli_plugins.subcommands.bundles",
    "pipelines": "icav2_cli_plugins.subcommands.pipelines",
    "projectanalyses": "icav2_cli_plugins.subcommands.projectanalyses",
    "projectdata": "icav2_cli_plugins.subcommands.projectdata",
    "projectpipelines": "icav2_cli_plugins.subcommands.projectpipelines",
    "tenants": "icav2_cli_plugins.subcommands.tenants",
    "configure": "icav2_cli_plugins.subcommands.configure",
}

# Maps command names to their class name in the module
COMMAND_CLASS_MAP = {
    "bundles": "Bundles",
    "pipelines": "Pipelines",
    "projectanalyses": "ProjectAnalyses",
    "projectdata": "ProjectData",
    "projectpipelines": "ProjectPipelines",
    "tenants": "Tenants",
}


def lazy_import_command(cmd: str):
    """Import the command module only when dispatched."""
    import importlib
    module_path = COMMAND_MODULE_MAP.get(cmd)
    if module_path is None:
        return None
    return importlib.import_module(module_path)


def _resolve_profile_and_token(cli_profile):
    """
    Resolve the active profile and ensure a valid access token.

    Returns a ResolvedConfig with access_token populated.
    """
    from .profile_resolver import ProfileResolver
    from .token_manager import TokenManager, validate_env_token
    from .globals import CONFIG_FILE_PATH, CACHE_DIR

    # Resolve profile configuration
    resolver = ProfileResolver(config_path=CONFIG_FILE_PATH, cli_profile=cli_profile)
    config = resolver.resolve()

    # If ICAV2_ACCESS_TOKEN is set in env, validate it (hard error if invalid)
    env_token = os.environ.get("ICAV2_ACCESS_TOKEN", "")
    if env_token:
        # validate_env_token exits with error if token is expired/malformed
        validated_token = validate_env_token(env_token)
        config.access_token = validated_token
    else:
        # No env token — use TokenManager to get/refresh from API key
        if config.api_key is None:
            print(
                f"Error: Profile '{config.profile_name}' has no API key configured. "
                f"Run 'icav2 configure set' to set one.",
                file=sys.stderr,
            )
            sys.exit(1)

        token_mgr = TokenManager(profile_name=config.profile_name, cache_dir=CACHE_DIR)
        try:
            config.access_token = token_mgr.get_valid_token(
                api_key=config.api_key, base_url=config.base_url
            )
        except RuntimeError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    return config


def _set_environment_from_config(config):
    """
    Set environment variables from the resolved configuration so that
    plugin subcommands and the _icav2 binary can use them.
    """
    if config.access_token:
        os.environ["ICAV2_ACCESS_TOKEN"] = config.access_token
    if config.base_url:
        os.environ["ICAV2_BASE_URL"] = config.base_url
    if config.project_id:
        os.environ["ICAV2_PROJECT_ID"] = config.project_id


def _delegate_to_icav2(args, config=None):
    """
    Execute the bundled _icav2 binary with environment variables
    set from the resolved configuration.

    Uses os.execve to replace the current process with the _icav2 binary.
    """
    from .globals import LOCAL_BINARY_PATH

    if not LOCAL_BINARY_PATH.exists():
        print(
            f"Error: _icav2 binary not found at {LOCAL_BINARY_PATH}. "
            f"Please re-run the installer to set it up.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Set environment for the subprocess
    env = os.environ.copy()
    if config is not None:
        if config.access_token:
            env["ICAV2_ACCESS_TOKEN"] = config.access_token
        if config.base_url:
            env["ICAV2_BASE_URL"] = config.base_url
        if config.project_id:
            env["ICAV2_PROJECT_ID"] = config.project_id

    binary_path = str(LOCAL_BINARY_PATH)
    argv = [binary_path] + args
    os.execve(binary_path, argv, env)


def _dispatch():
    """Parse global args and dispatch to the appropriate handler."""

    # This variable comprises both the subcommand AND the args
    global_args: dict = docopt(__doc__, sys.argv[1:], version=version, options_first=True)

    # Handle all global args we've set
    if global_args["--debug"]:
        logger.info("Setting logging level to 'DEBUG'")
        logger.setLevel(level="DEBUG")
    else:
        logger.setLevel(level="INFO")

    # Extract the --profile flag (highest precedence for profile selection)
    cli_profile = global_args.get("--profile")

    cmd = global_args['<command>']
    subcmd = global_args.get("<subcommand>")

    # Build command_argv for subcommand dispatch
    command_argv = [cmd]
    if subcmd is not None:
        command_argv.append(subcmd)
    command_argv.extend(global_args["<args>"])

    # Handle help and version early — no heavy imports needed
    if cmd == "help":
        print(__doc__)
        sys.exit(0)
    elif cmd == "version":
        print(version)
        sys.exit(0)
    elif cmd == "configure":
        # Configure commands work without a valid token (they set up config)
        from ..subcommands.configure import get_configure_subcommand
        if subcmd is None:
            print("Usage: icav2 configure <set|list>")
            print("\nAvailable configure subcommands: set, list")
            sys.exit(0)
        configure_module = get_configure_subcommand(subcmd)
        if configure_module is None:
            print(f'Unknown configure subcommand: "{subcmd}"')
            print("Available configure subcommands: set, list")
            sys.exit(1)
        # Get the command class from the configure submodule
        command_class = configure_module.Command
        subcommand_obj = command_class(command_argv)
        subcommand_obj()
    elif cmd in COMMAND_MODULE_MAP:
        # Plugin command — resolve profile and token first
        config = _resolve_profile_and_token(cli_profile)
        _set_environment_from_config(config)

        # Lazy import the plugin command module
        module = lazy_import_command(cmd)
        class_name = COMMAND_CLASS_MAP[cmd]
        subcommand_class = getattr(module, class_name)
        subcommand_obj = subcommand_class(command_argv)
        subcommand_obj()
    else:
        # Unknown command — delegate to the local _icav2 binary
        config = _resolve_profile_and_token(cli_profile)

        # Build the full argument list to pass to _icav2
        delegate_args = [cmd]
        if subcmd is not None:
            delegate_args.append(subcmd)
        delegate_args.extend(global_args["<args>"])

        _delegate_to_icav2(delegate_args, config)


def main():
    # If only the bare command is written, append help so documentation shows
    if len(sys.argv) == 1:
        sys.argv.append('help')
    try:
        _dispatch()
    except KeyboardInterrupt:
        pass

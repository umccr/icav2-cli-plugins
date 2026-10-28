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
    Projects
    ######################
    projects                            Collection of subfunctions relating to projects

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
    Jobs
    ######################
    jobs                                Collection of subfunctions relating to jobs

    ######################
    Regions
    ######################
    regions                             Collection of subfunctions relating to regions

    ######################
    Storage Bundles
    ######################
    storagebundles                      Collection of subfunctions relating to storage bundles

    ######################
    Storage Configurations
    ######################
    storageconfigurations               Collection of subfunctions relating to storage configurations

    ######################
    Tokens
    ######################
    tokens                              Collection of subfunctions relating to access tokens

    ######################
    Tenants
    #######################
    tenants                             (deprecated - use 'configure' instead)
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
    "projects": "icav2_cli_plugins.subcommands.projects",
    "projectanalyses": "icav2_cli_plugins.subcommands.projectanalyses",
    "projectdata": "icav2_cli_plugins.subcommands.projectdata",
    "projectpipelines": "icav2_cli_plugins.subcommands.projectpipelines",
    "configure": "icav2_cli_plugins.subcommands.configure",
    "jobs": "icav2_cli_plugins.subcommands.jobs",
    "regions": "icav2_cli_plugins.subcommands.regions",
    "storagebundles": "icav2_cli_plugins.subcommands.storagebundles",
    "storageconfigurations": "icav2_cli_plugins.subcommands.storageconfigurations",
    "tokens": "icav2_cli_plugins.subcommands.tokens",
}

# Maps command names to their class name in the module
COMMAND_CLASS_MAP = {
    "bundles": "Bundles",
    "pipelines": "Pipelines",
    "projects": "Projects",
    "projectanalyses": "ProjectAnalyses",
    "projectdata": "ProjectData",
    "projectpipelines": "ProjectPipelines",
    "jobs": "Jobs",
    "regions": "Regions",
    "storagebundles": "StorageBundles",
    "storageconfigurations": "StorageConfigurations",
    "tokens": "Tokens",
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
    from .globals import CONFIG_FILE_PATH
    from pathlib import Path

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

        token_mgr = TokenManager(
            profile_name=config.profile_name,
            config_path=CONFIG_FILE_PATH,
            private_key_path=(
                Path(config.encryption_private_key)
                if config.encryption_private_key
                else None
            ),
            public_key_path=(
                Path(config.encryption_public_key)
                if config.encryption_public_key
                else None
            ),
        )
        try:
            config.access_token = token_mgr.get_valid_token(
                api_key=config.api_key,
                base_url=config.base_url,
                cached_token=config.cached_access_token,
            )
        except RuntimeError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    # If project_id is not set but project_name is, resolve it via the API
    if not config.project_id and config.project_name:
        from .config_helpers import get_project_id_from_project_name_curl
        try:
            config.project_id = get_project_id_from_project_name_curl(
                base_url=config.base_url,
                project_name=config.project_name,
                access_token=config.access_token,
            )
        except (ValueError, Exception) as e:
            print(
                f"Error: Could not resolve project name '{config.project_name}' to a project ID. "
                f"Check that the project exists and your token has access.",
                file=sys.stderr,
            )
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
    Also passes --server-url explicitly since the _icav2 binary may not
    read ICAV2_BASE_URL from the environment.
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

    # Inject --server-url flag since the _icav2 binary expects hostname via flag
    extra_flags = []
    base_url = env.get("ICAV2_BASE_URL", "")
    if base_url:
        from urllib.parse import urlparse
        parsed = urlparse(base_url)
        if parsed.hostname:
            extra_flags = ["--server-url", parsed.hostname]

    binary_path = str(LOCAL_BINARY_PATH)
    argv = [binary_path] + args + extra_flags
    os.execve(binary_path, argv, env)


def _get_icav2_binary_version():
    """
    Return the version string reported by the bundled _icav2 binary,
    or None if the binary cannot be found or run.
    """
    import subprocess
    from .globals import LOCAL_BINARY_PATH

    if not LOCAL_BINARY_PATH.exists():
        return None

    try:
        result = subprocess.run(
            [str(LOCAL_BINARY_PATH), "version"],
            capture_output=True,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return None

    output = (result.stdout or result.stderr or "").strip()
    if not output:
        return None

    # The binary prints e.g. "Version: 2.47.0, BuildNumber: 97, BuildTime: ..."
    # Pull out just the version number if we can, otherwise return the raw line.
    first_line = output.splitlines()[0].strip()
    if first_line.lower().startswith("version:"):
        return first_line.split(":", 1)[1].split(",")[0].strip()
    return first_line


def _print_version():
    """Print the versions of icav2-cli-plugins and its key dependencies."""
    from importlib.metadata import version as _pkg_version, PackageNotFoundError

    def _safe_pkg_version(pkg_name):
        try:
            return _pkg_version(pkg_name)
        except PackageNotFoundError:
            return "unknown"

    icav2_bin_version = _get_icav2_binary_version()

    print(f"icav2-cli-plugins: {version}")
    print(f"icav2 (binary):    {icav2_bin_version if icav2_bin_version else 'not found'}")
    print(f"wrapica:           {_safe_pkg_version('wrapica')}")
    print(f"libica:            {_safe_pkg_version('libica')}")


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
        _print_version()
        sys.exit(0)
    elif cmd == "configure":
        # Configure commands work without a valid token (they set up config)
        from ..subcommands.configure import get_configure_subcommand, CONFIGURE_SUBCOMMANDS

        def _print_configure_help():
            print("Usage: icav2 configure <subcommand> [<args>...]")
            print("")
            print("Available subcommands:")
            print("  set             Interactively configure a profile")
            print("  list            Display all configured profiles")
            print("  generate-keys   Generate RSA key pair for API key encryption")
            sys.exit(0)

        if subcmd is None or subcmd in ("--help", "-h", "help"):
            _print_configure_help()
        configure_module = get_configure_subcommand(subcmd)
        if configure_module is None:
            print(f'Unknown configure subcommand: "{subcmd}"')
            print("")
            print("Available subcommands: " + ", ".join(CONFIGURE_SUBCOMMANDS.keys()))
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

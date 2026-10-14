"""
Tests for the migrated central pipeline coercion path in subcommands/__init__.py.

These tests verify that the shared ``DocOptArg.coerce_magical_value`` method resolves a
pipeline argument via the new wrapica ``name``/``version`` resolvers
(``coerce_pipeline_id_or_name_to_pipeline_obj`` /
``coerce_pipeline_id_or_name_to_project_pipeline_obj``) rather than the deprecated
``_code`` helpers, and that:

  * a UUID string is still routed through the resolver and returned unchanged;
  * a non-UUID string is resolved by pipeline NAME (not code);
  * importing ``icav2_cli_plugins.subcommands`` does not eagerly import wrapica.

We use subprocess isolation (mirroring ``tests/test_deferred_imports.py``) so the test does
not require a live ICAv2 session - the wrapica submodules imported lazily inside
``coerce_magical_value`` are replaced by lightweight stub modules in ``sys.modules`` before
the method is exercised.
"""

import subprocess
import sys
import textwrap


# A stub-wrapica harness injected into a fresh interpreter. It installs fake ``wrapica.*``
# modules so that the lazy imports inside ``coerce_magical_value`` succeed without a live
# session, then drives the pipeline-coercion branch and reports which resolver was called.
STUB_HARNESS = textwrap.dedent("""\
    import sys
    import types

    calls = []

    def _make_module(name, **attrs):
        mod = types.ModuleType(name)
        for attr_key, attr_value in attrs.items():
            setattr(mod, attr_key, attr_value)
        sys.modules[name] = mod
        return mod

    # Sentinels for the union type aliases used in the arg_type comparisons.
    class PipelineType:
        pass

    class ProjectPipelineType:
        pass

    # Resolved pipeline objects are non-str sentinels (as a real pipeline object would be),
    # so later ``isinstance(value, str)`` branches in coerce_magical_value do not re-fire.
    class _ResolvedPipeline:
        def __init__(self, source):
            self.source = source

    # Fake resolver callables that record the symbol invoked and the args passed.
    def coerce_pipeline_id_or_name_to_pipeline_obj(value, pipeline_version=None):
        calls.append(("pipeline_name", value, pipeline_version))
        return _ResolvedPipeline(value)

    def coerce_pipeline_id_or_name_to_project_pipeline_obj(value, pipeline_version=None):
        calls.append(("project_pipeline_name", value, pipeline_version))
        return _ResolvedPipeline(value)

    # Guard rails - the deprecated code helpers must never be referenced.
    def _forbidden(*args, **kwargs):
        raise AssertionError("deprecated pipeline-code resolver was called")

    # Minimal stand-ins for every wrapica submodule imported inside coerce_magical_value.
    _make_module(
        "wrapica.bundle",
        Bundle=type("Bundle", (), {}),
        coerce_bundle_id_or_name_to_bundle_obj=_forbidden,
    )
    _make_module(
        "wrapica.data",
        Data=type("Data", (), {}),
        coerce_data_id_path_or_icav2_uri_to_data_obj=_forbidden,
    )
    # AnalysisStorageSize is tested with ``value in AnalysisStorageSize`` further down the
    # method (an enum membership check in the real code), so the stub needs ``__contains__``.
    class _AnalysisStorageSizeMeta(type):
        def __contains__(cls, item):
            return False

    class AnalysisStorageSize(metaclass=_AnalysisStorageSizeMeta):
        pass

    _make_module("wrapica.enums", AnalysisStorageSize=AnalysisStorageSize)
    _make_module(
        "wrapica.pipelines",
        PipelineType=PipelineType,
        coerce_pipeline_id_or_name_to_pipeline_obj=coerce_pipeline_id_or_name_to_pipeline_obj,
    )
    _make_module(
        "wrapica.project_data",
        ProjectData=type("ProjectData", (), {}),
        coerce_data_id_uri_or_path_to_project_data_obj=_forbidden,
        is_folder_id_format=lambda value: False,
    )
    _make_module(
        "wrapica.project",
        Project=type("Project", (), {}),
        coerce_project_id_or_name_to_project_obj=_forbidden,
        get_project_id=lambda: "project-id",
    )
    _make_module(
        "wrapica.project_analysis",
        AnalysisStorageType=type("AnalysisStorageType", (), {}),
        AnalysisType=type("AnalysisType", (), {}),
        coerce_analysis_id_or_user_reference_to_analysis_obj=_forbidden,
    )
    _make_module(
        "wrapica.project_pipelines",
        ProjectPipelineType=ProjectPipelineType,
        coerce_analysis_storage_id_or_size_to_analysis_storage=_forbidden,
        coerce_pipeline_id_or_name_to_project_pipeline_obj=coerce_pipeline_id_or_name_to_project_pipeline_obj,
    )
    _make_module(
        "wrapica.region",
        Region=type("Region", (), {}),
        coerce_region_id_or_city_name_to_region_obj=_forbidden,
    )
    _make_module(
        "wrapica.user",
        User=type("User", (), {}),
        coerce_user_id_or_name_to_user_obj=_forbidden,
    )

    # Fail loudly if any deprecated code symbol is even looked up on the pipeline modules.
    for _mod_name in ("wrapica.pipelines", "wrapica.project_pipelines"):
        _mod = sys.modules[_mod_name]
        setattr(_mod, "coerce_pipeline_id_or_code_to_pipeline_obj", _forbidden)
        setattr(_mod, "coerce_pipeline_id_or_code_to_project_pipeline_obj", _forbidden)

    from icav2_cli_plugins.subcommands import DocOptArg
""")


def _run_harness(body: str, timeout: int = 60) -> subprocess.CompletedProcess:
    script = STUB_HARNESS + textwrap.dedent(body)
    return subprocess.run(
        [sys.executable, "-c", script],
        capture_output=True,
        text=True,
        timeout=timeout,
    )


class TestPipelineCoercion:
    """The central coercion path resolves pipelines by id-or-name, never by code."""

    def test_uuid_routes_through_name_resolver_unchanged(self):
        """A UUID string is handed to the new resolver and returned unchanged."""
        result = _run_harness("""\
            uuid_value = "12345678-1234-1234-1234-123456789abc"
            arg = DocOptArg(cli_arg_keys=["--pipeline"])
            arg.arg_type = PipelineType
            returned = arg.coerce_magical_value("pipeline", uuid_value)

            assert calls == [("pipeline_name", uuid_value, None)], calls
            assert returned.source == uuid_value, returned
            print("PASS")
        """)
        assert result.returncode == 0, (
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_non_uuid_routes_through_name_resolver(self):
        """A non-UUID string is resolved by pipeline name (version defaults to None/latest)."""
        result = _run_harness("""\
            name_value = "my_pipeline_name"
            arg = DocOptArg(cli_arg_keys=["--pipeline"])
            arg.arg_type = PipelineType
            returned = arg.coerce_magical_value("pipeline", name_value)

            assert calls == [("pipeline_name", name_value, None)], calls
            assert returned.source == name_value, returned
            print("PASS")
        """)
        assert result.returncode == 0, (
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_project_pipeline_routes_through_project_name_resolver(self):
        """A ProjectPipelineType arg routes through the project-pipeline name resolver."""
        result = _run_harness("""\
            name_value = "my_project_pipeline"
            arg = DocOptArg(cli_arg_keys=["--pipeline"])
            arg.arg_type = ProjectPipelineType
            returned = arg.coerce_magical_value("pipeline", name_value)

            assert calls == [("project_pipeline_name", name_value, None)], calls
            assert returned.source == name_value, returned
            print("PASS")
        """)
        assert result.returncode == 0, (
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

    def test_subcommands_import_does_not_load_wrapica(self):
        """Importing the subcommands package must not eagerly import wrapica."""
        script = textwrap.dedent("""\
            import sys
            import icav2_cli_plugins.subcommands

            loaded = [
                key for key in sys.modules
                if key == "wrapica" or key.startswith("wrapica.")
            ]
            if loaded:
                print(f"FAIL: wrapica imported at load time: {loaded}", file=sys.stderr)
                sys.exit(1)
            print("PASS")
            sys.exit(0)
        """)
        result = subprocess.run(
            [sys.executable, "-c", script],
            capture_output=True,
            text=True,
            timeout=30,
        )
        assert result.returncode == 0, (
            f"stdout: {result.stdout}\nstderr: {result.stderr}"
        )

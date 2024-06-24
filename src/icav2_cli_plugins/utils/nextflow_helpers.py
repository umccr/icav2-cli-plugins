#!/usr/bin/env python
from pathlib import Path

# Utils
from .logger import get_logger
from .subprocess_handler import run_subprocess_proc

# Set logger
logger = get_logger()


def download_nf_core_pipeline_to_zip(
        pipeline_name: str,
        pipeline_revision: str,
        output_zip_path: Path
) -> None:
    """
    Download Nextflow pipeline to zip file
    """
    nfcore_download_return_code, nfcore_download_stdout, nfcore_download_stderr = run_subprocess_proc(
        [
            "nf-core",
            "download",
            pipeline_name,
            "--revision", pipeline_revision,
            "--compress", "zip",
            "--outdir", output_zip_path.with_suffix("").name
        ],
        cwd=str(output_zip_path.parent),
        capture_output=True
    )

    if nfcore_download_return_code != 0:
        logger.error(f"Error downloading Nextflow pipeline: {nfcore_download_stderr}")
        raise ChildProcessError



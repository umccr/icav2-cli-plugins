#!/usr/bin/env python

"""
Helper functions for getting information from a release

"""
import json
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict

from bs4 import BeautifulSoup

from utils.subprocess_handler import run_subprocess_proc

from utils.logger import get_logger

from markdown import markdown

logger = get_logger()


def download_zipped_workflow_from_github_release(repo: str, tag_name: str, output_path: Path):
    """
    Using gh, collect the zip asset and
    :param repo:
    :param tag_name:
    :param output_path:
    :return:
    """
    if not output_path.parent.is_dir():
        logger.error(f"output path variable '{output_path}' parent directory does not exist")
        raise NotADirectoryError

    with TemporaryDirectory() as tmp_dir:
        gh_zip_download_returncode, gh_zip_download_stdout, gh_zip_download_stderr = run_subprocess_proc(
            [
                "gh", "release", "download",
                "--repo", repo,
                "--pattern", "*.zip",
                tag_name
            ]
        )

        if not gh_zip_download_returncode == 0:
            logger.error("Failed to download zip file")
            logger.error(f"Stdout was {gh_zip_download_stdout}")
            logger.error(f"Stderr was {gh_zip_download_stderr}")
            raise ChildProcessError

        try:
            zip_path: Path = next(Path(tmp_dir).glob("*.zip"))
            shutil.copy2(zip_path, output_path)
        except StopIteration:
            logger.error("Could not find zip file")
            raise FileNotFoundError


def get_release_markdown_file_doc(repo: str, tag_name: str, output_path: Path):
    """
    From a release, collect the body of the release as a markdown file
    :param repo:
    :param tag_name:
    :param output_path: 
    :return:
    """
    if not output_path.parent.is_dir():
        logger.error(f"output path variable '{output_path}' parent directory does not exist")
        raise NotADirectoryError

    gh_markdown_download_returncode, gh_markdown_download_stdout, gh_markdown_download_stderr = run_subprocess_proc(
        [
            "gh", "release", "view",
            "--repo", repo,
            "--json", "body",
            tag_name
        ]
    )

    if not gh_markdown_download_returncode == 0:
        logger.error("Failed to download markdown")
        logger.error(f"Stdout was {gh_markdown_download_stdout}")
        logger.error(f"Stderr was {gh_markdown_download_stderr}")
        raise ChildProcessError

    # Read from stdout
    body_output = json.loads(gh_markdown_download_stdout)["body"]

    with open(output_path, "w") as md_h:
        md_h.write(body_output)


def get_release_markdown_file_doc_as_html(repo: str, tag_name: str, output_path: Path):
    """
    Get the release markdown file doc as a html object via bs4
    :param repo:
    :param tag_name:
    :return:
    """
    if not output_path.parent.is_dir():
        logger.error(f"Could not write to output path parameter '{output_path}' parent does not exist")
        raise NotADirectoryError

    with TemporaryDirectory() as tmpdir:
        # Download the markdown doc
        output_md_path = Path(tmpdir) / "tmp.md"
        get_release_markdown_file_doc(
            repo=repo,
            tag_name=tag_name,
            output_path=output_md_path
        )

        # Write output html
        with open(output_md_path, 'r') as md_h, open(output_path, "w") as html_h:
            html_h.write(markdown(md_h.read()))


def get_inputs_template_from_html_doc(html_doc: Path) -> Dict:
    """
    Get the inputs template from the html documentation
    :param html_doc:
    :return:
    """

    with open(html_doc, "r") as html_h:
        soup = BeautifulSoup(html_h.read())

    # Inputs template
    inputs_template_header = soup.find("h2", text="Inputs Template")

    inputs_template_text = inputs_template_header.find("code").text

    return json.loads(inputs_template_text)


def get_overrides_template_from_html_doc(html_doc) -> Dict:
    """
    Get the overrides template from the html documentation
    :param html_doc:
    :return:
    """

    with open(html_doc, "r") as html_h:
        soup = BeautifulSoup(html_h.read())

    # Inputs template
    overrides_template_header = soup.find("h2", text="Overrides Template")

    overrides_template_zipped_workflow = overrides_template_header.find("h3", text="Zipped workflow")

    overrides_template_text = overrides_template_zipped_workflow.find("code").text

    return json.loads(overrides_template_text)


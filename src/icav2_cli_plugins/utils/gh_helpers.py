#!/usr/bin/env python

"""
Helper functions for getting information from a release

"""
import json
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, Tuple
from urllib.parse import urlparse

from bs4 import BeautifulSoup

from .globals import GITHUB_RELEASE_REPO_TAG_REGEX_MATCH
from .subprocess_handler import run_subprocess_proc

from .logger import get_logger

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
                "--dir", tmp_dir,
                "--pattern", "*.zip",
                tag_name
            ],
            capture_output=True
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


def get_release_repo_and_tag_from_release_url(release_url: str) -> Tuple[str, str]:
    release_path = urlparse(release_url).path
    release_regex_match = GITHUB_RELEASE_REPO_TAG_REGEX_MATCH.fullmatch(release_path)
    if release_regex_match is None:
        logger.error("Could not get release repo and tag from release url")
        raise ValueError

    # Ensure we only got two matches
    try:
        assert len(release_regex_match.groups()) == 2
    except AssertionError:
        logger.error(f"Expected 2 matches for release regex match but got {len(release_regex_match.groups())}")
        logger.error(f"Groups were {release_regex_match.groups()}")
        raise AssertionError

    return release_regex_match.groups()


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
        ],
        capture_output=True
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

        with open(output_path, "w") as output_html_h:
            pandoc_returncode, _, pandoc_stderr = run_subprocess_proc(
                [
                    "pandoc",
                    "--from", "markdown",
                    "--to", "html",
                    output_md_path
                ],
                stdout=output_html_h,
                stderr=True
            )


def get_inputs_template_from_html_doc(html_doc: Path) -> Dict:
    """
    Get the inputs template from the html documentation
    :param html_doc:
    :return:
    """

    with open(html_doc, "r") as html_h:
        soup = BeautifulSoup(html_h.read(), features="lxml")

    # Inputs template
    inputs_template_header = soup.find("h2", text="Inputs Template")

    inputs_template_text = inputs_template_header.find_next("code").text

    return json.loads(inputs_template_text)


def get_overrides_template_from_html_doc(html_doc) -> Dict:
    """
    Get the overrides template from the html documentation
    :param html_doc:
    :return:
    """

    with open(html_doc, "r") as html_h:
        soup = BeautifulSoup(html_h.read(), features="lxml")

    # Inputs template
    overrides_template_header = soup.find("h2", text="Overrides Template")

    # We want the code for the zipped workflow
    overrides_template_zipped_workflow = overrides_template_header.find_next("h3", text="Zipped workflow")

    overrides_template_text = overrides_template_zipped_workflow.find_next("code").text

    return json.loads(overrides_template_text)


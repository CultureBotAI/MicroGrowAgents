"""Download resources from YAML file."""

from pathlib import Path

from kghub_downloader.download_utils import download_from_yaml
from kghub_downloader.model import DownloadOptions


def download(
    yaml_file: str, output_dir: str, snippet_only: bool = False, ignore_cache: bool = False
) -> None:
    """
    Download data files from list of URLs.

    Download based on config (default: download.yaml)
    into data directory (default: data/raw).

    :param yaml_file: A string pointing to the yaml file utilized to facilitate the downloading of data.
    :param output_dir: A string pointing to the location to download data to.
    :param snippet_only: Downloads only the first 5 kB of the source, for testing and file checks.
    :param ignore_cache: Ignore cache and download files even if they exist [false]
    :return: None.
    """
    # Create download options
    download_options = DownloadOptions(
        snippet_only=snippet_only,
        ignore_cache=ignore_cache,
    )

    download_from_yaml(
        yaml_file=yaml_file,
        output_dir=output_dir,
        download_options=download_options,
    )

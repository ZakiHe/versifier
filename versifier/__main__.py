import logging
from functools import partial
from typing import List

import click

from versifier.core import PoetryExtension

from .config import Config

logger = logging.getLogger(__name__)


@click.group()
def cli() -> None:
    logging.basicConfig(level=logging.INFO)


@cli.command()
@click.option("--poetry-path", default="poetry", help="path to poetry")
@click.option("-r", "--requirements", multiple=True, default=[], help="requirements files")
@click.option("-d", "--dev-requirements", multiple=True, default=[], help="dev requirements files")
@click.option("-e", "--exclude", multiple=True, default=[], help="exclude packages")
def requirements_to_poetry(
    poetry_path: str,
    requirements: List[str],
    dev_requirements: List[str],
    exclude: List[str],
) -> None:
    ext = PoetryExtension(poetry_path=poetry_path)
    ext.add_from_requirements_txt(
        requirements,
        dev_requirements,
        exclude,
    )


@cli.command()
@click.option("-o", "--output", default="", help="output file")
@click.option("--poetry-path", default="poetry", help="path to poetry")
@click.option("--exclude-specifiers", is_flag=True, help="exclude specifiers")
@click.option("--include-comments", is_flag=True, help="include comments")
@click.option("-d", "--include-dev-requirements", is_flag=True, help="include dev requirements")
@click.option("-E", "--extra-requirements", multiple=True, default=[], help="extra requirements")
@click.option("-m", "--markers", multiple=True, default=[], help="markers")
def poetry_to_requirements(
    output: str,
    poetry_path: str,
    exclude_specifiers: bool,
    include_comments: bool,
    include_dev_requirements: bool,
    extra_requirements: List[str],
    markers: List[str],
) -> None:
    config = Config.from_toml()
    ext = PoetryExtension(poetry_path=poetry_path)
    fn = partial(
        ext.export_to_requirements_txt,
        include_specifiers=not exclude_specifiers,
        include_comments=include_comments,
        exclude=config.private_packages,
        include_dev_requirements=include_dev_requirements,
        extra_requirements=extra_requirements,
        markers=markers,
    )

    if output == "":
        fn(callback=print)

    else:
        with open(output, "w") as f:
            fn(callback=lambda line: f.write(line + "\n"))


@cli.command()
@click.option("--output", default=".", help="output dir")
@click.option("--poetry-path", default="poetry", help="path to poetry")
@click.option("-E", "--extra-requirements", multiple=True, default=[], help="extra requirements")
@click.option("--exclude-file-patterns", multiple=True, default=[], help="exclude files")
def extract_private_packages(
    output: str,
    poetry_path: str,
    extra_requirements: List[str],
    exclude_file_patterns: List[str],
) -> None:
    config = Config.from_toml()
    ext = PoetryExtension(poetry_path=poetry_path)

    ext.extract_packages(
        output_dir=output,
        packages=config.private_packages,
        extra_requirements=extra_requirements,
        exclude_file_patterns=exclude_file_patterns,
    )


@cli.command()
@click.option("--output", default=".", help="output dir")
@click.option("--poetry-path", default="poetry", help="path to poetry")
@click.option("--nuitka-path", default="nuitka3", help="path to nuitka3")
@click.option("-E", "--extra-requirements", multiple=True, default=[], help="extra requirements")
def compile_private_packages(
    output: str,
    poetry_path: str,
    nuitka_path: str,
    extra_requirements: List[str],
) -> None:
    config = Config.from_toml()
    ext = PoetryExtension(poetry_path=poetry_path, nuitka_path=nuitka_path)
    ext.compile_packages(
        output_dir=output,
        packages=config.private_packages,
        extra_requirements=extra_requirements,
    )


if __name__ == "__main__":
    cli()

import logging
from functools import partial
from tempfile import TemporaryDirectory
from typing import List, Optional

import click

from versifier import core

from .compiler import Compiler
from .config import get_private_packages_from_pyproject, list_all_packages
from .poetry import Poetry

logger = logging.getLogger(__name__)


@click.group()
def cli() -> None:
    logging.basicConfig(level=logging.INFO)


@cli.command()
@click.option("--poetry-path", default="poetry", help="path to poetry")
@click.option("-r", "--requirements", multiple=True, default=[], help="requirements files")
@click.option("-d", "--dev-requirements", multiple=True, default=[], help="dev requirements files")
@click.option("-e", "--exclude", multiple=True, default=[], help="exclude packages")
@click.option("--add-only", is_flag=True, help="add only")
def requirements_to_poetry(
    poetry_path: str,
    requirements: List[str],
    dev_requirements: List[str],
    exclude: List[str],
    add_only: bool,
) -> None:
    poetry = Poetry(poetry_path)
    if not add_only:
        poetry.init_if_needed()

    ext = core.DependencyManager(poetry)
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
@click.option("-c", "--config", default="pyproject.toml", help="config file")
@click.option("-P", "--private-packages", multiple=True, default=[], help="private packages")
def poetry_to_requirements(
    output: str,
    poetry_path: str,
    exclude_specifiers: bool,
    include_comments: bool,
    include_dev_requirements: bool,
    extra_requirements: List[str],
    markers: List[str],
    config: str,
    private_packages: List[str],
) -> None:
    if not private_packages:
        private_packages = get_private_packages_from_pyproject(config)
    ext = core.DependencyExporter(Poetry(poetry_path))
    fn = partial(
        ext.export_to_requirements_txt,
        include_specifiers=not exclude_specifiers,
        include_comments=include_comments,
        exclude=private_packages,
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
@click.option("-o", "--output", default=".", help="output dir")
@click.option("--poetry-path", default="poetry", help="path to poetry")
@click.option("-E", "--extra-requirements", multiple=True, default=[], help="extra requirements")
@click.option("--exclude-file-patterns", multiple=True, default=[], help="exclude files")
@click.option("-c", "--config", default="pyproject.toml", help="config file")
@click.option("-P", "--private-packages", multiple=True, default=[], help="private packages")
def extract_private_packages(
    output: str,
    poetry_path: str,
    extra_requirements: List[str],
    exclude_file_patterns: List[str],
    config: str,
    private_packages: List[str],
) -> None:
    if not private_packages:
        private_packages = get_private_packages_from_pyproject(config)

    ext = core.PackageExtractor(Poetry(poetry_path))
    ext.extract_packages(
        output_dir=output,
        packages=private_packages,
        extra_requirements=extra_requirements,
        exclude_file_patterns=exclude_file_patterns,
    )


@cli.command()
@click.option("--nuitka-path", default="nuitka3", help="path to nuitka3")
@click.option("-r", "--root", default=".", help="root dir")
@click.option("-o", "--output", default=None, help="output dir")
@click.option("-m", "--modules", multiple=True, default=None, help="included packages")
def obfuscate_modules(
    nuitka_path: str,
    root: str,
    output: Optional[str],
    modules: List[str],
) -> None:
    if not modules:
        modules = list_all_packages(root)

    if not modules:
        raise click.ClickException("No packages found")

    ext = core.PackageObfuscator(compiler=Compiler(nuitka_path))
    ext.obfuscate_packages(
        packages=modules,
        root_dir=root,
        output_dir=output,
    )


@cli.command()
@click.option("--nuitka-path", default="nuitka3", help="path to nuitka3")
@click.option("--poetry-path", default="poetry", help="path to poetry")
@click.option("-r", "--root", default=".", help="root dir")
@click.option("-o", "--output", default=None, help="output dir")
@click.option("-E", "--extra-requirements", multiple=True, default=[], help="extra requirements")
@click.option("-P", "--private-packages", multiple=True, default=[], help="private packages")
def obfuscate_private_packages(
    poetry_path: str,
    nuitka_path: str,
    root: str,
    output: Optional[str],
    extra_requirements: List[str],
    private_packages: List[str],
) -> None:
    if not private_packages:
        private_packages = get_private_packages_from_pyproject("pyproject.toml")

    if not private_packages:
        raise click.ClickException("No private packages found")

    with TemporaryDirectory() as td:
        extractor = core.PackageExtractor(Poetry(poetry_path))
        extractor.extract_packages(
            output_dir=td,
            packages=private_packages,
            extra_requirements=extra_requirements,
        )

        obfuscator = core.PackageObfuscator(compiler=Compiler(nuitka_path))
        obfuscator.obfuscate_packages(
            packages=private_packages,
            root_dir=td,
            output_dir=output,
        )


if __name__ == "__main__":
    cli()

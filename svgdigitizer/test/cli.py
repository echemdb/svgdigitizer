r"""
Helpers for click CLI testing.

Click's own CliRunner is quite cumbersome to work with in some simple test
scenarios so we wrap it in more convenient ways here.

"""

# *********************************************************************
#  This file is part of svgdigitizer.
#
#        Copyright (C)      2025 Albert Engstfeld
#        Copyright (C) 2021-2024 Julian Rüth
#
#  svgdigitizer is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  svgdigitizer is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with svgdigitizer. If not, see <https://www.gnu.org/licenses/>.
# *********************************************************************

import json
import os

import pandas
import pandas.testing
import pytest


def invoke(command, *args):
    r"""
    Invoke the click ``command`` with the given list of string arguments.

    EXAMPLES::

        >>> import click
        >>> @click.command()
        ... def hello(): print("Hello World")
        >>> invoke(hello)
        Hello World

        >>> @click.command()
        ... def fails(): raise Exception("expected error")
        >>> invoke(fails)
        Traceback (most recent call last):
        ...
        Exception: expected error

    """
    from click.testing import CliRunner

    invocation = CliRunner().invoke(command, args, catch_exceptions=False)
    output = invocation.output.strip()
    if output:
        print(output)


class TemporaryData:
    r"""
    Provides a temporary directory with test files.

    EXAMPLES::

        >>> import os
        >>> with TemporaryData("**/xy.*") as directory:
        ...     'xy.svg' in os.listdir(directory)
        True

    """

    def __init__(self, *patterns):
        self._patterns = patterns
        self._tmpdir = None

    def __enter__(self):
        import tempfile

        self._tmpdir = tempfile.TemporaryDirectory()

        try:
            import glob
            import shutil

            import svgdigitizer

            cwd = os.getcwd()
            os.chdir(os.path.join(os.path.dirname(svgdigitizer.__file__), "..", "test"))
            try:
                for pattern in self._patterns:
                    for filename in glob.glob(pattern):
                        shutil.copy(filename, self._tmpdir.name)

                return self._tmpdir.name
            finally:
                os.chdir(cwd)
        except Exception:
            self._tmpdir.cleanup()
            raise

    def __exit__(self, *args):
        self._tmpdir.cleanup()


@pytest.mark.parametrize(
    "name, args",
    [
        # Digitize tests
        ("xy", ["digitize", "xy.svg"]),
        ("scaling_factor", ["digitize", "scaling_factor.svg"]),
        ("x_and_y_scale_bar", ["digitize", "x_and_y_scale_bar.svg"]),
        ("sampling", ["digitize", "sampling.svg", "--sampling-interval", ".00101"]),
        (
            "sampling_many_points",
            ["digitize", "sampling_many_points.svg", "--sampling-interval", ".001508"],
        ),
        ("svg_without_layer", ["digitize", "svg_without_layer.svg"]),
        # CV tests
        ("xy_rate", ["cv", "xy_rate.svg", "--metadata", "xy_rate.yaml", "--si-units"]),
        (
            "xy_rate_without_metadata",
            ["cv", "xy_rate_without_metadata.svg", "--si-units"],
        ),
        (
            "xy_rate_reference",
            [
                "cv",
                "xy_rate_reference.svg",
                "--metadata",
                "xy_rate_reference.yaml",
                "--si-units",
            ],
        ),
        (
            "cv_comment",
            ["cv", "cv_comment.svg", "--metadata", "cv_comment.yaml", "--si-units"],
        ),
        (
            "xy_rate_without_metadata_skewed",
            ["cv", "xy_rate_without_metadata_skewed.svg", "--skewed", "--si-units"],
        ),
        ("axes_orientation", ["cv", "axes_orientation.svg", "--si-units"]),
        (
            "cv_bibliography",
            [
                "cv",
                "cv_bibliography.svg",
                "--metadata",
                "cv_bibliography.yaml",
                "--si-units",
                "--bibliography",
                "../bibliography/bibliography.bib",
            ],
        ),
        (
            "cv_bibliography",
            [
                "cv",
                "cv_bibliography.svg",
                "--metadata",
                "cv_bibliography.yaml",
                "--si-units",
                "--bibliography",
                "../bibliography/bibliography.bib",
                "--citation-key",
                "custom_key",
            ],
        ),
        (
            "package_no_bibliography",
            [
                "cv",
                "package_no_bibliography.svg",
                "--metadata",
                "package_no_bibliography.yaml",
                "--si-units",
                "--bibliography",
            ],
        ),
        (
            "figure_bibliography",
            [
                "figure",
                "figure_bibliography.svg",
                "--metadata",
                "figure_bibliography.yaml",
                "--si-units",
                "--bibliography",
                "../bibliography/bibliography.bib",
            ],
        ),
        (
            "xy_rate_reference_no_si",
            [
                "cv",
                "xy_rate_reference_no_si.svg",
                "--metadata",
                "xy_rate_reference_no_si.yaml",
            ],
        ),
        (
            "figure_comment",
            ["figure", "figure_comment.svg", "--metadata", "figure_comment.yaml"],
        ),
    ],
)
def test_svgdigitizer_cli(name, args):
    """
    Test that the svgdigitizer CLI commands produce the expected CSV and JSON outputs.
    """
    cwd = os.getcwd()
    with TemporaryData(f"data/{name}.*", "data/*.bib") as workdir:
        os.chdir(workdir)
        try:
            from svgdigitizer.entrypoint import cli

            invoke(cli, *args, "--outdir", "outdir")

            # If a JSON expected file exists, compare it
            json_expected = f"{name}.json.expected"
            if os.path.exists(json_expected):
                with (
                    open(f"outdir/{name}.json", encoding="utf-8") as actual,
                    open(json_expected, encoding="utf-8") as expected,
                ):
                    assert json.load(actual) == json.load(
                        expected
                    ), f"JSON mismatch for {name}"

            # Always compare CSV outputs
            csv_expected = f"{name}.csv.expected"
            pandas.testing.assert_frame_equal(
                pandas.read_csv(f"outdir/{name}.csv"),
                pandas.read_csv(csv_expected),
            )

        finally:
            os.chdir(cwd)

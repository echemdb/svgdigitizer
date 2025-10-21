r"""
Helpers for click CLI testing.

Click's own CliRunner is quite cumbersome to work with in some simple test
scenarios so we wrap it in more convenient ways here.

"""
# *********************************************************************
#  This file is part of svgdigitizer.
#
#        Copyright (C) 2025 Albert Engstfeld
#        Copyright (C) 2021 Julian Rüth
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
            import os.path
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
        ("cli-digitize-xy", ["digitize", "test/data/xy.svg"]),
        ("cli-digitize-scaling-factor", ["digitize", "test/data/scaling_factor.svg"]),
        ("cli-digitize-x_and_y_scale_bar", ["digitize", "test/data/x_and_y_scale_bar.svg"]),
        ("cli-digitize-sampling-interval", ["digitize", "test/data/sampling.svg", "--sampling-interval", ".00101"]),
        ("cli-digitize-sampling-many-points", ["digitize", "test/data/sampling_many_points.svg", "--sampling-interval", ".001508"]),
        ("cli-digitize-svg-without-layer", ["digitize", "test/data/svg_without_layer.svg"]),

        # CV tests
        ("cli-cv-xy-rate", ["cv", "test/data/xy_rate.svg", "--metadata", "test/data/xy_rate.yaml", "--si-units"]),
        ("cli-cv-xy-rate-without-metadata", ["cv", "test/data/xy_rate_without_metadata.svg", "--si-units"]),
        ("cli-cv-xy-rate-reference", ["cv", "test/data/xy_rate_reference.svg", "--metadata", "test/data/xy_rate_reference.yaml", "--si-units"]),
        ("cli-cv-cv-comment", ["cv", "test/data/cv_comment.svg", "--metadata", "test/data/cv_comment.yaml", "--si-units"]),
        ("cli-cv-xy-rate-without-metadata-skewed", ["cv", "test/data/xy_rate_without_metadata_skewed.svg", "--skewed", "--si-units"]),
        ("cli-cv-axes-orientation", ["cv", "test/data/axes_orientation.svg", "--si-units"]),
        ("cli-cv-bibliography", ["cv", "test/data/cv_bibliography.svg", "--metadata", "test/data/cv_bibliography.yaml", "--si-units", "--bibliography"]),
        ("cli-cv-package-no-bibliography", ["cv", "test/data/package_no_bibliography.svg", "--metadata", "test/data/package_no_bibliography.yaml", "--si-units", "--bibliography"]),
        ("cli-figure-bibliography", ["figure", "test/data/figure_bibliography.svg", "--metadata", "test/data/figure_bibliography.yaml", "--si-units", "--bibliography"]),
        ("cli-cv-xy-rate-reference-no-si", ["cv", "test/data/xy_rate_reference_no_si.svg", "--metadata", "test/data/xy_rate_reference_no_si.yaml"]),
        ("cli-figure-figure-comment", ["figure", "test/data/figure_comment.svg", "--metadata", "test/data/figure_comment.yaml"]),
    ],
)
def test_svgdigitizer_cli(name, args):
    """
    Test that the svgdigitizer CLI commands produce the expected CSV and JSON outputs.
    """
    cwd = os.getcwd()
    with TemporaryData(f"{name}.*") as workdir:
        os.chdir(workdir)
        try:
            from svgdigitizer.entrypoint import cli

            invoke(cli, *args, "--outdir", "outdir")

            # If a JSON expected file exists, compare it
            json_expected = f"{name}.json.expected"
            if os.path.exists(json_expected):
                with open(f"outdir/{name}.json", encoding="utf-8") as actual, open(json_expected, encoding="utf-8") as expected:
                    assert json.load(actual) == json.load(expected), f"JSON mismatch for {name}"

            # Always compare CSV outputs
            csv_expected = f"{name}.csv.expected"
            pandas.testing.assert_frame_equal(
                pandas.read_csv(f"outdir/{name}.csv"),
                pandas.read_csv(csv_expected),
            )

        finally:
            os.chdir(cwd)

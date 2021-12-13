r"""
Helpers for click CLI testing.

Click's own CliRunner is quite cumbersome to work with in some simple test
scenarios so we wrap it in more convenient ways here.

"""
# *********************************************************************
#  This file is part of svgdigitizer.
#
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
            import os
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

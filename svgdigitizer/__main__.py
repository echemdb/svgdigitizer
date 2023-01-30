r"""
The svgdigitizer suite.

EXAMPLES::

    >>> from svgdigitizer.test.cli import invoke
    >>> invoke(cli, "--help")  # doctest: +NORMALIZE_WHITESPACE
    Usage: cli [OPTIONS] COMMAND [ARGS]...
      The svgdigitizer suite.
    Options:
      --help  Show this message and exit.
    Commands:
      cv        Digitize a cylic voltammogram.
      digitize  Digitize a plot.
      paginate  Render PDF pages as individual SVG files with linked PNG images.
      plot      Display a plot of the data traced in an SVG.

"""
# ********************************************************************
#  This file is part of svgdigitizer.
#
#        Copyright (C) 2021-2022 Albert Engstfeld
#        Copyright (C)      2021 Johannes Hermann
#        Copyright (C) 2021-2022 Julian Rüth
#        Copyright (C)      2021 Nicolas Hörmann
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
# ********************************************************************
from svgdigitizer.entrypoint import cli

if __name__ == "__main__":
    cli()

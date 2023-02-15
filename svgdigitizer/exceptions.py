r"""
A collection of custom exceptions for svgdigitizer.
"""
# ********************************************************************
#  This file is part of svgdigitizer.
#
#        Copyright (C) 2021-2023 Albert Engstfeld
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


class SVGContentError(RuntimeError):
    """Raised when facing issues with the structure of the SVG input."""


class AnnotationError(SVGContentError):
    """The annotations in the SVG are is missing or incorrect."""


class CurveError(SVGContentError):
    """Raised when paths are missing, paths without label were found,
    path labels were found without a path, or multiple paths were found."""

    def __init__(self, curve=None):
        self.msg = (
            f"No path with label '{curve}' found in the SVG."
            if curve
            else "No path found in the SVG."
        )

    def __str__(self):
        return self.msg


class AxisError(SVGContentError):
    """Raised when axis are missing, too many axis are present,
    or axis are not properly labeled."""

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


# class MissingCurveLabelError(SVGContentError):
#     r"""
#     Raised when no curve label is found in the SVG.

#     EXAMPLES::

#         >>> from svgdigitizer.svg import SVG
#         >>> from svgdigitizer.svgplot import SVGPlot
#         >>> from io import StringIO
#         >>> svg = SVG(StringIO(r'''
#         ... <svg>
#         ...   <g>
#         ...     <path d="M 0 100 L 100 0" />
#         ...     <text x="0" y="0">kurve: 0</text>
#         ...   </g>
#         ...   <g>
#         ...     <path d="M 0 200 L 0 100" />
#         ...     <text x="0" y="200">x1: 0</text>
#         ...   </g>
#         ...   <g>
#         ...     <path d="M 100 200 L 100 100" />
#         ...     <text x="100" y="200">x2: 1</text>
#         ...   </g>
#         ...   <g>
#         ...     <path d="M -100 100 L 0 100" />
#         ...     <text x="-100" y="100">y1: 0</text>
#         ...   </g>
#         ...   <g>
#         ...     <path d="M -100 0 L 0 0" />
#         ...     <text x="-100" y="0">y2: 1</text>
#         ...   </g>
#         ... </svg>'''))
#         >>> plot = SVGPlot(svg)
#         >>> plot.curve
#         Traceback (most recent call last):
#         ...
#         svgdigitizer.models.exceptions.MissingCurveLabelError: No curve label found in the SVG.

#         >>> plot = SVGPlot(svg, curve="main curve")
#         >>> plot.curve
#         Traceback (most recent call last):
#         ...
#         svgdigitizer.models.exceptions.MissingCurveLabelError: No curve label with name 'main curve' found in the SVG.

#     """

#     def __init__(self, curve=None):
#         self.msg = (
#             f"No curve label with name '{curve}' found in the SVG."
#             if curve
#             else "No curve label found in the SVG."
#         )

#     def __str__(self):
#         return self.msg


class CurveError(SVGContentError):
    r"""
    In svgdigitizer a curve consists of a group with path and a textlabel.
    By default the textlabel must be of type ``<text x="0" y="0">curve: some generic name</text>``.

    An error is raised when
    * no path is found in the SVG
    * a path without a textlabel
    * a curve label but no path

    EXAMPLES::

        >>> from svgdigitizer.svg import SVG
        >>> from svgdigitizer.svgplot import SVGPlot
        >>> from io import StringIO
        >>> svg = SVG(StringIO(r'''
        ... <svg>
        ...   <g>
        ...     <text x="0" y="0">curve: 0</text>
        ...   </g>
        ...   <g>
        ...     <path d="M 0 200 L 0 100" />
        ...     <text x="0" y="200">x1: 0</text>
        ...   </g>
        ...   <g>
        ...     <path d="M 100 200 L 100 100" />
        ...     <text x="100" y="200">x2: 1</text>
        ...   </g>
        ...   <g>
        ...     <path d="M -100 100 L 0 100" />
        ...     <text x="-100" y="100">y1: 0</text>
        ...   </g>
        ...   <g>
        ...     <path d="M -100 0 L 0 0" />
        ...     <text x="-100" y="0">y2: 1</text>
        ...   </g>
        ... </svg>'''))
        >>> plot = SVGPlot(svg)
        >>> plot.curve
        Traceback (most recent call last):
        ...
        svgdigitizer.models.exceptions.CurveError: No path found in the SVG.


    Curves with specific labels can be selected::

        >>> plot = SVGPlot(svg, curve="main curve")
        >>> plot.curve
        Traceback (most recent call last):
        ...
        svgdigitizer.models.exceptions.CurveError: No path with label 'main curve' found in the SVG.

    """

    def __init__(self, curve=None):
        self.msg = (
            f"No path with label '{curve}' found in the SVG."
            if curve
            else "No path found in the SVG."
        )

    def __str__(self):
        return self.msg


class MultipleCurveLabelError(SVGContentError):
    def __init__(self):
        self.msg = "More than one curve label found in the SVG, but only a single labeled curve is supported."

    def __str__(self):
        return self.msg

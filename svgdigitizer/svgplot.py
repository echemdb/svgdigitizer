# ********************************************************************
#  This file is part of svgdigitizer.
#
#        Copyright (C) 2021 Albert Engstfeld
#        Copyright (C) 2021 Johannes Hermann
#        Copyright (C) 2021 Julian Rüth
#        Copyright (C) 2021 Nicolas Hörmann
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
from svgpathtools import Path, Line
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from functools import cache
import logging

logger = logging.getLogger('svgplot')


class SVGPlot:
    r"""
    A plot as a Scalable Vector Graphics (SVG) which can be converted to (x, y)
    coordinate pairs.

    Typically, the SVG input has been created by tracing a measurement plot from
    a publication with a `<path>` in an SVG editor such as Inkscape. Such a
    path can then be analyzed by this class to produce the coordinates
    corrsponding to the original measured values.

    INPUT:

    - ``algorithm`` -- mapping from the SVG coordinate system to the plot
      coordinate system. The default, `"axis-aligned"` assumes that the plot
      axes are perfectly aligned with the SVG coordinate system. Alternatively,
      `"mark-aligned"` assumes the end points of the axis markers are aligned,
      i.e., `x1` and `x2` have the exact same y coordinate in the plot
      coordinate system to also handle coordinate systems that are rotated or
      skewed in the SVG.

    EXAMPLES:

    An instance of this class can be created from a specially prepared SVG
    file. There must at least be a `<path>` with a corresponding label. Here, a
    segment goes from `(0, 100)` to `(100, 0)` in the (negative) SVG coordinate
    system which corresponds to a segment from `(0, 0)` to `(1, 1)` in the plot
    coordinate system::

    >>> from svgdigitizer.svg import SVG
    >>> from io import StringIO
    >>> svg = SVG(StringIO(r'''
    ... <svg>
    ...   <g>
    ...     <path d="M 0 100 L 100 0" />
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
    >>> plot.df
         x    y
    0  0.0  0.0
    1  1.0  1.0

    """
    def __init__(self, svg, xlabel=None, ylabel=None, sampling_interval=None, curve=None, algorithm='axis-aligned'):
        self.svg = svg
        self.xlabel = xlabel or 'x'
        self.ylabel = ylabel or 'y'
        self.sampling_interval = sampling_interval
        self._curve = curve
        self._algorithm = algorithm

    @property
    @cache
    def transformed_sampling_interval(self):
        r"""
        Return the sampling interval in terms of SVG coordinates on the x-axis.

        EXAMPLES::

            # >>> TODO

        """
        if not self.sampling_interval:
            return None
        if self._algorithm == 'axis-aligned':
            x1 = (0, 0)
            x2 = (self.sampling_interval, 0)
        elif self._algorithm == 'mark-aligned':
            x1 = self.marked_points[f"{self.xlabel}1"]
            x2 = self.marked_points[f"{self.xlabel}2"]
            unit = complex(x2[0] - x1[0], x2[1] - x1[1])
            unit /= abs(unit)
            unit *= self.sampling_interval
            x2 = (x1[0] + unit.real, x1[1] + unit.imag)
        else:
            raise NotImplementedError(f"sampling-interval not supported for {self._algorithm}")

        return (self.from_svg(*x2)[0] - self.from_svg(*x1)[0])

    @property
    @cache
    def units(self):
        r"""
        Return the unit for each axis.

        EXAMPLES::

        >>> from svgdigitizer.svg import SVG
        >>> from io import StringIO
        >>> svg = SVG(StringIO(r'''
        ... <svg>
        ...   <g>
        ...     <path d="M 0 200 L 0 100" />
        ...     <text x="0" y="200">x1: 0 cm</text>
        ...   </g>
        ...   <g>
        ...     <path d="M 100 200 L 100 100" />
        ...     <text x="100" y="200">x2: 1cm</text>
        ...   </g>
        ...   <g>
        ...     <path d="M -100 100 L 0 100" />
        ...     <text x="-100" y="100">y1: 0</text>
        ...   </g>
        ...   <g>
        ...     <path d="M -100 0 L 0 0" />
        ...     <text x="-100" y="0">y2: 1 A</text>
        ...   </g>
        ... </svg>'''))
        >>> plot = SVGPlot(svg)
        >>> plot.units
        {'x': 'cm', 'y': 'A'}

        TESTS:

        Units on the axes must match::

        >>> from svgdigitizer.svg import SVG
        >>> from io import StringIO
        >>> svg = SVG(StringIO(r'''
        ... <svg>
        ...   <g>
        ...     <path d="M 0 200 L 0 100" />
        ...     <text x="0" y="200">x1: 0 cm</text>
        ...   </g>
        ...   <g>
        ...     <path d="M 100 200 L 100 100" />
        ...     <text x="100" y="200">x2: 1m</text>
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
        >>> from unittest import TestCase
        >>> with TestCase.assertLogs(_) as logs:
        ...    plot.units
        ...    print(logs.output)
        {'x': 'm', 'y': None}
        ['WARNING:svgplot:Units on x axis do not match. Will ignore unit cm and use m.']

        Units on the scalebar must match the unit on the axes::

        >>> from svgdigitizer.svg import SVG
        >>> from io import StringIO
        >>> svg = SVG(StringIO(r'''
        ... <svg>
        ...   <g>
        ...     <path d="M 0 200 L 0 100" />
        ...     <text x="0" y="200">x1: 0</text>
        ...   </g>
        ...   <g>
        ...     <path d="M 100 200 L 100 100" />
        ...     <text x="100" y="200">x2: 1m</text>
        ...   </g>
        ...   <g>
        ...     <path d="M -100 100 L 0 100" />
        ...     <text x="-100" y="100">y1: 0mA</text>
        ...   </g>
        ...   <g>
        ...     <path d="M -300 300 L -200 300" />
        ...     <path d="M -300 300 L -200 200" />
        ...     <text x="-300" y="300">y_scale_bar: 1A</text>
        ...   </g>
        ... </svg>'''))
        >>> plot = SVGPlot(svg)
        >>> with TestCase.assertLogs(_) as logs:
        ...    plot.units
        ...    print(logs.output)
        {'x': 'm', 'y': 'A'}
        ['WARNING:svgplot:Units on y axis do not match. Will ignore unit mA and use A.']

        """
        def unit(axis):
            units = [
                point[1][-1] for point in [self.marked_points[axis + "1"], self.marked_points[axis + "2"]]
                if point[1][-1] is not None
            ]

            if len(units) == 0:
                return None
            if len(units) == 2:
                if units[0] != units[1]:
                    logger.warning(f"Units on {axis} axis do not match. Will ignore unit {units[0]} and use {units[1]}.")
            return units[-1]

        return {
            self.xlabel: unit(self.xlabel),
            self.ylabel: unit(self.ylabel),
        }

    @property
    @cache
    def marked_points(self):
        r"""
        Return the points that have been marked on the axes of the plot.

        For each point, a tuple is returned relating the point's coordinates in
        the SVG coordinate system to the points coordinates in the plot
        coordinate system, or `None` if that points coordinate is not known.

        EXAMPLES:

        >>> from svgdigitizer.svg import SVG
        >>> from io import StringIO
        >>> svg = SVG(StringIO(r'''
        ... <svg>
        ...   <g>
        ...     <path d="M 0 100 L 100 0" />
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
        >>> plot.marked_points == {'x2': ((100.0, 100.0), (1.0, None, None)), 'x1': ((0.0, 100.0), (0.0, None, None)), 'y2': ((0.0, 0.0), (None, 1.0, None)), 'y1': ((0.0, 100.0), (None, 0.0, None))}
        True

        TESTS:

        Test that scalebars can be parsed::

        >>> from svgdigitizer.svg import SVG
        >>> from io import StringIO
        >>> svg = SVG(StringIO(r'''
        ... <svg>
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
        ...     <path d="M -300 300 L -200 300" />
        ...     <path d="M -300 300 L -200 200" />
        ...     <text x="-300" y="300">y_scale_bar: 1</text>
        ...   </g>
        ... </svg>'''))
        >>> plot = SVGPlot(svg)
        >>> plot.marked_points == {'x2': ((100.0, 100.0), (1.0, None, None)), 'x1': ((0.0, 100.0), (0.0, None, None)), 'y2': ((0.0, 0.0), (None, 1.0, None)), 'y1': ((0.0, 100.0), (None, 0.0, None))}
        True

        """
        points = {}

        xlabels = [f"{self.xlabel}1", f"{self.xlabel}2"]
        ylabels = [f"{self.ylabel}1", f"{self.ylabel}2"]

        # Process explicitly marked point on the axes.
        for labeled_paths in self.labeled_paths['ref_point']:
            label = labeled_paths.label.point
            value = float(labeled_paths.label.value)
            unit = labeled_paths.label.unit or None

            if label in xlabels:
                plot = (value, None, unit)
            elif label in ylabels:
                plot = (None, value, unit)
            else:
                raise NotImplementedError(f"Unexpected label grouped with marked point. Expected the label to be one of {xlabels + ylabels} but found {label}.")

            if label in points:
                raise Exception(f"Found axis label {label} more than once.")

            if len(labeled_paths.paths) != 1:
                raise NotImplementedError(f"Expected exactly one path to be grouped with the marked point {label} but found {len(paths)}.")

            path = labeled_paths.paths[0]

            points[label] = (path.far, plot)

        if xlabels[0] not in points:
            raise Exception(f"Label {xlabels[0]} not found in SVG.")
        if ylabels[0] not in points:
            raise Exception(f"Label {ylabels[0]} not found in SVG.")

        # Process scale bars.
        for labeled_paths in self.labeled_paths['scale_bar']:
            label = labeled_paths.label.axis
            value = float(labeled_paths.label.value)
            unit = labeled_paths.label.unit or None

            if label not in [self.xlabel, self.ylabel]:
                raise Exception(f"Expected label on scalebar to be one of {self.xlabel}, {self.ylabel} but found {label}.")

            if label + "2" in points:
                raise Exception(f"Found more than one axis label {label}2 and scalebar for {label}.")

            if len(labeled_paths.paths) != 2:
                raise NotImplementedError(f"Expected exactly two paths to be grouped with the scalebar label {label} but found {len(paths)}.")

            endpoints = [path.far for path in labeled_paths.paths]
            scalebar = (endpoints[0][0] - endpoints[1][0], endpoints[0][1] - endpoints[1][1])

            # The scalebar has an explicit orientation in the SVG but the
            # author of the scalebar was likely not aware.
            # We assume here that the scalebar was meant to be oriented like
            # the coordinate system in the SVG, i.e., x coordinates grow to the
            # right, y coordinates grow to the bottom.
            if label == self.xlabel and scalebar[0] < 0 or label == self.ylabel and scalebar[1] > 0:
                scalebar = (-scalebar[0], -scalebar[1])

            # Construct the second marked point from the first marked point + scalebar.
            p1 = points[label + "1"]
            p2 = ((p1[0][0] + scalebar[0], p1[0][1] + scalebar[1]), (None, None))

            if label == self.xlabel:
                p2 = (p2[0], (p1[1][0] + value, None, unit))
            else:
                p2 = (p2[0], (None, p1[1][1] + value, unit))

            points[label + "2"] = p2

        if xlabels[1] not in points:
            raise Exception(f"Label {xlabels[1]} not found in SVG.")
        if ylabels[1] not in points:
            raise Exception(f"Label {ylabels[1]} not found in SVG.")

        return points

    @property
    @cache
    def scaling_factors(self):
        r"""
        Return the scaling factors for each axis.

        >>> from svgdigitizer.svg import SVG
        >>> from io import StringIO
        >>> svg = SVG(StringIO(r'''
        ... <svg>
        ...   <text x="0" y="0">y_scaling_factor: 50.6</text>
        ...   <text x="0" y="0">xsf: 50.6</text>
        ... </svg>'''))
        >>> plot = SVGPlot(svg)
        >>> plot.scaling_factors
        {'x': 50.6, 'y': 50.6}

        """
        scaling_factors = {self.xlabel: 1, self.ylabel: 1}

        for label in self.svg.get_texts(r'^(?P<axis>x|y)(_scaling_factor|sf)\: (?P<value>-?\d+\.?\d*)'):
            scaling_factors[label.axis] = float(label.value)

        return scaling_factors

    def from_svg(self, x, y):
        r"""
        Map the point (x, y) from the SVG coordinate system to the plot
        coordinate system.

        EXAMPLES:

        A simple plot. The plot uses a Cartesian (positive) coordinate system
        which in the SVG becomes a negative coordinate system, i.e., in the
        plot y grows towards the bottom. Here, the SVG coordinate (0, 100) is
        mapped to (0, 0) and (100, 0) is mapped to (1, 1)::

        >>> from svgdigitizer.svg import SVG
        >>> from io import StringIO
        >>> svg = SVG(StringIO(r'''
        ... <svg>
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
        >>> plot.from_svg(0, 100)
        (0.0, 0.0)
        >>> plot.from_svg(100, 0)
        (1.0, 1.0)

        A typical plot. Like the above but the origin is shifted and the two
        axes are not scaled equally. Here (1024, 512) is mapped to (0, 0) and
        (1124, 256) is mapped to (1, 1)::

        >>> from svgdigitizer.svg import SVG
        >>> from io import StringIO
        >>> svg = SVG(StringIO(r'''
        ... <svg>
        ...   <g>
        ...     <path d="M 1024 612 L 1024 512" />
        ...     <text x="1024" y="612">x1: 0</text>
        ...   </g>
        ...   <g>
        ...     <path d="M 1124 612 L 1124 512" />
        ...     <text x="1124" y="612">x2: 1</text>
        ...   </g>
        ...   <g>
        ...     <path d="M 924 512 L 1024 512" />
        ...     <text x="924" y="512">y1: 0</text>
        ...   </g>
        ...   <g>
        ...     <path d="M 924 256 L 1024 256" />
        ...     <text x="924" y="256">y2: 1</text>
        ...   </g>
        ... </svg>'''))
        >>> plot = SVGPlot(svg)
        >>> plot.from_svg(1024, 512)
        (0.0, 0.0)
        >>> from numpy import allclose
        >>> allclose(plot.from_svg(1124, 256), (1, 1))
        True

        A skewed plot. In this plot the axes are not orthogonal. In real plots
        the axes might be non-orthogonal but not as much as in this
        example. Here, one axis goes horizontally from (0, 100) to (100, 100)
        and the other axis goes at an angle from (0, 100) to (100, 0)::

        >>> from svgdigitizer.svg import SVG
        >>> from io import StringIO
        >>> svg = SVG(StringIO(r'''
        ... <svg>
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
        ...     <path d="M 0 0 L 100 0" />
        ...     <text x="0" y="0">y2: 1</text>
        ...   </g>
        ... </svg>'''))
        >>> plot = SVGPlot(svg, algorithm='mark-aligned')
        >>> plot.from_svg(0, 100)
        (0.0, 0.0)
        >>> plot.from_svg(100, 100)
        (1.0, 0.0)
        >>> plot.from_svg(100, 0)
        (0.0, 1.0)
        >>> plot.from_svg(0, 0)
        (-1.0, 1.0)

        """
        from numpy import dot
        return tuple(dot(self.transformation, [x, y, 1])[:2])

    @property
    @cache
    def transformation(self):
        r"""
        Return the affine map from the SVG coordinate system to the plot
        coordinate system as a matrix, see
        https://en.wikipedia.org/wiki/Affine_group#Matrix_representation

        EXAMPLES:

        A simple plot. The plot uses a Cartesian (positive) coordinate system
        which in the SVG becomes a negative coordinate system, i.e., in the
        plot y grows towards the bottom. Here, the SVG coordinate (0, 100) is
        mapped to (0, 0) and (100, 0) is mapped to (1, 1)::

        >>> from svgdigitizer.svg import SVG
        >>> from io import StringIO
        >>> svg = SVG(StringIO(r'''
        ... <svg>
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
        >>> SVGPlot(svg).transformation
        array([[ 0.01,  0.  ,  0.  ],
               [ 0.  , -0.01,  1.  ],
               [ 0.  ,  0.  ,  1.  ]])

        A typical plot. Like the above but the origin is shifted and the two
        axes are not scaled equally. Here (1000, 500) is mapped to (0, 0) and
        (1100, 300) is mapped to (1, 1)::

        >>> from svgdigitizer.svg import SVG
        >>> from io import StringIO
        >>> svg = SVG(StringIO(r'''
        ... <svg>
        ...   <g>
        ...     <path d="M 1000 600 L 1000 500" />
        ...     <text x="1000" y="600">x1: 0</text>
        ...   </g>
        ...   <g>
        ...     <path d="M 1100 600 L 1100 500" />
        ...     <text x="1100" y="600">x2: 1</text>
        ...   </g>
        ...   <g>
        ...     <path d="M 900 500 L 1000 500" />
        ...     <text x="900" y="500">y1: 0</text>
        ...   </g>
        ...   <g>
        ...     <path d="M 900 300 L 1000 300" />
        ...     <text x="900" y="300">y2: 1</text>
        ...   </g>
        ... </svg>'''))
        >>> A = SVGPlot(svg).transformation
        >>> from numpy import allclose
        >>> allclose(A, [
        ...   [ 0.01,  0.000, -10.00],
        ...   [ 0.00, -0.005,   2.50],
        ...   [ 0.00,  0.000,   1.00],
        ... ])
        True

        A skewed plot. In this plot the axes are not orthogonal. In real plots
        the axes might be non-orthogonal but not as much as in this
        example. Here, one axis goes horizontally from (0, 100) to (100, 100)
        and the other axis goes at an angle from (0, 100) to (100, 0)::

        >>> from svgdigitizer.svg import SVG
        >>> from io import StringIO
        >>> svg = SVG(StringIO(r'''
        ... <svg>
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
        ...     <path d="M 0 0 L 100 0" />
        ...     <text x="0" y="0">y2: 1</text>
        ...   </g>
        ... </svg>'''))
        >>> SVGPlot(svg, algorithm='mark-aligned').transformation
        array([[ 0.01,  0.01, -1.  ],
               [ 0.  , -0.01,  1.  ],
               [ 0.  ,  0.  ,  1.  ]])

        """
        # We construct the basic transformation from the SVG coordinate system
        # to the plot coordinate system from four points in the SVG about we
        # know something in the plot coordinate system:
        # * x1: a point whose x-coordinate we know
        # * y1: a point whose y-coordinate we know
        # * x2: a point whose x-coordinate we know
        # * y2: a point whose y-coordinate we know
        # For the axis-aligned implementation, we further assume that only
        # changing the x coordinate in the SVG does not change the y coordinate
        # in the plot and conversely.
        # For the mark-aligned algorithm, we assume that x1 and x2 have the
        # same y coordinate in the plot coordinate system. And that y1 and y2
        # have the same x coordinate in the plot coordinate system.
        # In any case, this gives six relations for the six unknowns of an
        # affine transformation.
        x1 = self.marked_points[f"{self.xlabel}1"]
        x2 = self.marked_points[f"{self.xlabel}2"]
        y1 = self.marked_points[f"{self.ylabel}1"]
        y2 = self.marked_points[f"{self.ylabel}2"]

        # We find the linear transformation:
        # [A[0] A[1] A[2]]
        # [A[3] A[4] A[5]]
        # [   0    0    1]
        # By solving for the linear conditions indicated above:
        conditions = [
            # x1 maps to something with the correct x coordinate
            ([x1[0][0], x1[0][1], 1, 0, 0, 0], x1[1][0]),
            # y1 maps to something with the correct y coordinate
            ([0, 0, 0, y1[0][0], y1[0][1], 1], y1[1][1]),
            # x2 maps to something with the correct x coordinate
            ([x2[0][0], x2[0][1], 1, 0, 0, 0], x2[1][0]),
            # y2 maps to something with the correct y coordinate
            ([0, 0, 0, y2[0][0], y2[0][1], 1], y2[1][1]),
        ]

        if self._algorithm == 'axis-aligned':
            conditions.extend([
                # Moving along the SVG x axis does not change the y coordinate
                ([0, 0, 0, 1, 0, 0], 0),
                # Moving along the SVG y axis does not change the x coordinate
                ([0, 1, 0, 0, 0, 0], 0),
            ])
        elif self._algorithm == 'mark-aligned':
            conditions.extend([
                # x1 and x2 map to the same y coordinate
                ([0, 0, 0, x1[0][0] - x2[0][0], x1[0][1] - x2[0][1], 0], 0),
                # y1 and y2 map to the same x coordinate
                ([y1[0][0] - y2[0][0], y1[0][1] - y2[0][1], 0, 0, 0, 0], 0),
            ])
        else:
            raise NotImplementedError(f"Unknown algorithm {self._algorithm}.")

        from numpy.linalg import solve
        A = solve([c[0] for c in conditions], [c[1] for c in conditions])

        # Rewrite the solution as a linear transformation matrix.
        A = [
            [A[0], A[1], A[2]],
            [A[3], A[4], A[5]],
            [0, 0, 1],
        ]

        # Apply scaling factors, as a diagonal matrix.
        from numpy import dot
        A = dot([
            [1/self.scaling_factors[self.xlabel], 0, 0],
            [0, 1/self.scaling_factors[self.ylabel], 0],
            [0, 0, 1],
        ], A)

        return A

    @property
    @cache
    def curve(self):
        r"""
        Return the path that is tracing the plot in the SVG.

        Return the `<path>` tag that is not used for other purposes such as
        pointing to axis labels.

        EXAMPLES:

        A plot going from (0, 0) to (1, 1)::

        >>> from svgdigitizer.svg import SVG
        >>> from io import StringIO
        >>> svg = SVG(StringIO(r'''
        ... <svg>
        ...   <g>
        ...     <path d="M 0 100 L 100 0" />
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
        [(0.0, 100.0), (100.0, 0.0)]

        TESTS:

        Test that filtering by curve identifier works::

        >>> plot = SVGPlot(svg, curve="main curve")
        >>> plot.curve
        Traceback (most recent call last):
        ...
        Exception: No curve main curve found in SVG.

        """
        curves = [curve for curve in self.labeled_paths['curve'] if self._curve is None or curve.label.curve_id == self._curve]

        if len(curves) == 0:
            raise Exception(f"No curve {self._curve} found in SVG.")
        if len(curves) > 1:
            raise Exception(f"More than one curve {self._curve} fonud in SVG.")

        paths = curves[0].paths

        if len(paths) == 0:
            raise Exception("Curve has not a single <path>.")
        if len(paths) > 1:
            raise NotImplementedError("Cannot handle curve with more than one <path>.")

        path = paths[0]

        if self.sampling_interval:
            # sample path if interval is set
            return SVGPlot.sample_path(path.path, self.transformed_sampling_interval)
        else:
            return path.points

    @property
    @cache
    def labeled_paths(self):
        r"""
        All paths with their corresponding label.

        We only consider paths which are grouped with a label, i.e., a `<text>`
        element. These text elements then tell us about the meaning of that
        path, e.g., the path that is labeled as `curve` is the actual graph we
        are going to extract the (x, y) coordinate pairs from.
        """
        patterns = {
            'ref_point': r'^(?P<point>(x|y)\d)\: ?(?P<value>-?\d+\.?\d*) ?(?P<unit>.+)?',
            'scale_bar': r'^(?P<axis>x|y)(_scale_bar|sb)\: ?(?P<value>-?\d+\.?\d*) ?(?P<unit>.+)?',
            'curve': r'^curve: ?(?P<curve_id>.+)',
        }

        labeled_paths = {key: self.svg.get_labeled_paths(pattern) for (key, pattern) in patterns.items()}

        for paths in self.svg.get_labeled_paths():
            if paths.label._label not in [p.label._label for pattern in patterns for p in labeled_paths[pattern]]:
                logger.warning(f"Ignoring <path> with unsupported label {paths.label}.")

        return labeled_paths

    @classmethod
    def sample_path(self, path, sampling_interval, error=None, endpoints="include"):
        r"""
        Return points on `path`, sampled at equidistant increments on the
        x-axis.

        INPUT:

        - `path` -- the SVG path to sample along the SVG x-axis.

        - `sampling_interval` -- the distance between two samples on the SVG
          x-axis.

        - `error` -- see the algorithm section below; can be `None` or a
          non-negative float.

        - `endpoints` -- whether to include the endpoints of each path segment
          `"include"` or not to include them `"exclude"`; see below for details.

        ALGORITHM:

        To do this exactly, we would need to parametrize the curve in terms of
        the x-component of the arc length. While this might actually be
        possible, it is not implemented in `svgpathtools`. What is implemented is
        a method `ilength` that returns the time at which the curve has a
        certain arc length. This essentially gives us a black box for such
        parameterization. However, this method is too slow for our purposes.
        Instead, we try to guess what increments in time are needed and then
        control for the error which is fast.

        You can select which algorithm to use with the `error` keyword. If
        `None`, the fast algorithm is used with an heuristically chosen error
        bound. If set to an explicit value, the fast algorithm is used assuring
        that the sampling points are at most `error` from the correct sampling
        point on the x-axis in the SVG coordinate system. If `error` is zero,
        the slow algorithm is used which uses `ilength` from `svgpathtools`.

        Sampling at equidistant increments might actually drop features of the
        curve. In the most extreme case, a vertical line segment, such sampling
        returns one (implementation dependent) point on that line segment. When
        `endpoints` is set to `"include"`, we always include the endpoints of
        each path segment even if they are not spaced by the sampling interval.
        If set to `"exclude"` we strictly sample with the sampling interval.


        """
        if error is None:
            # We allow the actual sampling points to be 1% from their correct positions.
            error = sampling_interval / 100

        import svgpathtools.path
        ILENGTH_S_TOL = svgpathtools.path.ILENGTH_S_TOL if error == 0 else error / 8
        ILENGTH_ERROR = svgpathtools.path.ILENGTH_ERROR if error == 0 else error / 65536
        LENGTH_ERROR = svgpathtools.path.LENGTH_ERROR if error == 0 else error / 65536

        # The path consists of path segments, each mapping a time t in [0, 1]
        # to the actual path coordinates. To get equidistant increments on the
        # x-axis, we need to determine the corresponding (typically
        # non-equidistant) increments in t. For this, we project the path down
        # to the x-axis so that arc length at time t is the same as the total
        # length in x direction at time t.
        from numpy import identity
        project_x = identity(3)
        project_x[1][1] = 0

        xpath = svgpathtools.path.transform(path, project_x)
        xlengths = [p.length() for p in xpath]

        points = []

        # We now sample the curve in euidistant increments along the x-axis.
        # For this we split the curve into path segments, starting at the first:
        segment = 0

        # The current path length on the x axis:
        x = 0

        # The corresponding time on the path segment that gives `x`.
        t = 0

        # The increment of t that approximately gives an increment of
        # sampling_interval.
        increments = [0]

        def guess_increment():
            if len(increments) >= 2:
                alg = "constant"
            else:
                alg = "constant"

            if alg == "constant":
                return increments[-1]
            if alg == "spline":
                values = increments[-3:]
                xs = [0]
                for value in range(len(values) - 1):
                    xs.append(xs[-1] - sampling_interval)
                xs.reverse()
                from scipy.interpolate import CubicSpline
                S = CubicSpline(xs, values)
                return float(S(sampling_interval))

        # For debugging purposes, we keep track of how often the guessed
        # increment was correct (and produced a speedup.)
        statistics = [0, 0]

        def add_sample(s):
            r"""
            Sample the current path segment at time `s` and record the sample.
            """
            p = path[segment].point(s)
            points.append((p.real, p.imag))

        def xlength(s):
            r"""
            Return the arc length on the x-axis at time `s`.
            """
            return xpath[segment].length(0, s, error=LENGTH_ERROR) 

        while True:
            assert 0 <= t <= 1, f"Cannot sample at time {t}."

            add_sample(t)

            # Increment to the next desired x.
            x += sampling_interval

            while x > xlengths[segment]:
                print(f"{int(statistics[0] / (statistics[1] + 1) * 100)}%")

                # We have left the current path segment.

                if endpoints == 'include':
                    # Include the final point of this path segment.
                    add_sample(1)

                # Go to the next path segment.
                x -= xlengths[segment]
                segment += 1

                if segment >= len(path):
                    # We have sampled each path segment of the path. The sample
                    # is complete.
                    return np.array(points)

                if endpoints == 'include':
                    # Include the initial point of this path segment.
                    add_sample(0)

                    if points[-1] == points[-2]:
                        # Drop one of the endpoints when the path is connected.
                        points.pop()

                    # Continue sampling from the start of the new path segment.
                    x = sampling_interval
                    t = 0

            assert x >= 0, f"Cannot sample at negative x={x}"

            # We now calculate the `t` that produces `x` on xpath. We start
            # with a guess and if that is not good enough, we compute the exact
            # value (which is very expensive.)
            increment = guess_increment()
            if increment < 0:
                increment = 0
            if increment > 1 - t:
                increment = 1 - t
            increments.append(increment)
            t += increment
            statistics[1] += 1

            # Check whether the guessed `t` is a good approximation.
            if error == 0 or abs(xlength(t) - x) > error:
                # Compute the correct value of `t`.
                s = xpath[segment].ilength(x, s_tol=ILENGTH_S_TOL, error=ILENGTH_ERROR)

                assert 0 <= s <= 1, f"svgpathtools produced invalid time {s}"
                
                if error != 0 and abs(xlength(s) - x) > error:
                    # TODO: Warn
                    print(f"Went from guessed {t} to correct {s} to get to the x path length of {x}. However, this actually got us the x path length of {xlength(s)} which is not good enough for our error bound {error}.")

                # Update our guess for the step size on the time axis.
                increments[-1] = s - (t - increment)
                print(f"{increment} was a bad guess. The correct guess would have been {increments[-1]}.")
                t = s
            else:
                statistics[0] += 1


            add_sample(t)

    @property
    @cache
    def df(self):
        return pd.DataFrame([self.from_svg(x, y) for (x, y) in self.curve], columns=[self.xlabel, self.ylabel])

    def plot(self):
        '''curve function'''
        fig, ax = plt.subplots(1, 1)
        self.df.plot(x=self.xlabel, y=self.ylabel, ax=ax, label=f'curve {i}')
        plt.xlabel(self.xlabel)
        plt.ylabel(self.ylabel)
        plt.tight_layout()
        plt.show()

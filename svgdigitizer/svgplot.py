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
    def axis_labels(self):
        r"""
        Return the label for each axis.

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
        >>> plot.axis_labels
        {'x': 'cm', 'y': 'A'}

        TESTS:

        Labels on the axes must match::

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
        ...    plot.axis_labels
        ...    print(logs.output)
        {'x': 'm', 'y': None}
        ['WARNING:svgplot:Labels on x axis do not match. Will ignore label cm and use m.']

        Labels on the scalebar must match the labels on the axes::

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
        ...    plot.axis_labels
        ...    print(logs.output)
        {'x': 'm', 'y': 'A'}
        ['WARNING:svgplot:Labels on y axis do not match. Will ignore label mA and use A.']

        """
        def axis_label(axis):
            labels = [
                point[1][-1] for point in [self.marked_points[axis + "1"], self.marked_points[axis + "2"]]
                if point[1][-1] is not None
            ]

            if len(labels) == 0:
                return None
            if len(labels) == 2:
                if labels[0] != labels[1]:
                    logger.warning(f"Labels on {axis} axis do not match. Will ignore label {labels[0]} and use {labels[1]}.")
            return labels[-1]

        return {
            self.xlabel: axis_label(self.xlabel),
            self.ylabel: axis_label(self.ylabel),
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
                raise NotImplementedError(f"Expected exactly one path to be grouped with the marked point {label} but found {len(labeled_paths.paths)}.")

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
                raise NotImplementedError(f"Expected exactly two paths to be grouped with the scalebar label {label} but found {len(labeled_paths.paths)}.")

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

        This essentially returns the `<path>` tag that is not used for other
        purposes such as pointing to axis labels. However, the path is written
        in the plot coordinate system.

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
        Path(Line(start=0j, end=(1+1j)))

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

        from svgpathtools.path import transform
        return transform(path.path, self.transformation)

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
            'ref_point': r'^(?P<point>(x|y)\d)\: ?(?P<value>-?\d+\.?\d*) *(?P<unit>.+)?',
            'scale_bar': r'^(?P<axis>x|y)(_scale_bar|sb)\: ?(?P<value>-?\d+\.?\d*) *(?P<unit>.+)?',
            'curve': r'^curve: ?(?P<curve_id>.+)',
        }

        labeled_paths = {key: self.svg.get_labeled_paths(pattern) for (key, pattern) in patterns.items()}

        for paths in self.svg.get_labeled_paths():
            if paths.label._label not in [p.label._label for pattern in patterns for p in labeled_paths[pattern]]:
                logger.warning(f"Ignoring <path> with unsupported label {paths.label}.")

        return labeled_paths

    @classmethod
    def sample_path(self, path, sampling_interval, endpoints="include"):
        r"""
        Return points on `path`, sampled at equidistant increments on the
        x-axis.

        INPUT:

        - `path` -- the SVG path to sample along the SVG x-axis.

        - `sampling_interval` -- the distance between two samples on the SVG
          x-axis.

        - `endpoints` -- whether to include the endpoints of each path segment
          `"include"` or not to include them `"exclude"`; see below for details.

        ALGORITHM:

        Let us assume that `path` is made up of Bezier curve segments (the
        other cases work essentially the same but are easier.) We project the
        curve down to the x-axis. This projection is stil a Bezier curve, i.e.,
        of the form

            B(t) = (1-t)^3 P_0 + 3t(1-t)^2 P_1 + 3t^2(1-t) P_2 + t^3 P_3.

        Since all the control points are on the axis, this is just a univariate
        polynomial of degree 3, in particular we can easily differentiate it,
        take its absolute value and integrate again. The result is a piecewise
        function x(t) that is a polynomial of degree three and it encodes the
        total distance on the x-axis at time t. So given some `X` we can easily
        solve for

            x(T) = X

        Incrementing `X` by the step size, this gives us all the times `T` that
        we wanted to sample for.

        Sampling at equidistant increments might actually drop features of the
        curve. In the most extreme case, a vertical line segment, such sampling
        returns one (implementation dependent) point on that line segment. When
        `endpoints` is set to `"include"`, we always include the endpoints of
        each path segment even if they are not spaced by the sampling interval.
        If set to `"exclude"` we strictly sample at the sampling interval.

        EXAMPLES:

        We can sample a pair of line segments::

        >>> from svgpathtools.path import Path
        >>> path = Path("M 0 0 L 1 1 L 2 0")
        >>> SVGPlot.sample_path(path, .5)
        [(0.0, 0.0), (0.5, 0.5), (1.0, 1.0), (1.5, 0.5), (2.0, 0.0)]

        We can sample a pair of Bezier curves, going from (0, 0) to (2, 0) with
        a sharp peak at (1, 1)::

        >>> from svgpathtools.path import Path
        >>> path = Path("M0 0 C 1 0, 1 0, 1 1 C 1 0, 1 0, 2 0")
        >>> SVGPlot.sample_path(path, 1)
        [(0.0, 0.0), (1.0, 1.0), (2.0, 0.0)]
        >>> len(SVGPlot.sample_path(path, .5))
        5
        >>> len(SVGPlot.sample_path(path, .1))
        21
        >>> len(SVGPlot.sample_path(path, .01))
        201

        We can sample vertical line segments::

        >>> from svgpathtools.path import Path
        >>> path = Path("M 0 0 L 0 1 M 1 1 L 1 0")
        >>> SVGPlot.sample_path(path, .0001)
        [(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0)]
        >>> SVGPlot.sample_path(path, .0001, endpoints='exclude')  # the implementation chooses the initial points of the segments
        [(0.0, 1.0), (1.0, 0.0)]

        """
        import numpy
        import svgpathtools

        EPS = 1e-6

        samples = []

        # The current path length on the x-axis at which we plan to sample (in the range [0, length of the current path segment]):
        X = 0

        # A projection down to the x-axis so that we can measure lengths in
        # x-axis direction only.
        from numpy import identity
        project_x = identity(3)
        project_x[1][1] = 0

        for segment in path:
            sample_at = []

            if endpoints == 'include':
                # Include the initial point of the new path segment.
                sample_at.append(0)

                # Continue sampling from the start of the new path segment.
                assert sampling_interval >= X, "sampling with endpoints should produce more points than sampling without"
                X = sampling_interval

            x = numpy.poly1d(numpy.real(segment.poly()))

            # At the extrema of the projection to the x-axis, the curve changes direction.
            extrema = list(root.real for root in numpy.polyder(x).roots if abs(root.imag) < EPS and 0 < root.real < 1)

            # Eventually this will contain the total length of this path segment.
            segment_length = 0

            # The time at which we sampled last.
            T = 0

            # Sample in the range [tmin, tmax] = [time at which the curve changed its behavior last, time at which the curve changes its behavior next]
            for tmin, tmax in zip([0] + extrema, extrema + [1]):
                snippet_length = abs(x(tmax) - x(tmin))
                segment_length += snippet_length

                sgn = 1 if x(tmax) > x(tmin) else -1
                f = sgn * (x - x(tmin)) + (segment_length - snippet_length)

                while X <= segment_length:
                    if abs(X - segment_length) < EPS:
                        # We are very close to the end of this segment. In this
                        # case the root computation below tends to get unstable
                        # returning roots that are slightly beyond [0, 1] so we
                        # skip forward to the end of the segment.
                        sample_at.append(tmax)
                        X = segment_length
                        break

                    # The time at which we reach position X is in [tmin, tmax)
                    # Note that this call is where all the runtime is spent in sampling.
                    # Since the polynomial is at most of degree 3 we could
                    # possibly solve symbolically and then plug in all the
                    # values for X at once which might be much faster:
                    # https://en.wikipedia.org/wiki/Cubic_equation#General_cubic_formula
                    roots = (f - X).roots
                    assert len(roots), f"The polynomial {f} should not be constant and therefore should have some roots."
                    real_roots = roots.real[abs(roots.imag) < EPS]
                    assert len(real_roots), f"The polynomial {f} should have a real root in [{tmin}, {tmax}] but we only found complex roots {roots}"
                    eligible_roots = [t for t in real_roots if tmin <= t <= tmax]
                    assert eligible_roots, f"The polynomial {f} should have a real root in [{tmin}, {tmax}] but all roots were outside that range: {roots}"
                    t = min(eligible_roots)

                    sample_at.append(t)

                    X += sampling_interval

            # We have left the current path segment.
            if endpoints == 'include':
                # Include the final point of this path segment.
                sample_at.append(1)

            assert sample_at == sorted(sample_at), f"Samples are out of order {sample_at}"

            if endpoints == 'include':
                # Do not sample points that are just a numerical-error away from the end points.
                assert sample_at[1] > EPS, f"First real sampling point should be quite a bit away from t=0 but it is only at {sample_t[1]}"
                if 1 - sample_at[-2] < EPS:
                    sample_at = sample_at[:-2] + [sample_at[-1]]

                # Do not sample at the initial point if the path is connected
                # so we do not get a duplicate with the end point of the
                # previous segment.
                if samples and abs(segment.point(0) - samples[-1]) < EPS:
                    sample_at = sample_at[1:]

            # Sample the curve
            samples.extend(segment.poly()(sample_at))

            # Go to the next path segment.
            X -= segment_length

            assert X >= 0, f"Cannot sample at negative x={x}"

        return [(p.real, p.imag) for p in samples]

    @property
    @cache
    def df(self):
        r"""
        Return the plot data as a dataframe of pairs (x, y).

        The returned data lives in the plot coordinate system.

        EXMAMPLES::

        A diagonal from (0, 100) to (100, 0) in the SVG coordinate system,
        i.e., the function y=x::

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

        The same plot but now sampled at 0.2 increments on the x-axis::

            >>> plot = SVGPlot(svg, sampling_interval=.2)
            >>> plot.df
                 x    y
            0  0.0  0.0
            1  0.2  0.2
            2  0.4  0.4
            3  0.6  0.6
            4  0.8  0.8
            5  1.0  1.0

        Again diagonal from (0, 100) to (100, 0) in the SVG coordinate system,
        i.e., visually the function y=x. However, the coordinate system is
        skewed, the x-axis is parallel to the plot and so this is actually the
        function y=0::

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
            ...     <path d="M 100 200 L 100 0" />
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
            >>> plot = SVGPlot(svg, algorithm='mark-aligned')
            >>> plot.df
                 x    y
            0  0.0  0.0
            1  1.0  0.0

        The same plot but now sampled at 0.2 increments on the x-axis::

            >>> plot = SVGPlot(svg, sampling_interval=.2, algorithm='mark-aligned')
            >>> plot.df
                 x    y
            0  0.0  0.0
            1  0.2  0.0
            2  0.4  0.0
            3  0.6  0.0
            4  0.8  0.0
            5  1.0  0.0

        """
        if self.sampling_interval:
            points = SVGPlot.sample_path(self.curve, self.sampling_interval)
        else:
            from .svg import LabeledPath
            points = LabeledPath.path_points(self.curve)

        return pd.DataFrame(points, columns=[self.xlabel, self.ylabel])

    def plot(self):
        r"""
        Visualize the data in this plot.
        """
        fig, ax = plt.subplots(1, 1)
        self.df.plot(x=self.xlabel, y=self.ylabel, ax=ax)
        plt.xlabel(self.xlabel)
        plt.ylabel(self.ylabel)
        plt.tight_layout()
        plt.show()

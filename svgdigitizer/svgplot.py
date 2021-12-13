r"""
Scientific plots in SVG format.

A :class:`SVGPlot` wraps a plot in SVG format consisting of a curve, axis
labels and (optionally) additional metadata provided as text fields in the SVG.

As an example, consider the graph given by the line segment connecting (0, 0)
and (1, 1). In the SVG coordinate system, such a line segment is
given as the path connecting the points (0, 100) and (100, 0); note that the
SVG coordinate system is negative, i.e., the y-axis grows towards the bottom::

    >>> curve = '<path d="M 0 100 L 100 0" />'

We need to attach a label to this path, so :class:`SVGPlot` understands that
this is the actual curve that contains data we want to digitize. We do so by
grouping this path with a label, that says "curve: …". The position of that
label has no importance but is required. The identifier itself does also not
matter in this example.  It is only relevant when there are multiple curves in
the same SVG::

    >>> curve = f'''
    ...     <g>
    ...       { curve }
    ...       <text x="0" y="0">curve: 0</text>
    ...     </g>
    ... '''

Additionally, we need to establish a plot coordinate system. We do so by
creating ticks for two reference ticks for both the x-axis and the y-axis.
To start, we want to define that the y=100 in the SVG coordinate system
corresponds to y=0 in the plot coordinate system::

    >>> y1 = '<text x="-100" y="100">y1: 0</text>'

The location of this reference label does not matter much, we just put it
somewhere where it looks nice. Now we need to pinpoint the place on the y-axis
that corresponds to y=0. We do so by drawing a path from close to the base
point of the reference label to that point on the y-axis and group it with the
label::

    >>> y1 = f'''
    ...     <g>
    ...       <path d="M -100 100 L 0 100" />
    ...       { y1 }
    ...     </g>
    ... '''

We repeat the same process for the other reference labels, i.e., `y2`, `x1`,
`x2` and obtain our input SVG that :class:`SVGPlot` can make sense of. Note
that we added some units, so the x-axis is the time in seconds, and the y-axis
is a voltage in volts.

    >>> svg = f'''
    ...     <svg>
    ...       { curve }
    ...       <g>
    ...         <path d="M 0 200 L 0 100" />
    ...         <text x="0" y="200">x1: 0</text>
    ...       </g>
    ...       <g>
    ...         <path d="M 100 200 L 100 100" />
    ...         <text x="100" y="200">x2: 1s</text>
    ...       </g>
    ...       { y1 }
    ...       <g>
    ...         <path d="M -100 0 L 0 0" />
    ...         <text x="-100" y="0">y2: 1V</text>
    ...       </g>
    ...     </svg>
    ... '''

We wrap this string into an :class:`svg.SVG` object and create an actual
:class:`SVGPlot` from it::

    >>> from svgdigitizer.svg import SVG
    >>> from io import StringIO
    >>> svg = SVG(StringIO(svg))
    >>> plot = SVGPlot(svg)

Now we can query the plot for things such as the units used on the axes::

    >>> plot.axis_labels
    {'x': 's', 'y': 'V'}

We can get a pandas data frame with actual plot data in the plot coordinate
system::

    >>> plot.df
         x    y
    0  0.0  0.0
    1  1.0  1.0

This data frame is built from the end points of the paths that make up the
curve. We can also interpolate at equidistant points on the x-axis by
specifying a `sampling_interval`::

    >>> plot = SVGPlot(svg, sampling_interval=.1)
    >>> plot.df
          x    y
    0   0.0  0.0
    1   0.1  0.1
    2   0.2  0.2
    3   0.3  0.3
    4   0.4  0.4
    5   0.5  0.5
    6   0.6  0.6
    7   0.7  0.7
    8   0.8  0.8
    9   0.9  0.9
    10  1.0  1.0

"""
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
import logging
from functools import cache

import pandas as pd

logger = logging.getLogger("svgplot")


class SVGPlot:
    r"""
    A plot as a Scalable Vector Graphics (SVG) which can be converted to (x, y)
    coordinate pairs.

    Typically, the SVG input has been created by tracing a measurement plot from
    a publication with a `<path>` in an SVG editor such as Inkscape. Such a
    path can then be analyzed by this class to produce the coordinates
    corresponding to the original measured values.

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
    _EPSILON = 1e-6

    def __init__(
        self,
        svg,
        xlabel=None,
        ylabel=None,
        sampling_interval=None,
        curve=None,
        algorithm="axis-aligned",
    ):
        self.svg = svg
        self.xlabel = xlabel or "x"
        self.ylabel = ylabel or "y"
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
                point[1][-1]
                for point in [
                    self.marked_points[axis + "1"],
                    self.marked_points[axis + "2"],
                ]
                if point[1][-1] is not None
            ]

            if len(labels) == 0:
                return None
            if len(labels) == 2:
                if labels[0] != labels[1]:
                    logger.warning(
                        f"Labels on {axis} axis do not match. Will ignore label {labels[0]} and use {labels[1]}."
                    )
            return labels[-1]

        return {
            self.xlabel: axis_label(self.xlabel),
            self.ylabel: axis_label(self.ylabel),
        }

    @property
    def _marked_points_from_axis_markers(self):
        r"""
        Return the points that have been explicitly marked on the axes of the plot.

        For each point, a tuple is returned relating the point's coordinates in
        the SVG coordinate system to the point's coordinates in the plot
        coordinate system, or `None` if that point's coordinate is not known.
        """
        points = {}

        xlabels = [f"{self.xlabel}1", f"{self.xlabel}2"]
        ylabels = [f"{self.ylabel}1", f"{self.ylabel}2"]

        # Process explicitly marked point on the axes.
        for labeled_paths in self.labeled_paths["ref_point"]:
            assert len(labeled_paths) != 0

            if len(labeled_paths) != 1:
                raise ValueError(
                    f"Expected exactly one path to be grouped with {labeled_paths.label}"
                )

            path = labeled_paths[0]

            label = labeled_paths.label
            point = label.point
            value = float(label.value)
            unit = label.unit or None

            if point in xlabels:
                plot = (value, None, unit)
            elif point in ylabels:
                plot = (None, value, unit)
            else:
                raise NotImplementedError(
                    f"Unexpected label grouped with marked point. Expected the label to be one of {xlabels + ylabels} but found {label}."
                )

            if point in points:
                raise Exception(f"Found axis label {label} more than once.")

            if len(labeled_paths) != 1:
                raise NotImplementedError(
                    f"Expected exactly one path to be grouped with the marked point {label} but found {len(labeled_paths.paths)}."
                )

            points[point] = (path.far, plot)

        return points

    def _marked_points_from_scalebars(self, base_points):
        r"""
        Return the points that have been specified through a scalebar in the plot.

        For each point, a tuple is returned relating the point's coordinates in
        the SVG coordinate system to the point's coordinates in the plot
        coordinate system, or `None` if that point's coordinate is not known.
        """
        points = {}

        # Process scale bars.
        for labeled_paths in self.labeled_paths["scale_bar"]:
            if len(labeled_paths) != 2:
                raise NotImplementedError(
                    f"Expected exactly two paths to be grouped with the scalebar label {labeled_paths.label} but found {len(labeled_paths)}."
                )

            label = labeled_paths.label
            axis = label.axis
            value = float(label.value)
            unit = label.unit or None

            if axis not in [self.xlabel, self.ylabel]:
                raise Exception(
                    f"Expected label on scalebar to be one of {self.xlabel}, {self.ylabel} but found {axis}."
                )

            endpoints = [path.far for path in labeled_paths]
            scalebar = (
                endpoints[0][0] - endpoints[1][0],
                endpoints[0][1] - endpoints[1][1],
            )

            # The scalebar has an explicit orientation in the SVG but the
            # author of the scalebar was likely not aware.
            # We assume here that the scalebar was meant to be oriented like
            # the coordinate system in the SVG, i.e., x coordinates grow to the
            # right, y coordinates grow to the bottom.
            if (
                axis == self.xlabel
                and scalebar[0] < 0
                or axis == self.ylabel
                and scalebar[1] > 0
            ):
                scalebar = (-scalebar[0], -scalebar[1])

            # Construct the second marked point from the first marked point + scalebar.
            base_point = base_points[axis + "1"]
            point = (
                (base_point[0][0] + scalebar[0], base_point[0][1] + scalebar[1]),
                (None, None),
            )

            if axis == self.xlabel:
                point = (point[0], (base_point[1][0] + value, None, unit))
            else:
                point = (point[0], (None, base_point[1][1] + value, unit))

            points[axis + "2"] = point

        return points

    @property
    @cache
    def marked_points(self):
        r"""
        Return the points that have been marked on the axes of the plot.

        For each point, a tuple is returned relating the point's coordinates in
        the SVG coordinate system to the point's coordinates in the plot
        coordinate system, or `None` if that point's coordinate is not known.

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
        xlabels = [f"{self.xlabel}1", f"{self.xlabel}2"]
        ylabels = [f"{self.ylabel}1", f"{self.ylabel}2"]

        points = self._marked_points_from_axis_markers

        if xlabels[0] not in points:
            raise Exception(f"Label {xlabels[0]} not found in SVG.")
        if ylabels[0] not in points:
            raise Exception(f"Label {ylabels[0]} not found in SVG.")

        for label, point in self._marked_points_from_scalebars(points).items():
            if label in points:
                raise Exception(f"Found an axis label and scale bar for {label}.")

            points[label] = point

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

        EXAMPLES::

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

        for label in self.svg.get_texts(
            r"^(?P<axis>x|y)(_scaling_factor|sf)\: (?P<value>-?\d+\.?\d*)"
        ):
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
            >>> from numpy import allclose
            >>> allclose(plot.from_svg(1024, 512), (0, 0))
            True
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
        # * x_1: a point whose x-coordinate we know
        # * y_1: a point whose y-coordinate we know
        # * x_2: a point whose x-coordinate we know
        # * y_2: a point whose y-coordinate we know
        # For the axis-aligned implementation, we further assume that only
        # changing the x coordinate in the SVG does not change the y coordinate
        # in the plot and conversely.
        # For the mark-aligned algorithm, we assume that x1 and x2 have the
        # same y coordinate in the plot coordinate system. And that y1 and y2
        # have the same x coordinate in the plot coordinate system.
        # In any case, this gives six relations for the six unknowns of an
        # affine transformation.
        x_1 = self.marked_points[f"{self.xlabel}1"]
        x_2 = self.marked_points[f"{self.xlabel}2"]
        y_1 = self.marked_points[f"{self.ylabel}1"]
        y_2 = self.marked_points[f"{self.ylabel}2"]

        # We find the linear transformation:
        # [transformation[0] transformation[1] transformation[2]]
        # [transformation[3] transformation[4] transformation[5]]
        # [   0    0    1]
        # By solving for the linear conditions indicated above:
        conditions = [
            # x1 maps to something with the correct x coordinate
            ([x_1[0][0], x_1[0][1], 1, 0, 0, 0], x_1[1][0]),
            # y1 maps to something with the correct y coordinate
            ([0, 0, 0, y_1[0][0], y_1[0][1], 1], y_1[1][1]),
            # x2 maps to something with the correct x coordinate
            ([x_2[0][0], x_2[0][1], 1, 0, 0, 0], x_2[1][0]),
            # y2 maps to something with the correct y coordinate
            ([0, 0, 0, y_2[0][0], y_2[0][1], 1], y_2[1][1]),
        ]

        if self._algorithm == "axis-aligned":
            conditions.extend(
                [
                    # Moving along the SVG x axis does not change the y coordinate
                    ([0, 0, 0, 1, 0, 0], 0),
                    # Moving along the SVG y axis does not change the x coordinate
                    ([0, 1, 0, 0, 0, 0], 0),
                ]
            )
        elif self._algorithm == "mark-aligned":
            conditions.extend(
                [
                    # x1 and x2 map to the same y coordinate
                    ([0, 0, 0, x_1[0][0] - x_2[0][0], x_1[0][1] - x_2[0][1], 0], 0),
                    # y1 and y2 map to the same x coordinate
                    ([y_1[0][0] - y_2[0][0], y_1[0][1] - y_2[0][1], 0, 0, 0, 0], 0),
                ]
            )
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

        A = dot(
            [
                [1 / self.scaling_factors[self.xlabel], 0, 0],
                [0, 1 / self.scaling_factors[self.ylabel], 0],
                [0, 0, 1],
            ],
            A,
        )

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
        curves = self.labeled_paths["curve"]

        if len(curves) == 0:
            raise Exception("No curve found in SVG.")

        curves = [
            curve
            for curve in curves
            if self._curve is None or curve.label.curve_id == self._curve
        ]

        if len(curves) == 0:
            raise Exception(f"No curve {self._curve} found in SVG.")
        if len(curves) > 1:
            raise Exception(f"More than one curve {self._curve} fonud in SVG.")

        paths = curves[0]

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

        EXAMPLES::

            >>> from svgdigitizer.svg import SVG
            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 100 L 100 0" />
            ...     <text x="0" y="0">curve: 0</text>
            ...   </g>
            ... </svg>'''))
            >>> plot = SVGPlot(svg)
            >>> plot.labeled_paths
            {'ref_point': [], 'scale_bar': [], 'curve': [[Path "curve: 0"]]}

        TESTS::

            >>> from svgdigitizer.svg import SVG
            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 100 L 100 0" />
            ...     <text x="0" y="0">kurve: 0</text>
            ...   </g>
            ... </svg>'''))
            >>> plot = SVGPlot(svg)
            >>> from unittest import TestCase
            >>> with TestCase.assertLogs(_) as warnings:
            ...     plot.labeled_paths
            ...     print(warnings.output)
            {'ref_point': [], 'scale_bar': [], 'curve': []}
            ['WARNING:svgplot:Ignoring <path> with unsupported label kurve: 0.']

        """
        patterns = {
            "ref_point": r"^(?P<point>(x|y)\d)\: ?(?P<value>-?\d+\.?\d*) *(?P<unit>.+)?",
            "scale_bar": r"^(?P<axis>x|y)(_scale_bar|sb)\: ?(?P<value>-?\d+\.?\d*) *(?P<unit>.+)?",
            "curve": r"^curve: ?(?P<curve_id>.+)",
        }

        # Collect labeled paths with supported patterns.
        labeled_paths = {
            key: self.svg.get_labeled_paths(pattern)
            for (key, pattern) in patterns.items()
        }

        # Collect all labeled paths and warn if there is a label that we do not recognize.
        for paths in self.svg.get_labeled_paths():
            if str(paths.label) not in [
                str(recognized_paths.label)
                for pattern in patterns
                for recognized_paths in labeled_paths[pattern]
            ]:
                logger.warning(f"Ignoring <path> with unsupported label {paths.label}.")

        return labeled_paths

    @classmethod
    def sample_path(cls, path, sampling_interval, endpoints="include"):
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
            >>> SVGPlot.sample_path(path, .0001, endpoints='exclude')  # the implementation chooses the initial point of the first segment
            [(0.0, 1.0)]

        TESTS:

        A case where numpy's root finding returns the extrema out of order::

            >>> from svgpathtools.path import Path
            >>> path = Path("M-267 26 C -261 25, -266 24, -264 23")
            >>> len(SVGPlot.sample_path(path, .001))
            4159

        """
        samples = []

        # The path length on the x-axis at which we plan to sample (in the range [0, length of the path segment]):
        sample_from_x = 0

        for segment in path:
            sample_at, sample_from_x = cls._sample_segment(
                segment=segment,
                sampling_interval=sampling_interval,
                sample_from_x_length=sample_from_x,
                endpoints=endpoints,
            )

            # Do not sample at the initial point if the path is connected
            # so we do not get a duplicate with the end point of the
            # previous segment.
            if samples and abs(segment.point(0) - samples[-1]) < cls._EPSILON:
                sample_at = sample_at[1:]

            samples.extend(segment.poly()(sample_at))

        return [(p.real, p.imag) for p in samples]

    @classmethod
    def _sample_segment(
        cls, segment, sampling_interval, sample_from_x_length=0, endpoints="include"
    ):
        r"""
        Sample the `segment` at equidistant points spaced by
        `sampling_interval` on the x-axis starting at `starting_from_x_length`.

        Returns the times at which to sample, and also the single place at
        which to sample in the next segment written as a length on the x-axis.

        This is a helper method for `sample_path`.

        EXAMPLES:

        A single line segment::

            >>> from svgpathtools.path import Path
            >>> path = Path("M 0 0 L 1 1")
            >>> segment = next(iter(path))
            >>> SVGPlot._sample_segment(segment, .25)
            ([0, 0.25, 0.5, 0.75, 1], 0.0)

        The first point to sample can be shifted with `sample_from_x_length`;
        this also shitfs the next point at which to sample next in the
        following segment::

            >>> SVGPlot._sample_segment(segment, .25, sample_from_x_length=.125, endpoints='exclude')
            ([0.125, 0.375, 0.625, 0.875], 0.125)

        When `sample_from_x_length` exceeds the length of the segment, no
        sampling might be performed::

            >>> SVGPlot._sample_segment(segment, .25, sample_from_x_length=2, endpoints='exclude')
            ([], 1.0)

        When including the endpoints, `sample_from_x_length` has no effect since
        we always start and end sampling at the end points of the segment::

            >>> SVGPlot._sample_segment(segment, .25, sample_from_x_length=2)
            ([0, 0.25, 0.5, 0.75, 1], 0.0)

        ::

            >>> SVGPlot._sample_segment(segment, .75, sample_from_x_length=2)
            ([0, 0.75, 1], 0.0)

        """
        if sample_from_x_length < 0:
            raise ValueError(f"Cannot sample at negative length {sample_from_x_length}")

        sample_at = []

        # The path length on the x-axis at which we plan to sample (in the range [0, length of the path segment]):
        x_length_target = sample_from_x_length

        if endpoints == "include":
            # Include the initial point of the path segment.
            sample_at.append(0)

            # Continue sampling from the start of the path segment.
            x_length_target = sampling_interval

        import numpy

        x = numpy.poly1d(numpy.real(segment.poly()))

        # At the extrema of the projection to the x-axis, the curve changes direction.
        extrema = list(
            sorted(
                root.real
                for root in numpy.polyder(x).roots
                if abs(root.imag) < cls._EPSILON and 0 < root.real < 1
            )
        )

        # Eventually this will equal the total length of this path segment.
        segment_length = 0

        # Sample in the range [tmin, tmax] = [time at which the curve changed its behavior last, time at which the curve changes its behavior next]
        for tmin, tmax in zip([0] + extrema, extrema + [1]):
            snippet_length = abs(x(tmax) - x(tmin))

            sample_snippet_at, x_length_target = cls._sample_snippet(
                segment=segment,
                t_range=(tmin, tmax),
                sampling_interval=sampling_interval,
                sample_from_x_length=x_length_target,
                x_length_range=(segment_length, segment_length + snippet_length),
            )
            sample_at.extend(sample_snippet_at)

            segment_length += snippet_length

        # We have left the path segment.
        if endpoints == "include":
            # Include the final point of this path segment.
            sample_at.append(1)

        assert sample_at == sorted(sample_at), f"Samples are out of order {sample_at}"

        if endpoints == "include":
            # Do not sample points that are just a numerical-error away from the end points.
            assert (
                sample_at[1] > cls._EPSILON
            ), f"First real sampling point should be quite a bit away from t=0 but it is only at {sample_at[1]}"
            if 1 - sample_at[-2] < cls._EPSILON:
                sample_at = sample_at[:-2] + [sample_at[-1]]

            x_length_target = segment_length

        # Go to the next path segment.
        x_length_target -= segment_length

        # Sample the curve
        return sample_at, x_length_target

    @classmethod
    def _sample_snippet(
        cls, segment, sampling_interval, sample_from_x_length, t_range, x_length_range
    ):
        r"""
        Sample the path segment `segment` at times in the range `[t_range[0],
        t_range[1]]` at equidistant steps spaced by `sampling_interval` on the
        length of the segment projected to the x-axis, starting from
        `sample_from_x_length`.

        Returns the times at which to sample and the place at which to sample
        in the next snippet written as a segment length on the x-axis.

        For performance reasons, the length of the segment after projection to
        the x-axis at the times `t_range` must be provided as a pair
        `x_length_range`.

        This is a helper method for `sample_path`.

        EXAMPLES:

        We sample a piece of a line segment::

            >>> from svgpathtools.path import Path
            >>> path = Path("M 0 0 L 1 1")
            >>> segment = next(iter(path))
            >>> SVGPlot._sample_snippet(segment, sampling_interval=.25, sample_from_x_length=.25, t_range=[.25, .75], x_length_range=[.25, .75])
            ([0.25, 0.5, 0.75], 1.0)
            >>> SVGPlot._sample_snippet(segment, sampling_interval=1, sample_from_x_length=.5, t_range=[.5, 1.], x_length_range=[.5, 1.])
            ([0.5], 1.5)

        """
        if sample_from_x_length < 0:
            raise ValueError(f"Cannot sample at negative length {sample_from_x_length}")

        if t_range[1] < t_range[0]:
            raise ValueError("Sampling must not go backwards in time.")

        if x_length_range[1] < x_length_range[0]:
            raise ValueError("Sampling must not go backwards on the segment.")

        import numpy

        x = numpy.poly1d(numpy.real(segment.poly()))

        sample_at = []

        # The path length on the x-axis at which we plan to sample (in the range [0, length of the path segment]):
        x_length_target = sample_from_x_length

        sgn = 1 if x(t_range[1]) > x(t_range[0]) else -1
        x_length = sgn * (x - x(t_range[0])) + x_length_range[0]

        while x_length_target <= x_length_range[1]:
            if abs(x_length_target - x_length_range[1]) < cls._EPSILON:
                # We are very close to the end of this segment. In this
                # case the root computation below tends to get unstable
                # returning roots that are slightly beyond [0, 1] so we
                # skip forward to the end of the segment.
                sample_at.append(t_range[1])
                x_length_target = x_length_range[1] + sampling_interval
                break

            # The time at which we reach position X is in [t_range[0], t_range[1])
            # Note that this call is where all the runtime is spent in sampling.
            # Since the polynomial is at most of degree 3 we could
            # possibly solve symbolically and then plug in all the
            # values for x_pos at once which might be much faster:
            # https://en.wikipedia.org/wiki/Cubic_equation#General_cubic_formula
            t = cls._min_real_root(x_length - x_length_target, t_range[0], t_range[1])
            sample_at.append(t)

            x_length_target += sampling_interval

        return sample_at, x_length_target

    @classmethod
    def _min_real_root(cls, polynomial, tmin, tmax):
        r"""
        Return the smallest real root of `polynomial` in the range [tmin, tmax].

        EXAMPLES:

        A cubic polynomial with roots at 0, 1, 2::

            >>> import numpy
            >>> p = numpy.poly1d([1, -3, 2, 0])
            >>> SVGPlot._min_real_root(p, 0, 10)
            0.0
            >>> SVGPlot._min_real_root(p, 1, 10)
            1.0
            >>> SVGPlot._min_real_root(p, 2, 10)
            2.0
            >>> SVGPlot._min_real_root(p, 3, 10)
            Traceback (most recent call last):
            ...
            ValueError: ...


        """
        roots = polynomial.roots

        if len(roots) == 0:
            raise ValueError(f"The polynomial {polynomial} must not be constant.")

        real_roots = roots.real[abs(roots.imag) < cls._EPSILON]
        if len(real_roots) == 0:
            raise ValueError(
                f"The polynomials {polynomial} must have real roots. But all roots where complex: {roots}"
            )

        eligible_roots = [t for t in real_roots if tmin <= t <= tmax]
        if len(eligible_roots) == 0:
            raise ValueError(
                f"The polynomial {polynomial} must have roots in [{tmin}, {tmax}]. But all roots where outside that range: {roots}"
            )

        return min(eligible_roots)

    @property
    @cache
    def df(self):
        r"""
        Return the plot data as a dataframe of pairs (x, y).

        The returned data lives in the plot coordinate system.

        EXAMPLES:

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

        EXAMPLES::

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
            ...     <text x="100" y="200">x2: 1 s</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">y1: 0</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">y2: 1 cm</text>
            ...   </g>
            ... </svg>'''))
            >>> plot = SVGPlot(svg)
            >>> plot.plot()

        """
        self.df.plot(
            x=self.xlabel,
            y=self.ylabel,
            xlabel=f"{self.xlabel} [{self.axis_labels[self.xlabel]}]",
            ylabel=f"{self.ylabel} [{self.axis_labels[self.ylabel]}]",
            legend=False,
        )

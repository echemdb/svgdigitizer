from svg.path import parse_path
from svgpathtools import Path, Line
from xml.dom import minidom, Node
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from functools import cache
import re
import logging

label_patterns = {
    'ref_point': r'^(?P<point>(x|y)\d)\: ?(?P<value>-?\d+\.?\d*) ?(?P<unit>.+)?',
    'scale_bar': r'^(?P<axis>x|y)(_scale_bar|sb)\: ?(?P<value>-?\d+\.?\d*) ?(?P<unit>.+)?',
    'scaling_factor': r'^(?P<axis>x|y)(_scaling_factor|sf)\: (?P<value>-?\d+\.?\d*)',
    'curve': r'^curve: ?(?P<curve_id>.+)',
}

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

    >>> from io import StringIO
    >>> svg = StringIO(r'''
    ... <svg>
    ...   <g>
    ...     <path d="M 0 100 L 100 0" />
    ...     <text>curve: 0</text>
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
    ... </svg>''')
    >>> plot = SVGPlot(svg)
    >>> plot.df
         x    y
    0  0.0  0.0
    1  1.0  1.0

    """
    def __init__(self, svg, xlabel=None, ylabel=None, sampling_interval=None, curve=None, algorithm='axis-aligned'):
        self.svg = minidom.parse(svg)

        self.xlabel = xlabel or 'x'
        self.ylabel = ylabel or 'y'

        self.sampling_interval = sampling_interval

        self._curve = curve

        self._algorithm = algorithm

    @property
    @cache
    def transformed_sampling_interval(self):
        factor = 1/((self.trafo['x'](self.sampling_interval)-self.trafo['x'](0))/(self.sampling_interval/1000))
        return factor

    @property
    @cache
    def marked_points(self):
        r"""
        Return the points that have been marked on the axes of the plot.

        For each point, a tuple is returned relating the point's coordinates in
        the SVG coordinate system to the points coordinates in the plot
        coordinate system, or `None` if that points coordinate is not known.

        EXAMPLES:

        >>> from io import StringIO
        >>> svg = StringIO(r'''
        ... <svg>
        ...   <g>
        ...     <path d="M 0 100 L 100 0" />
        ...     <text>curve: 0</text>
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
        ... </svg>''')
        >>> plot = SVGPlot(svg)
        >>> plot.marked_points == {'x2': ((100.0, 100.0), (1.0, None)), 'x1': ((0.0, 100.0), (0.0, None)), 'y2': ((0.0, 0.0), (None, 1.0)), 'y1': ((0.0, 100.0), (None, 0.0))}
        True

        """
        points = {}

        xlabels = [f"{self.xlabel}1", f"{self.xlabel}2"]
        ylabels = [f"{self.ylabel}1", f"{self.ylabel}2"]

        # Process explicitly marked point on the axes.
        for (text, paths, match) in self.labeled_paths['ref_point']:
            label = match.group("point")

            if label in xlabels:
                plot = (float(match.group("value")), None)
            elif label in ylabels:
                plot = (None, float(match.group("value")))
            else:
                raise NotImplementedError(f"Unexpected label grouped with marked point. Expected the label to be one of {xlabels + ylabels} but found {label}.")

            if label in points:
                raise Exception(f"Found axis label {label} more than once.")

            if len(paths) != 1:
                raise NotImplementedError(f"Expected exactly one path to be grouped with the marked point {label} but found {len(paths)}.")

            path = parse_path(paths[0].getAttribute('d'))

            # We need to decide which endpoint of the path is actually the marked point on the axis.
            # We always take the one that is further from the label origin.
            text = complex(float(text.getAttribute('x')), float(text.getAttribute('y')))
            svg = max([path.point(0), path.point(1)], key=lambda p: abs(p - text))

            points[label] = ((svg.real, svg.imag), plot)

        if xlabels[0] not in points:
            raise Exception(f"Label {xlabels[0]} not found in SVG.")
        if ylabels[0] not in points:
            raise Exception(f"Label {ylabels[0]} not found in SVG.")

        # Process scale bars.
        for (text, paths, match) in self.labeled_paths['scale_bar']:
            label = match.group('axis')
            value = float(match.group("value"))

            if label not in [self.xlabel, self.ylabel]:
                raise Exception(f"Expected label on scalebar to be one of {self.xlabel}, {self.ylabel} but found {label}.")

            if label + "2" in points:
                raise Exception(f"Found more than one axis label {label}2 and scalebar for {label}.")

            if len(paths) != 1:
                raise NotImplementedError(f"Expected exactly one path to be grouped with the scalebar label {label} but found {len(paths)}.")

            path = parse_path(paths[0].getAttribute('d'))

            scalebar = path.point(1) - path.point(0)

            # The scalebar has an explicit orientation in the SVG but the
            # author of the scalebar was likely not aware.
            # We assume here that the scalebar was meant to be oriented like
            # the coordinate system in the SVG, i.e., x coordinates grow to the
            # right, y coordinates grow to the bottom.
            if label == self.xlabel:
                if scalebar.real < 0:
                    scalebar = -scalebar
            else:
                if scalebar.imag > 0:
                    scalebar = -scalebar

            # Construct the second marked point from the first marked point + scalebar.
            p1 = points[label + "1"]
            p2 = ((p1[0][0] + scalebar.real, p1[0][1] + scalebar.imag), (None, None))

            if label == self.xlabel:
                p2 = (p2[0], (p1[1][0] + value, None))
            else:
                p2 = (p2[0], (None, p1[1][1] + value))

            points[label + "2"] = p2

        if xlabels[1] not in points:
            raise Exception(f"Label {xlabels[1]} not found in SVG.")
        if ylabels[1] not in points:
            raise Exception(f"Label {ylabels[1]} not found in SVG.")

        return points

    @property
    @cache
    def scale_bars(self):
        scale_bars = {}

        for (text, path, match) in self.labeled_paths['scale_bar']:
            end_points = []
            for path in paths:
                parsed_path = parse_path(path.getAttribute('d'))
                # always take the point of the path which is further away from text origin
                path_points = []
                path_points.append((parsed_path.point(0).real, parsed_path.point(0).imag))
                path_points.append((parsed_path.point(1).real, parsed_path.point(1).imag))
                if (path_points[0][0]-x_text)**2 + (path_points[0][1]-y_text)**2 > (path_points[1][0]-x_text)**2 + (path_points[1][1]-y_text)**2:
                    point = 0
                else:
                    point = 1
                end_points.append(path_points[point])

            scale_bars[match.group("axis")] = {}
            if match.group("axis") == 'x':
                scale_bars[match.group("axis")]['ref'] = abs(end_points[1][0] - end_points[0][0])
            elif match.group("axis") == 'y':
                scale_bars[match.group("axis")]['ref'] = abs(end_points[1][1] - end_points[0][1])
            scale_bars[match.group("axis")]['real'] = float(match.group("value"))

        return scale_bars

    @property
    @cache
    def scaling_factors(self):
        scaling_factors = {self.xlabel: 1, self.ylabel: 1}
        for text in self.svg.getElementsByTagName('text'):

            # parse text content
            match = re.match(label_patterns['scale_bar'], SVGPlot._text_value(text))

            if match:
                scaling_factors[match.group("axis")] = float(match.group("value"))

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

        >>> from io import StringIO
        >>> svg = StringIO(r'''
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
        ... </svg>''')
        >>> plot = SVGPlot(svg)
        >>> plot.from_svg(0, 100)
        (0.0, 0.0)
        >>> plot.from_svg(100, 0)
        (1.0, 1.0)

        A typical plot. Like the above but the origin is shifted and the two
        axes are not scaled equally. Here (1024, 512) is mapped to (0, 0) and
        (1124, 256) is mapped to (1, 1)::

        >>> from io import StringIO
        >>> svg = StringIO(r'''
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
        ... </svg>''')
        >>> plot = SVGPlot(svg)
        >>> plot.from_svg(1024, 512)
        (0.0, 0.0)
        >>> plot.from_svg(1124, 256)
        (1.0, 1.0)

        A skewed plot. In this plot the axes are not orthogonal. In real plots
        the axes might be non-orthogonal but not as much as in this
        example. Here, one axis goes horizontally from (0, 100) to (100, 100)
        and the other axis goes at an angle from (0, 100) to (100, 0)::

        >>> from io import StringIO
        >>> svg = StringIO(r'''
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
        ... </svg>''')
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

        >>> from io import StringIO
        >>> svg = StringIO(r'''
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
        ... </svg>''')
        >>> SVGPlot(svg).transformation
        array([[ 0.01,  0.  ,  0.  ],
               [ 0.  , -0.01,  1.  ],
               [ 0.  ,  0.  ,  1.  ]])

        A typical plot. Like the above but the origin is shifted and the two
        axes are not scaled equally. Here (1000, 500) is mapped to (0, 0) and
        (1100, 300) is mapped to (1, 1)::

        >>> from io import StringIO
        >>> svg = StringIO(r'''
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
        ... </svg>''')
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

        >>> from io import StringIO
        >>> svg = StringIO(r'''
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
        ... </svg>''')
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
        A = dot(A, [
            [1/self.scaling_factors[self.xlabel], 0, 0],
            [0, 1/self.scaling_factors[self.ylabel], 0],
            [0, 0, 1],
        ])

        return A

    @classmethod
    def _text_value(cls, node):
        r"""
        Return the text content of a node (including the text of its children) such as a `<text>` node.

        EXAMPLES::

        >>> svg = minidom.parseString('<text> text </text>')
        >>> SVGPlot._text_value(svg)
        'text'

        >>> svg = minidom.parseString('<text> te<!-- comment -->xt </text>')
        >>> SVGPlot._text_value(svg)
        'text'

        >>> svg = minidom.parseString('<text><tspan>te</tspan><tspan>xt</tspan></text>')
        >>> SVGPlot._text_value(svg)
        'text'

        """
        if node.nodeType == Node.TEXT_NODE:
            return node.data.strip()
        return "".join(SVGPlot._text_value(child) for child in node.childNodes)

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
        labeled_paths = {key: [] for key in label_patterns}

        groups = set(path.parentNode for path in self.svg.getElementsByTagName('path'))

        for group in groups:
            if group.nodeType != Node.ELEMENT_NODE or group.tagName != 'g':
                logger.warning("Parent of <path> is not a <g>. Ignoring this path and its siblings.")
                continue

            # Determine all the <path>s in this <g>.
            paths = [path for path in group.childNodes if path.nodeType == Node.ELEMENT_NODE and path.tagName == 'path']
            assert paths

            # Determine the label associated to these <path>s
            label = None
            for child in group.childNodes:
                if child.nodeType == Node.COMMENT_NODE:
                    continue
                elif child.nodeType == Node.TEXT_NODE:
                    if SVGPlot._text_value(child):
                        logger.warning(f'Ignoring unexpected text node "{SVGPlot._text_value(child)}" grouped with <path>.')
                elif child.nodeType == Node.ELEMENT_NODE:
                    if child.tagName == 'path':
                        continue
                    if child.tagName != "text":
                        logger.warning(f"Unexpected <{child.tagName}> grouped with <path>. Ignoring unexpected <{child.tagName}>.")
                        continue

                    if label is not None:
                        logger.warning(f'More than one <text> label associated to this <path>. Ignoring all but the first one, i.e., ignoring "{SVGPlot._text_value(child)}".')
                        continue

                    label = child

            if not label:
                logger.warning(f"Ignoring unlabeled <path> and its siblings.")
                continue

            # Parse the label
            for kind in label_patterns:
                match = re.match(label_patterns[kind], SVGPlot._text_value(label))
                if match:
                    labeled_paths[kind].append((label, paths, match))
                    break
            else:
                logger.warning(f'Ignoring <path> with unsupported label "{label}".')

        return labeled_paths

    @property
    @cache
    def curve(self):
        r"""
        Return the path that is tracing the plot in the SVG.

        Return the `<path>` tag that is not used for other purposes such as
        pointing to axis labels.

        EXAMPLES:

        A plot going from (0, 0) to (1, 1)::

        >>> from io import StringIO
        >>> svg = StringIO(r'''
        ... <svg>
        ...   <g>
        ...     <path d="M 0 100 L 100 0" />
        ...     <text>curve: 0</text>
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
        ... </svg>''')
        >>> plot = SVGPlot(svg)
        >>> plot.curve
        [(0.0, 100.0), (100.0, 0.0)]

        """
        curves = [curve for (text, curve, match) in self.labeled_paths['curve'] if self._curve is None or match.group("curve_id") == self._curve]

        if len(curves) == 0:
            raise Exception("No curve {self._curve} found in SVG.")
        if len(curves) > 1:
            raise Exception("More than one curve {self._curve} fonud in SVG.")

        path = curves[0]
        if len(path) == 0:
            raise Exception("Curve has not a single <path>.")
        if len(path) > 1:
            raise NotImplementedError("Cannot handle curve with more than one <path>.")

        if self.sampling_interval:
            # sample path if interval is set
            return self.sample_path(path[0].getAttribute('d'))
        else:
            return self._parse_shape(path[0].getAttribute('d'))

    @classmethod
    def _parse_shape(self, shape):
        r"""
        Return the points on the `shape` which comse from the `d` attribute of
        a `<path>`.

        EXAMPLES::

        >>> SVGPlot._parse_shape('M 0 0 L 1 0 L 1 1 L 0 1 L 0 0')
        [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.0, 0.0)]

        """
        return [(command.end.real, command.end.imag) for command in parse_path(shape)]

    def sample_path(self, path_string):
        '''samples a path with equidistant x segment by segment'''
        path = Path(path_string)
        xmin, xmax, ymin, ymax = path.bbox()
        x_samples = np.linspace(xmin, xmax, int(abs(xmin - xmax)/self.transformed_sampling_interval))
        points = []
        for segment in path:
            segment_path = Path(segment)
            xmin_segment, xmax_segment, _, _ = segment.bbox()
            segment_points = [[], []]

            for x in x_samples:
                # only sample the x within the segment
                if x >= xmin_segment and x <= xmax_segment:
                    intersects = Path(Line(complex(x, ymin), complex(x, ymax))).intersect(segment_path)
                    # it is possible that a segment includes both scan directions
                    # which leads to two intersections
                    for i in range(len(intersects)):
                        point = intersects[i][0][1].point(intersects[i][0][0])
                        segment_points[i].append((point.real, point.imag))

            # second intersection is appended in reverse order!!
            if len(segment_points[1]) > 0:
                segment_points[0].extend(segment_points[1][::-1])
            # sometimes segments are shorter than sampling interval
            if len(segment_points[0]) > 0:
                first_segment_point = (segment.point(0).real, segment.point(0).imag)

                if (segment_points[0][-1][0]-first_segment_point[0])**2+(segment_points[0][-1][1]-first_segment_point[1])**2 > (segment_points[0][0][0]-first_segment_point[0])**2+(segment_points[0][0][1]-first_segment_point[1])**2:
                    points.extend(segment_points[0])
                else:
                    points.extend(segment_points[0][::-1])

        return np.array(points)

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

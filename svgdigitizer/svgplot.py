from svg.path import parse_path
from svgpathtools import Path, Line
from xml.dom import minidom, Node
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from functools import cached_property
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

    EXAMPLES:

    An instance of this class can be created from a specially prepared SVG
    file. There must at least be a `<path>` with a corresponding label::

    >>> from io import StringIO
    >>> svg = StringIO(r'''
    ... <svg>
    ...   <g>
    ...     <path d="M 0 0 L 100 100" />
    ...     <text>curve: 0</text>
    ...   </g>
    ...   <g>
    ...     <path d="M 0 0 L 100 0" />
    ...     <text x="0" y="0">x1: 0</text>
    ...   </g>
    ...   <g>
    ...     <path d="M 0 0 L 100 0" />
    ...     <text x="100" y="0">x2: 1</text>
    ...   </g>
    ...   <g>
    ...     <path d="M 0 0 L 0 100" />
    ...     <text x="0" y="0">y1: 0</text>
    ...   </g>
    ...   <g>
    ...     <path d="M 0 0 L 0 100" />
    ...     <text x="0" y="100">y2: 1</text>
    ...   </g>
    ... </svg>''')
    >>> plot = SVGPlot(svg)
    >>> plot.dfs
    [     x    y
    0  1.0  1.0
    1  1.0  1.0]

    """
    def __init__(self, svg, xlabel=None, ylabel=None, sampling_interval=None):
        '''filename: should be a valid svg file created according to the documentation'''

        self.xlabel = xlabel or 'x'
        self.ylabel = ylabel or 'y'

        self.doc = minidom.parse(svg)
        self.ref_points, self.real_points = self.get_points()

        self.trafo = {}
        for axis in ['x','y']:
            self.trafo[axis] = self.get_trafo(axis)

        self.sampling_interval = sampling_interval

        self.get_parsed()
        self.create_df()

    @cached_property
    def transformed_sampling_interval(self):
        factor = 1/((self.trafo['x'](self.sampling_interval)-self.trafo['x'](0))/(self.sampling_interval/1000))
        return factor

    def get_points(self):
        '''Creates:
        ref_points: relative values of the spheres/ellipses in the svg file.
        real_points: real values of the points given in the title text of the svg file.'''
        ref_points = {}
        real_points = {}

        for i in self.labeled_paths['ref_point']:
            text, paths, regex_match = i

            ref_point_id = regex_match.group("point")
            real_points[ref_point_id] = float(regex_match.group("value"))

            x_text = float(text.getAttribute('x'))
            y_text = float(text.getAttribute('y'))

            parsed_path = parse_path(paths[0].getAttribute('d'))

            # always take the point of the path which is further away from text origin
            path_points = []
            path_points.append((parsed_path.point(0).real, parsed_path.point(0).imag))
            path_points.append((parsed_path.point(1).real, parsed_path.point(1).imag))
            if (((path_points[0][0]-x_text)**2 + (path_points[0][1]-y_text)**2)**0.5 >
            ((path_points[1][0]-x_text)**2 + (path_points[1][1]-y_text)**2)**0.5):
                point = 0
            else:
                point = 1

            ref_points[ref_point_id] = {'x': path_points[point][0], 'y': path_points[point][1]}

        return ref_points, real_points

    @cached_property
    def scale_bars(self):
        scale_bars = {}


        for i in self.labeled_paths['scale_bar']:
            text, paths, regex_match = i


            x_text = float(text.getAttribute('x'))
            y_text = float(text.getAttribute('y'))

            end_points = []
            for path in paths:
                parsed_path = parse_path(path.getAttribute('d'))
            # always take the point of the path which is further away from text origin
                path_points = []
                path_points.append((parsed_path.point(0).real, parsed_path.point(0).imag))
                path_points.append((parsed_path.point(1).real, parsed_path.point(1).imag))
                if (((path_points[0][0]-x_text)**2 + (path_points[0][1]-y_text)**2)**0.5 >
                ((path_points[1][0]-x_text)**2 + (path_points[1][1]-y_text)**2)**0.5):
                    point = 0
                else:
                    point = 1
                end_points.append(path_points[point])

            scale_bars[regex_match.group("axis")] = {}
            if regex_match.group("axis") == 'x':
                scale_bars[regex_match.group("axis")]['ref'] = abs(end_points[1][0] - end_points[0][0] )
            elif regex_match.group("axis") == 'y':
                scale_bars[regex_match.group("axis")]['ref'] = abs(end_points[1][1] - end_points[0][1])
            scale_bars[regex_match.group("axis")]['real'] = float(regex_match.group("value"))

        return scale_bars

    @cached_property
    def scaling_factors(self):
        scaling_factors = {'x': 1, 'y': 1}
        for text in self.doc.getElementsByTagName('text'):

            # parse text content
            regex_match = re.match(label_patterns['scale_bar'], SVGPlot._text_value(text))

            if regex_match:
                scaling_factors[regex_match.group("axis")] = float(regex_match.group("value"))

        return scaling_factors

    def get_parsed(self):
        '''cuve function'''
        self.allresults = {}
        for pathid, pvals in self.paths.items():
            self.allresults[pathid] = self.get_real_values(pvals)


    def get_trafo(self, axis):
        # we assume a rectangular plot
        p_real = self.real_points
        p_ref = self.ref_points
        try:
            mref = (p_real[f'{axis}2'] - p_real[f'{axis}1']) / (p_ref[f'{axis}2'][axis] - p_ref[f'{axis}1'][axis]) / self.scaling_factors[axis]
            trafo = lambda pathdata: mref * (pathdata - p_ref[f'{axis}1'][axis]) + p_real[f'{axis}1']
        except KeyError:
            mref = -1/self.scale_bars[axis]['ref'] * self.scale_bars[axis]['real']  / self.scaling_factors[axis] # unclear why we need negative sign: now I know, position of origin !!
            trafo = lambda pathdata: mref * (pathdata - p_ref[f'{axis}1'][axis]) + p_real[f'{axis}1']
        return trafo

    def get_real_values(self, xpathdata):
        xnorm = self.trafo['x'](xpathdata[:, 0])
        ynorm = self.trafo['y'](xpathdata[:, 1])
        return np.array([xnorm, ynorm])

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

    @cached_property
    def labeled_paths(self):
        r"""
        All paths with their corresponding label.

        We only consider paths which are grouped with a label, i.e., a `<text>`
        element. These text elements then tell us about the meaning of that
        path, e.g., the path that is labeled as `curve` is the actual graph we
        are going to extract the (x, y) coordinate pairs from.
        """
        labeled_paths = {key: [] for key in label_patterns}

        groups = set(path.parentNode for path in self.doc.getElementsByTagName('path'))

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

    @cached_property
    def paths(self):
        r"""
        Return the paths that are tracing plots in the SVG, i.e., return all
        the `<path>` tags that are not used for other purposes such as pointing
        to axis labels.
        """

        data_paths = {}
        for i in self.labeled_paths['curve']:
            text, paths, regex_match = i

            if not self.sampling_interval:
                # only consider first path since every curve has a label
                data_paths[paths[0].getAttribute('id')] = self.parse_pathstring(paths[0].getAttribute('d'))
            # sample path if interval set
            elif self.sampling_interval:
                data_paths[paths[0].getAttribute('id')] = self.sample_path(paths[0].getAttribute('d'))

        return data_paths


    def parse_pathstring(self, path_string):
        path = parse_path(path_string)
        posxy = []
        for e in path:
            x0 = e.start.real
            y0 = e.start.imag
            x1 = e.end.real
            y1 = e.end.imag
            posxy.append([x0, y0])

        return np.array(posxy)


    def sample_path(self, path_string):
        '''samples a path with equidistant x segment by segment'''
        path = Path(path_string)
        xmin, xmax, ymin, ymax = path.bbox()
        x_samples = np.linspace(xmin, xmax, int(abs(xmin - xmax)/self.transformed_sampling_interval))
        points = []
        for segment in path:
            segment_path = Path(segment)
            xmin_segment, xmax_segment, _, _ = segment.bbox()
            segment_points = [[],[]]

            for x in x_samples:
                # only sample the x within the segment
                if x >= xmin_segment and x <= xmax_segment:
                    intersects = Path(Line(complex(x,ymin),complex(x,ymax))).intersect(segment_path)
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

                if (((segment_points[0][-1][0]-first_segment_point[0])**2+(segment_points[0][-1][1]-first_segment_point[1])**2)**0.5 >
                    ((segment_points[0][0][0]-first_segment_point[0])**2+(segment_points[0][0][1]-first_segment_point[1])**2)**0.5):
                    points.extend(segment_points[0])
                else:
                    points.extend(segment_points[0][::-1])

        return np.array(points)

    def create_df(self):
        data = [self.allresults[list(self.allresults)[idx]].transpose() for idx, i in enumerate(self.allresults)]
        self.dfs = [pd.DataFrame(data[idx],columns=[self.xlabel,self.ylabel]) for idx, i in enumerate(data)]

    def plot(self):
        '''curve function'''
        #resdict = self.allresults
        #for i, v in resdict.items():
        #    plt.plot(v[0], v[1], label=i)

        fig, ax = plt.subplots(1,1)
        for i, df in enumerate(self.dfs):
            df.plot(x=self.xlabel, y=self.ylabel, ax=ax, label=f'curve {i}')
        # do we want the path in the legend as it was in the previous version?
        #plt.legend()
        plt.xlabel(self.xlabel)
        plt.ylabel(self.ylabel)
        plt.tight_layout()
        plt.show()

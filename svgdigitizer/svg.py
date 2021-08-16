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
from functools import cache
from xml.dom import minidom, Node
import re


class SVG:
    r"""
    An Scalable Vector Graphics (SVG) document.

    Provides access to the objects in an SVG while hiding details such as
    transformation attributes.
    """
    def __init__(self, svg):
        self.svg = minidom.parse(svg)

    class LabeledPaths:
        r"""
        Paths associated to a label.
        """
        def __init__(self, label, paths, match):
            self.label = SVG.Label(label, match)
            self.paths = [SVG.LabeledPath(path, label) for path in paths]

        def __repr__(self):
            return repr(str(self.label))

    class Label:
        def __init__(self, label, match):
            self._label = label
            self._value = SVG._text_value(label)
            for key, value in match.groupdict().items():
                setattr(self, key, value)

        def __eq__(self, other):
            return isinstance(other, SVG.Label) and self._label is other._label

        def __ne__(self, other):
            return not (self == other)

        def __str__(self):
            return self._value

    class LabeledPath:
        r"""
        Wraps a `<path>` applying all the transformations from parents.
        """
        def __init__(self, path, label):
            self._path = path
            self._label = label

        @property
        def far(self):
            r"""
            Return the end point of this path that is furthest away from the label.
            """
            # TODO: Transform
            text = float(self._label.getAttribute('x')), float(self._label.getAttribute('y'))
            endpoints = [self.points[0], self.points[-1]]
            return max(endpoints, key=lambda p: (text[0] - p[0]) ** 2 + (text[1] - p[1]) ** 2)

        @property
        def points(self):
            r"""
            Return the points defining this path.

            This returns the raw points in the `d` attribute, ignoring the
            commands that connect these points, i.e., ignoring whether these
            points are connected by `M` commands that do not actually draw
            anything, or any kind of visible curve.
            """
            return [(self.path[0].start.real, self.path[0].start.imag)] + [(command.end.real, command.end.imag) for command in self.path]

        @property
        def path(self):
            r"""
            Return the path transformed to the global SVG coordinate system,
            i.e., with all `transform` attributes resolved.

            Note that we do not resolve CSS `style` transformations yet.

            EXAMPLES::

                >>> from io import StringIO
                >>> svg = SVG(StringIO(r'''
                ... <svg>
                ...   <g>
                ...     <path d="M 0 100 L 100 0" />
                ...     <text>curve: 0</text>
                ...   </g>
                ... </svg>'''))
                >>> svg.get_labeled_paths()[0].paths[0].path
                Path(Line(start=100j, end=(100+0j)))

            TESTS:

            Transformations on the path are resolved::

                >>> from io import StringIO
                >>> svg = SVG(StringIO(r'''
                ... <svg>
                ...   <g>
                ...     <path d="M 0 100 L 100 0" transform="translate(100 200)" />
                ...     <text>curve: 0</text>
                ...   </g>
                ... </svg>'''))
                >>> svg.get_labeled_paths()[0].paths[0].path
                Path(Line(start=(100+300j), end=(200+200j)))

            Transformations on the containing group are resolved::

                >>> from io import StringIO
                >>> svg = SVG(StringIO(r'''
                ... <svg>
                ...   <g transform="translate(-100 -200)">
                ...     <path d="M 0 100 L 100 0" transform="translate(100 200)" />
                ...     <text>curve: 0</text>
                ...   </g>
                ... </svg>'''))
                >>> svg.get_labeled_paths()[0].paths[0].path
                Path(Line(start=100j, end=(100+0j)))

            """
            from svgpathtools import Path
            return SVG.transform(self._path)

    def get_labeled_paths(self, pattern=""):
        r"""
        Return all paths with their corresponding `<text>` label if it matches `pattern`.

        EXAMPLES::

        >>> from io import StringIO
        >>> svg = SVG(StringIO(r'''
        ... <svg>
        ...   <g>
        ...     <path d="M 0 100 L 100 0" />
        ...     <text>curve: 0</text>
        ...   </g>
        ... </svg>'''))
        >>> svg.get_labeled_paths("curve")
        ['curve: 0']
        >>> svg.get_labeled_paths("text")
        []
        >>> svg.get_labeled_paths()
        ['curve: 0']

        """
        labeled_paths = []

        groups = set(path.parentNode for path in self.svg.getElementsByTagName('path'))

        for group in groups:
            if group.nodeType != Node.ELEMENT_NODE or group.tagName != 'g':
                logger.warning("Parent of <path> is not a <g>. Ignoring this path and its siblings.")
                continue

            # Determine the label associated to these <path>s
            label = None
            for child in group.childNodes:
                if child.nodeType == Node.COMMENT_NODE:
                    continue
                elif child.nodeType == Node.TEXT_NODE:
                    if SVG._text_value(child):
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

            # Determine all the <path>s in this <g>.
            paths = [path for path in group.childNodes if path.nodeType == Node.ELEMENT_NODE and path.tagName == 'path']
            assert paths

            # Parse the label
            match = re.match(pattern, SVG._text_value(label), re.IGNORECASE)
            if match:
                labeled_paths.append(SVG.LabeledPaths(label, paths, match))

        return labeled_paths

    def get_texts(self, pattern=""):
        labels = []
        for text in self.svg.getElementsByTagName("text"):
            match = re.match(pattern, SVG._text_value(text), re.IGNORECASE)
            if match:
                labels.append(SVG.Label(text, match))

        return labels

    @classmethod
    def get_transform(cls, element):
        from svgpathtools.parser import parse_transform

        if element is None or element.nodeType == Node.DOCUMENT_NODE:
            return parse_transform(None)

        return cls.get_transform(element.parentNode).dot(parse_transform(element.getAttribute('transform')))

    @classmethod
    def transform(cls, element):
        transformation = cls.get_transform(element)

        if element.getAttribute('d'):
            # element is like a path
            from svgpathtools.path import transform
            from svgpathtools.parser import parse_path
            element = transform(parse_path(element.getAttribute('d')), transformation)
        else:
            raise NotImplementedError(f"Unsupported element {element}.")

        return element

    @classmethod
    def _text_value(cls, node):
        r"""
        Return the text content of a node (including the text of its children) such as a `<text>` node.

        EXAMPLES::

        >>> svg = minidom.parseString('<text> text </text>')
        >>> SVG._text_value(svg)
        'text'

        >>> svg = minidom.parseString('<text> te<!-- comment -->xt </text>')
        >>> SVG._text_value(svg)
        'text'

        >>> svg = minidom.parseString('<text><tspan>te</tspan><tspan>xt</tspan></text>')
        >>> SVG._text_value(svg)
        'text'

        """
        if node.nodeType == Node.TEXT_NODE:
            return node.data.strip()
        return "".join(SVG._text_value(child) for child in node.childNodes)

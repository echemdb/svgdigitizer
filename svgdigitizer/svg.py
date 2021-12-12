r"""
Provides access to the elements of an SVG tracing a plot for the digitiver.

EXAMPLES:

A simple SVG consisting of a path grouped with a label::

    >>> from io import StringIO
    >>> svg = SVG(StringIO(r'''
    ... <svg>
    ...   <g>
    ...     <path d="M 0 100 L 100 0" />
    ...     <text x="0" y="0">curve: 0</text>
    ...   </g>
    ... </svg>'''))

We can access the path by its label::

    >>> paths = svg.get_labeled_paths("curve")

We extract the single group with the label "curve" and the single path in this
group::

    >>> curve = paths[0][0]
    >>> curve
    Path "curve: 0"

We can query the path for the endpoints of its segments::

    >>> curve.points
    [(0.0, 100.0), (100.0, 0.0)]

We can recover the specification of that segment as it is encoded in the SVG::

    >>> curve.path
    Path(Line(start=100j, end=(100+0j)))

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
import re
from xml.dom import Node, minidom

logger = logging.getLogger("svg")


class SVG:
    r"""
    An Scalable Vector Graphics (SVG) document.

    Provides access to the objects in an SVG while hiding details such as
    transformation attributes.

    EXAMPLES:

    An SVG can be created from a string or from a (file) stream::

        >>> svg = SVG(r'''
        ... <svg>
        ...     <!-- an empty SVG -->
        ... </svg>''')
        >>> svg
        SVG('<?xml version="1.0" ?><svg>\n    <!-- an empty SVG -->\n</svg>')

    ::

        >>> from io import StringIO
        >>> svg = SVG(StringIO(r'''
        ... <svg>
        ...     <!-- an empty SVG -->
        ... </svg>'''))
        >>> svg
        SVG('<?xml version="1.0" ?><svg>\n    <!-- an empty SVG -->\n</svg>')

    """

    def __init__(self, svg):
        if isinstance(svg, str):
            self.svg = minidom.parseString(svg)
        else:
            self.svg = minidom.parse(svg)

    def __repr__(self):
        r"""
        Return a printable representation of this SVG object.

        EXAMPLES::

            >>> svg = SVG(r'''
            ... <svg>
            ...     <!-- an empty SVG -->
            ... </svg>''')
            >>> svg
            SVG('<?xml version="1.0" ?><svg>\n    <!-- an empty SVG -->\n</svg>')

        """
        return f"SVG({repr(self.svg.toxml())})"

    def get_labeled_paths(self, pattern=""):
        r"""
        Return all paths with their corresponding `<text>` label if it matches `pattern`.

        EXAMPLES::

            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 100 L 100 0" />
            ...     <text x="0" y="0">curve: 0</text>
            ...   </g>
            ... </svg>'''))
            >>> svg.get_labeled_paths("curve")
            [[Path "curve: 0"]]
            >>> svg.get_labeled_paths("text")
            []
            >>> svg.get_labeled_paths()
            [[Path "curve: 0"]]

        """
        labeled_paths = []

        groups = set(path.parentNode for path in self.svg.getElementsByTagName("path"))

        for group in groups:
            if group.nodeType != Node.ELEMENT_NODE or group.tagName != "g":
                logger.warning(
                    "Parent of <path> is not a <g>. Ignoring this path and its siblings."
                )
                continue

            # Determine the label associated to these <path>s
            label = None
            for child in group.childNodes:
                if child.nodeType == Node.COMMENT_NODE:
                    continue

                if child.nodeType == Node.TEXT_NODE:
                    if SVG._text_value(child):
                        logger.warning(
                            f'Ignoring unexpected text node "{SVG._text_value(child)}" grouped with <path>.'
                        )
                elif child.nodeType == Node.ELEMENT_NODE:
                    if child.tagName == "path":
                        continue
                    if child.tagName != "text":
                        logger.warning(
                            f"Unexpected <{child.tagName}> grouped with <path>. Ignoring unexpected <{child.tagName}>."
                        )
                        continue

                    if label is not None:
                        logger.warning(
                            f'More than one <text> label associated to this <path>. Ignoring all but the first one, i.e., ignoring "{SVG._text_value(child)}".'
                        )
                        continue

                    label = child

            if not label:
                logger.warning("Ignoring unlabeled <path> and its siblings.")
                continue

            # Determine all the <path>s in this <g>.
            paths = [
                path
                for path in group.childNodes
                if path.nodeType == Node.ELEMENT_NODE and path.tagName == "path"
            ]
            assert paths

            # Parse the label
            match = re.match(pattern, SVG._text_value(label), re.IGNORECASE)
            if match:
                labeled_paths.append(LabeledPaths(label, paths, match))

        return labeled_paths

    def get_texts(self, pattern=""):
        r"""
        Return all `<text>` elements that match `pattern`.

        EXAMPLES::

            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 100 L 100 0" />
            ...     <text x="0" y="0">curve: 0</text>
            ...   </g>
            ... </svg>'''))
            >>> svg.get_texts()
            [<text>curve: 0</text>]

        Named matches are directly available as attributes on the returned
        texts::

            >>> curves = svg.get_texts("curve: (?P<name>.*)")
            >>> curves[0].name
            '0'

        """
        labels = []
        for text in self.svg.getElementsByTagName("text"):
            match = re.match(pattern, SVG._text_value(text), re.IGNORECASE)
            if match:
                labels.append(Text(text, match))

        return labels

    @classmethod
    def _get_transform(cls, element):
        r"""
        Return the transformation needed to bring `element` into the root
        context of the SVG document.

        EXAMPLES::

            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g transform="translate(10, 10)">
            ...     <text x="0" y="0">curve: 0</text>
            ...   </g>
            ... </svg>'''))
            >>> SVG._get_transform(svg.svg.getElementsByTagName("text")[0])
            array([[ 1.,  0., 10.],
                   [ 0.,  1., 10.],
                   [ 0.,  0.,  1.]])

        """
        from svgpathtools.parser import parse_transform

        if element is None or element.nodeType == Node.DOCUMENT_NODE:
            return parse_transform(None)

        return cls._get_transform(element.parentNode).dot(
            parse_transform(element.getAttribute("transform"))
        )

    @classmethod
    def transform(cls, element):
        r"""
        Return a transformed version of `element` with all `transform` attributes applied.

        EXAMPLES:

        Transformations can be applied to text elements::

            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g transform="translate(100, 10)">
            ...     <text x="0" y="0" transform="translate(100, 10)">curve: 0</text>
            ...   </g>
            ... </svg>'''))
            >>> transformed = svg.transform(svg.svg.getElementsByTagName("text")[0])
            >>> transformed.toxml()
            '<text x="200.0" y="20.0">curve: 0</text>'

        Transformations can be applied to paths::

            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g transform="translate(100, 10)">
            ...     <path d="M 0 0 L 1 1" transform="translate(100, 10)" />
            ...   </g>
            ... </svg>'''))
            >>> svg.transform(svg.svg.getElementsByTagName("path")[0])
            Path(Line(start=(200+20j), end=(201+21j)))

        """
        transformation = cls._get_transform(element)

        if element.getAttribute("d"):
            # element is like a path
            from svgpathtools.parser import parse_path
            from svgpathtools.path import transform

            element = transform(parse_path(element.getAttribute("d")), transformation)
        elif element.hasAttribute("x") and element.hasAttribute("y"):
            # elements with an explicit location such as <text>
            x = float(element.getAttribute("x"))
            y = float(element.getAttribute("y"))
            x, y, _ = transformation.dot([x, y, 1])

            element = element.cloneNode(deep=True)
            if element.hasAttribute("transform"):
                element.removeAttribute("transform")
            element.setAttribute("x", str(x))
            element.setAttribute("y", str(y))
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


class Text:
    r"""
    A `<text>` element in an SVG such as a label for a path.

    EXAMPLES::

        >>> from io import StringIO
        >>> svg = SVG(StringIO(r'''
        ... <svg>
        ...   <text x="0" y="0">curve: 0</text>
        ... </svg>'''))
        >>> svg.get_texts()
        [<text>curve: 0</text>]

    The coordinates of the text in the SVG coordinate system are exposed as
    `.x` and `.y`::

        >>> from io import StringIO
        >>> svg = SVG(StringIO(r'''
        ... <svg>
        ...   <text x="0" y="0" transform="translate(10,100)">curve: 0</text>
        ... </svg>'''))
        >>> text = svg.get_texts()[0]
        >>> text.x
        10.0
        >>> text.y
        100.0

    """

    def __init__(self, label, match):
        self._label = label
        self._value = SVG._text_value(label)

        transformed = SVG.transform(label)
        self.x = float(transformed.getAttribute("x"))
        self.y = float(transformed.getAttribute("y"))

        for key, value in match.groupdict().items():
            setattr(self, key, value)

    def __repr__(self):
        return f"<text>{self._value}</text>"

    def __str__(self):
        return self._value


class LabeledPaths(list):
    r"""
    A collection of paths associated to a single label.

    EXAMPLES::

        >>> from io import StringIO
        >>> svg = SVG(StringIO(r'''
        ... <svg>
        ...   <g>
        ...     <path d="M 0 100 L 100 0" />
        ...     <text x="0" y="0">curve: 0</text>
        ...   </g>
        ... </svg>'''))
        >>> svg.get_labeled_paths()
        [[Path "curve: 0"]]

    """

    def __init__(self, label, paths, match):
        if not paths:
            raise ValueError("LabeledPaths must consist of at least one path.")

        self._label = Text(label, match)
        super().__init__([LabeledPath(path, self._label) for path in paths])

    @property
    def label(self):
        r"""
        Return the label associated to the paths.

        EXAMPLES::

            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 100 L 100 0" />
            ...     <text x="0" y="0">curve: 0</text>
            ...   </g>
            ... </svg>'''))
            >>> svg.get_labeled_paths()[0].label
            <text>curve: 0</text>

        """
        return self._label


class LabeledPath:
    r"""
    A `<path>` element in an SVG such as a trace of a plot with a text label.

    EXAMPLES::

        >>> from io import StringIO
        >>> svg = SVG(StringIO(r'''
        ... <svg>
        ...   <g>
        ...     <path d="M 0 100 L 100 0" />
        ...     <text x="0" y="0">curve: 0</text>
        ...   </g>
        ... </svg>'''))
        >>> svg.get_labeled_paths()[0][0]
        Path "curve: 0"

    """

    def __init__(self, path, label):
        self._path = path
        self.label = label

    @property
    def far(self):
        r"""
        Return the end point of this path that is furthest away from the label.

        EXAMPLES::

            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 100 L 100 0" />
            ...     <text x="0" y="100">curve: 0</text>
            ...   </g>
            ... </svg>'''))
            >>> path = svg.get_labeled_paths()[0][0]
            >>> path.far
            (100.0, 0.0)

        """
        text = self.label.x, self.label.y
        endpoints = [self.points[0], self.points[-1]]
        return max(
            endpoints, key=lambda p: (text[0] - p[0]) ** 2 + (text[1] - p[1]) ** 2
        )

    @classmethod
    def path_points(cls, path):
        r"""
        Return the points defining this path.

        This returns the raw points in the `d` attribute, ignoring the
        commands that connect these points, i.e., ignoring whether these
        points are connected by `M` commands that do not actually draw
        anything, or any kind of visible curve.
        """
        return [(path[0].start.real, path[0].start.imag)] + [
            (command.end.real, command.end.imag) for command in path
        ]

    @property
    def points(self):
        r"""
        Return the points defining this path.

        This returns the raw points in the `d` attribute, ignoring the
        commands that connect these points, i.e., ignoring whether these
        points are connected by `M` commands that do not actually draw
        anything, or any kind of visible curve.
        """
        return LabeledPath.path_points(self.path)

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
            ...     <text x="0" y="0">curve: 0</text>
            ...   </g>
            ... </svg>'''))
            >>> svg.get_labeled_paths()[0][0].path
            Path(Line(start=100j, end=(100+0j)))

        TESTS:

        Transformations on the path are resolved::

            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 100 L 100 0" transform="translate(100 200)" />
            ...     <text x="0" y="0">curve: 0</text>
            ...   </g>
            ... </svg>'''))
            >>> svg.get_labeled_paths()[0][0].path
            Path(Line(start=(100+300j), end=(200+200j)))

        Transformations on the containing group are resolved::

            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g transform="translate(-100 -200)">
            ...     <path d="M 0 100 L 100 0" transform="translate(100 200)" />
            ...     <text x="0" y="0">curve: 0</text>
            ...   </g>
            ... </svg>'''))
            >>> svg.get_labeled_paths()[0][0].path
            Path(Line(start=100j, end=(100+0j)))

        """
        return SVG.transform(self._path)

    def __repr__(self):
        return f'Path "{self.label}"'

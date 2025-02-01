r"""
Reconstructs scientific plots with units and allows reconstructing a
time axis.
In principle the class :class:`SVGFigure` adds more functionality than
the class :class:`~svgdigitizer.svgplot.SVGPlot`.

A detailed description of different kinds of plots can be found
in the :doc:`documentation </usage>`.

"""
# ********************************************************************
#  This file is part of svgdigitizer.
#
#        Copyright (C) 2021-2023 Albert Engstfeld
#        Copyright (C) 2021-2023 Julian Rüth
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
from functools import cached_property

import astropy.units as u
import matplotlib.pyplot as plt

from svgdigitizer.exceptions import SVGAnnotationError

logger = logging.getLogger("svgfigure")


class SVGFigure:
    """
    A digitized plot derived from an SVG file,
    which provides access to the objects of the figure.

    Typically, the SVG input has been created by tracing a CV from
    a publication with a `<path>` in an SVG editor such as Inkscape. Such a
    path can then be analyzed by this class to produce the coordinates
    corresponding to the original measured values.

    In addition it extracts the units from the labels, and thus allows
    conversion of the data into SI units. Also by providing a text field
    with a ``scan rate`` such as ``scan rate: 50 K / s``, allows reconstructing
    of the time axis of the data.

    A detailed description can also be found in the
    :doc:`documentation </usage>`.

    EXAMPLES:

    The following plot has different kinds of axis units.
    These units must be compatible with the
    `astropy unit module <https://docs.astropy.org/en/stable/units/index.html>`_:

        >>> from svgdigitizer.svg import SVG
        >>> from svgdigitizer.svgplot import SVGPlot
        >>> from svgdigitizer.svgfigure import SVGFigure
        >>> from io import StringIO
        >>> svg = SVG(StringIO(r'''
        ... <svg>
        ...   <g>
        ...     <path d="M 0 100 L 100 0" />
        ...     <text x="0" y="0">curve: 0</text>
        ...   </g>
        ...   <g>
        ...     <path d="M 0 200 L 0 100" />
        ...     <text x="0" y="200">T1: 0 mK</text>
        ...   </g>
        ...   <g>
        ...     <path d="M 100 200 L 100 100" />
        ...     <text x="100" y="200">T2: 1 mK</text>
        ...   </g>
        ...   <g>
        ...     <path d="M -100 100 L 0 100" />
        ...     <text x="-100" y="100">j1: 0 uA / cm2</text>
        ...   </g>
        ...   <g>
        ...     <path d="M -100 0 L 0 0" />
        ...     <text x="-100" y="0">j2: 1 uA / cm2</text>
        ...   </g>
        ...   <text x="-200" y="330">scan rate: 50 K/s</text>
        ... </svg>'''))
        >>> figure = SVGFigure(SVGPlot(svg))

    In addition a text label with a scan rate is provided in the above example,
    which allows reconstructing a time axis from the plot::

        >>> figure.df
                 t    T    j
        0  0.00000  0.0  0.0
        1  0.00002  1.0  1.0

    The data can also be directly converted into SI units::

        >>> figure_si = SVGFigure(SVGPlot(svg), force_si_units=True)
        >>> figure_si.df
                 t      T     j
        0  0.00000  0.000  0.00
        1  0.00002  0.001  0.01

    The units of the data can be retrieved from the data schema

        >>> figure_si.data_schema
        {'fields': [{'name': 'T', 'type': 'number', 'unit': 'K'},
                    {'name': 'j', 'type': 'number', 'unit': 'A / m2'},
                    {'name': 't', 'type': 'number', 'unit': 's'}]}

    The original units in turn can be retrieved from the figure schema

        >>> figure_si.figure_schema
        {'fields': [{'name': 'T', 'type': 'number', 'unit': 'mK', 'orientation': 'horizontal'},
                    {'name': 'j',
                     'type': 'number',
                     'unit': 'uA / cm2',
                     'orientation': 'vertical'}]}

    """

    def __init__(
        self, svgplot, metadata=None, measurement_type="custom", force_si_units=False
    ):
        self.svgplot = svgplot
        self._measurement_type = measurement_type
        self._metadata = metadata or {}
        self.force_si_units = force_si_units

    @staticmethod
    def create_figure(measurement_type=None):
        """
        Creates plots for specific data such as cyclic voltammograms (CV).
        TODO:: Add description and docstring (see issue #177)
        """
        from svgdigitizer.electrochemistry.cv import CV  # pylint: disable=cyclic-import

        if measurement_type == "CV":
            return CV

        raise NotImplementedError(
            f"The specific figure with name `{measurement_type} is currently not supported."
        )

    @cached_property
    def measurement_type(self):
        r"""
        A full name or acronym of the measurement shown in the plot,
        such as `IR`, `Raman`, `I-U profile`, ...

        EXAMPLES:

        The default name is 'custom'::

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
            >>> from svgdigitizer.svgfigure import SVGFigure
            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 200 L 0 100" />
            ...     <text x="0" y="200">x1: 0 V</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">x2: 1 V</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">j1: A / cm2</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">j2: 1 A / cm2</text>
            ...   </g>
            ... </svg>'''))
            >>> figure = SVGFigure(SVGPlot(svg))
            >>> figure.measurement_type
            'custom'

        The type can be specified explicitly.

            >>> figure = SVGFigure(SVGPlot(svg), measurement_type='I-U')
            >>> figure.measurement_type
            'I-U'

        """
        return self._measurement_type

    @cached_property
    def figure_label(self):
        r"""
        An identifier of the plot to distinguish it from other
        figures on the same page.

        The figure name is read from a ``<text>`` in the SVG file
        such as ``<text>figure: 2b</text>``.

        EXAMPLES::

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
            >>> from svgdigitizer.svgfigure import SVGFigure
            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 200 L 0 100" />
            ...     <text x="0" y="200">E1: 0 V</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">E2: 1 V</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">j1: 0 A / cm2</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">j2: 1 A / cm2</text>
            ...   </g>
            ...   <text x="-200" y="330">Figure: 2b</text>
            ... </svg>'''))
            >>> figure = SVGFigure(SVGPlot(svg))
            >>> figure.figure_label
            '2b'

        """
        figure_labels = self.svgplot.svg.get_texts("(?:figure): (?P<label>.+)")

        if len(figure_labels) > 1:
            logger.warning(
                f"More than one text field with figure labels. Ignoring all text fields except for the first: {figure_labels[0]}."
            )

        if not figure_labels:
            figure_label = self._metadata.get("source", {}).get("figure", "")
            if not figure_label:
                logger.warning(
                    "No text with `figure` containing a label such as `figure: 1a` found in the SVG."
                )
            return figure_label

        return figure_labels[0].label

    @cached_property
    def curve_label(self):
        r"""
        A descriptive label for this curve to distinguish it
        from other curves in the same figure.

        The curve label read from a ``<text>`` in the SVG file
        such as ``<text>curve: solid line</text>``.

        EXAMPLES::

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
            >>> from svgdigitizer.svgfigure import SVGFigure
            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 100 L 100 0" />
            ...     <text x="0" y="0">curve: solid line</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 0 200 L 0 100" />
            ...     <text x="0" y="200">E1: 0 V</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">E2: 1 V</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">j1: 0 A / cm2</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">j2: 1 A / cm2</text>
            ...   </g>
            ... </svg>'''))
            >>> figure = SVGFigure(SVGPlot(svg))
            >>> figure.curve_label
            'solid line'

        """
        curve_labels = self.svgplot.svg.get_texts("(?:curve): (?P<label>.+)")

        if len(curve_labels) > 1:
            logger.warning(
                f"More than one text field with curve labels. Ignoring all text fields except for the first: {curve_labels[0]}."
            )

        if not curve_labels:
            return self._metadata.get("source", {}).get("curve", "")

        return curve_labels[0].label

    def _axis_unit(self, label):
        r"""Returns the unit of an axis with a specific label.

        EXAMPLES::

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
            >>> from svgdigitizer.svgfigure import SVGFigure
            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 100 L 100 0" />
            ...     <text x="0" y="0">curve: solid line</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 0 200 L 0 100" />
            ...     <text x="0" y="200">E1: 0 V vs. RHE</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">E2: 1 V vs. RHE</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">j1: 0 A / cm2</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">j2: 1 A / cm2</text>
            ...   </g>
            ... </svg>'''))
            >>> figure = SVGFigure(SVGPlot(svg))
            >>> figure._axis_unit('E')
            'V vs. RHE'

        """
        unit = self.figure_schema.get_field(label).custom["unit"]

        if self.force_si_units:
            if self.unit_is_astropy(unit):
                return (1 * u.Unit(unit)).si.unit.to_string()

        return unit

    @cached_property
    def xunit(self):
        r"""Returns the unit of the x-axis.

        EXAMPLES::

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
            >>> from svgdigitizer.svgfigure import SVGFigure
            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 100 L 100 0" />
            ...     <text x="0" y="0">curve: solid line</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 0 200 L 0 100" />
            ...     <text x="0" y="200">E1: 0 V vs. RHE</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">E2: 1 V vs. RHE</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">j1: 0 A / cm2</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">j2: 1 A / cm2</text>
            ...   </g>
            ... </svg>'''))
            >>> figure = SVGFigure(SVGPlot(svg))
            >>> figure.xunit
            'V vs. RHE'

        Returns the SI unit when the the plot is converted to SI units::

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
            >>> from svgdigitizer.svgfigure import SVGFigure
            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 100 L 100 0" />
            ...     <text x="0" y="0">curve: solid line</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 0 200 L 0 100" />
            ...     <text x="0" y="200">E1: 0 mK</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">E2: 1 mK</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">j1: 0 A / cm2</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">j2: 1 A / cm2</text>
            ...   </g>
            ... </svg>'''))
            >>> figure = SVGFigure(SVGPlot(svg), force_si_units=True)
            >>> figure.xunit
            'K'

        """
        return self._axis_unit(self.svgplot.xlabel)

    @cached_property
    def yunit(self):
        r"""Returns the unit of the y-axis.

        EXAMPLES::

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
            >>> from svgdigitizer.svgfigure import SVGFigure
            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 100 L 100 0" />
            ...     <text x="0" y="0">curve: solid line</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 0 200 L 0 100" />
            ...     <text x="0" y="200">E1: 0 V</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">E2: 1 V</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">j1: 0 A / cm2</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">j2: 1 A / cm2</text>
            ...   </g>
            ... </svg>'''))
            >>> figure = SVGFigure(SVGPlot(svg))
            >>> figure.yunit
            'A / cm2'

         Returns the SI unit when the the plot is converted to SI units::

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
            >>> from svgdigitizer.svgfigure import SVGFigure
            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 100 L 100 0" />
            ...     <text x="0" y="0">curve: solid line</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 0 200 L 0 100" />
            ...     <text x="0" y="200">E1: 0 V</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">E2: 1 V</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">j1: 0 A / cm2</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">j2: 1 A / cm2</text>
            ...   </g>
            ... </svg>'''))
            >>> figure = SVGFigure(SVGPlot(svg), force_si_units=True)
            >>> figure.yunit
            'A / m2'

        """
        return self._axis_unit(self.svgplot.ylabel)

    @cached_property
    def comment(self):
        r"""
        Return a comment describing the plot.

        The comment is read from a ``<text>`` field in the SVG file such as ``<text>comment: noisy data</text>``.

        EXAMPLES:

        This example contains a comment::

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
            >>> from svgdigitizer.svgfigure import SVGFigure
            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 200 L 0 100" />
            ...     <text x="0" y="200">x1: 0 V</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">x2: 1 V</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">j1: A / cm2</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">j2: 1 A / cm2</text>
            ...   </g>
            ...   <text x="-200" y="330">scan rate: 50 V/s</text>
            ...   <text x="-400" y="430">comment: noisy data</text>
            ... </svg>'''))
            >>> figure = SVGFigure(SVGPlot(svg))
            >>> figure.comment
            'noisy data'

        This example does not contain a comment::

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
            >>> from svgdigitizer.svgfigure import SVGFigure
            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 200 L 0 100" />
            ...     <text x="0" y="200">x1: 0 V</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">x2: 1 V</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">j1: A / cm2</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">j2: 1 A / cm2</text>
            ...   </g>
            ...   <text x="-200" y="330">scan rate: 50 V/s</text>
            ... </svg>'''))
            >>> figure = SVGFigure(SVGPlot(svg))
            >>> figure.comment
            ''

        """
        comments = self.svgplot.svg.get_texts("(?:comment): (?P<value>.*)")

        if len(comments) > 1:
            logger.warning(
                f"More than one comment. Ignoring all comments except for the first: {comments[0]}."
            )

        if not comments:
            return self._metadata.get("figure description", {}).get("comment", "")

        return comments[0].value

    @cached_property
    def df(self):
        r"""
        Return the figure as a dataframe.

        EXAMPLES:

        A simple x vs. y plot without axis units::

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
            >>> from svgdigitizer.svgfigure import SVGFigure
            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 100 L 100 0" />
            ...     <text x="0" y="0">curve: 0</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 0 200 L 0 100" />
            ...     <text x="0" y="200">E1: 0</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">E2: 1</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">j1: 0</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">j2: 1</text>
            ...   </g>
            ... </svg>'''))
            >>> figure = SVGFigure(SVGPlot(svg))
            >>> figure.df
                 E    j
            0  0.0  0.0
            1  1.0  1.0

        A simple x vs. y plot with units on both axis::

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
            >>> from svgdigitizer.svgfigure import SVGFigure
            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 100 L 100 0" />
            ...     <text x="0" y="0">curve: 0</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 0 200 L 0 100" />
            ...     <text x="0" y="200">E1: 0 V</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">E2: 1 V</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">j1: 0 uA / cm2</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">j2: 1 uA / cm2</text>
            ...   </g>
            ... </svg>'''))
            >>> figure = SVGFigure(SVGPlot(svg))
            >>> figure.df
                 E    j
            0  0.0  0.0
            1  1.0  1.0

        A dataframe with a time axis, reconstructed with a given scan rate::

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
            >>> from svgdigitizer.svgfigure import SVGFigure
            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 100 L 100 0" />
            ...     <text x="0" y="0">curve: 0</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 0 200 L 0 100" />
            ...     <text x="0" y="200">E1: 0 mV</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">E2: 1 mV</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">j1: 0 uA / cm2</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">j2: 1 uA / cm2</text>
            ...   </g>
            ...   <text x="-200" y="330">scan rate: 50 mV / s</text>
            ... </svg>'''))
            >>> figure = SVGFigure(SVGPlot(svg))
            >>> figure.df
                  t    E    j
            0  0.00  0.0  0.0
            1  0.02  1.0  1.0

        A dataframe with a time axis, reconstructed with a given scan rate
        and in SI units::

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
            >>> from svgdigitizer.svgfigure import SVGFigure
            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 100 L 100 0" />
            ...     <text x="0" y="0">curve: 0</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 0 200 L 0 100" />
            ...     <text x="0" y="200">E1: 0 mV</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">E2: 1 mV</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">j1: 0 uA / cm2</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">j2: 1 uA / cm2</text>
            ...   </g>
            ...   <text x="-200" y="330">scan rate: 50 mV / s</text>
            ... </svg>'''))
            >>> figure = SVGFigure(SVGPlot(svg), force_si_units=True)
            >>> figure.df
                  t      E     j
            0  0.00  0.000  0.00
            1  0.02  0.001  0.01

        TESTS:

        A dataframe with a time axis, reconstructed with a given scan rate
        and in SI units, where the y-axis does not have compatible astropy units::

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
            >>> from svgdigitizer.svgfigure import SVGFigure
            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 100 L 100 0" />
            ...     <text x="0" y="0">curve: 0</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 0 200 L 0 100" />
            ...     <text x="0" y="200">E1: 0 mV</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">E2: 1 mV</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">j1: 0 persons</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">j2: 1 persons</text>
            ...   </g>
            ...   <text x="-200" y="330">scan rate: 50 mV / s</text>
            ... </svg>'''))
            >>> figure1 = SVGFigure(SVGPlot(svg), force_si_units=True)
            >>> figure1.df
                  t      E    j
            0  0.00  0.000  0.0
            1  0.02  0.001  1.0

        """
        df = self.svgplot.df.copy()

        if self.force_si_units:
            for column in df.columns:
                column_unit = self.figure_schema.get_field(column).custom["unit"]
                if self.unit_is_astropy(column_unit):
                    self._convert_axis_to_si(df, column)

        if self.scan_rate is not None:
            self._add_time_axis(df)
            return df[["t", self.svgplot.xlabel, self.svgplot.ylabel]]

        return df[[self.svgplot.xlabel, self.svgplot.ylabel]]

    def _convert_axis_to_si(self, df, label):
        r"""
        Scales the values in a df into SI values.

        EXAMPLES::

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
            >>> from svgdigitizer.svgfigure import SVGFigure
            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 100 L 100 0" />
            ...     <text x="0" y="0">curve: 0</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 0 200 L 0 100" />
            ...     <text x="0" y="200">E1: 0 mV</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">E2: 1 mV</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">j1: 0 uA / cm2</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">j2: 1 uA / cm2</text>
            ...   </g>
            ...   <text x="-200" y="330">scan rate: 50 mV / s</text>
            ... </svg>'''))
            >>> figure = SVGFigure(SVGPlot(svg))
            >>> figure._convert_axis_to_si(df = figure.svgplot.df.copy(), label='E')

        """
        quantity = 1 * u.Unit(self.figure_schema.get_field(label).custom["unit"])
        # Convert the axis unit to SI units and use the value
        # of the quantity to convert the original column data.
        df[label] = df[label] * quantity.si.value

    def _add_time_axis(self, df):
        r"""
        Add a time column to the dataframe `df`, based on the :property:`scan_rate`.

        EXAMPLES::

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
            >>> from svgdigitizer.svgfigure import SVGFigure
            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 100 L 100 0" />
            ...     <text x="0" y="0">curve: 0</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 0 200 L 0 100" />
            ...     <text x="0" y="200">E1: 0 cm</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">E2: 1 cm</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">j1: 0 uA / cm2</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">j2: 1 uA / cm2</text>
            ...   </g>
            ...   <text x="-200" y="330">scan rate: 50 cm/s</text>
            ... </svg>'''))
            >>> plot = SVGFigure(SVGPlot(svg), force_si_units=True)
            >>> df = plot.svgplot.df.copy()
            >>> plot._add_time_axis(df)

        """
        x_quantity = 1 * u.Unit(self.xunit)
        if self.force_si_units:
            x_quantity = 1 * x_quantity.si.unit

        factor = (x_quantity / (self.scan_rate)).decompose()

        df["delta_x"] = abs(df[self.svgplot.xlabel].diff().fillna(0))
        df["cumdelta_x"] = df["delta_x"].cumsum()
        df["t"] = df["cumdelta_x"] * factor.value

    @classmethod
    def unit_is_astropy(cls, unit):
        r"""
        Verify if a string is a compatible astropy unit.

        EXAMPLES::

            >>> from svgdigitizer.svgfigure import  SVGFigure
            >>> SVGFigure.unit_is_astropy('mV/s')
            True

        TESTS::

            >>> from svgdigitizer.svgfigure import  SVGFigure
            >>> SVGFigure.unit_is_astropy('mv/s')
            False

        """

        try:
            u.Unit(unit)
        except ValueError as exc:
            # The ValueError raised by astropy is rather useful to figure out
            # possible issues with the provided string.
            logger.warning(exc)
            return False
        return True

    @cached_property
    def scan_rate_labels(self):
        r"""
        Return the scan rate of the plot.

        The scan rate is read from a ``<text>`` in the SVG file such as
        ``<text>scan rate: 50 V / s</text>``.

        EXAMPLES::

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
            >>> from svgdigitizer.svgfigure import SVGFigure
            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 100 L 100 0" />
            ...     <text x="0" y="0">curve: 0</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 0 200 L 0 100" />
            ...     <text x="0" y="200">E1: 0 V</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">E2: 1 V</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">j1: 0 A / cm2</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">j2: 1 A / cm2</text>
            ...   </g>
            ...   <text x="-200" y="330">scan rate: 50 mV / s</text>
            ... </svg>'''))
            >>> figure = SVGFigure(SVGPlot(svg))
            >>> figure.scan_rate_labels
            [<text>scan rate: 50 mV / s</text>]

        """
        return self.svgplot.svg.get_texts(
            "(?:scan rate): (?P<value>-?[0-9.]+) *(?P<unit>.*)"
        )

    @cached_property
    def scan_rate(self):
        r"""
        Return the scan rate of the plot as an astropy quantity,
        when it matches the following criteria.

        The rate must be a unit divided by time or simply a frequency.
        It must be compatible with the unit on the x-axis, i.e.,
        when the x-axis unit is `K` the rate must be `K/s`.

        EXAMPLES::

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
            >>> from svgdigitizer.svgfigure import SVGFigure
            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 100 L 100 0" />
            ...     <text x="0" y="0">curve: 0</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 0 200 L 0 100" />
            ...     <text x="0" y="200">E1: 0 V</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">E2: 1 V</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">j1: 0 A / cm2</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">j2: 1 A / cm2</text>
            ...   </g>
            ...   <text x="-200" y="330">scan rate: 50 mV / s</text>
            ... </svg>'''))
            >>> figure = SVGFigure(SVGPlot(svg))
            >>> figure.scan_rate
            <Quantity 50. mV / s>

        TESTS:

        A plot without a scan rate::

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
            >>> from svgdigitizer.svgfigure import SVGFigure
            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 100 L 100 0" />
            ...     <text x="0" y="0">curve: 0</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 0 200 L 0 100" />
            ...     <text x="0" y="200">E1: 0 V</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">E2: 1 V</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">j1: 0 A / cm2</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">j2: 1 A / cm2</text>
            ...   </g>
            ... </svg>'''))
            >>> figure2 = SVGFigure(SVGPlot(svg))
            >>> figure2.scan_rate

        A plot with a scan rate that does not match with the x-axis units:

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
            >>> from svgdigitizer.svgfigure import SVGFigure
            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 100 L 100 0" />
            ...     <text x="0" y="0">curve: 0</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 0 200 L 0 100" />
            ...     <text x="0" y="200">E1: 0 V</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">E2: 1 V</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">j1: 0 A / cm2</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">j2: 1 A / cm2</text>
            ...   </g>
            ...   <text x="-200" y="330">scan rate: 50 m / s</text>
            ... </svg>'''))
            >>> figure3 = SVGFigure(SVGPlot(svg))
            >>> figure3.scan_rate

        """
        # The scan rate is ignored when the unit on the x-axis is not compatible with astropy.

        if not self.unit_is_astropy(self.xunit):
            logger.warning(
                "Ignoring scan rate since unit on the x-axis is not compatible with astropy."
            )
            return None

        rates = self.scan_rate_labels

        if len(rates) > 1:
            raise SVGAnnotationError(
                "Multiple text fields with a scan rate were provided in the SVG. Remove all but one."
            )

        # Infer the scan rate from the provided metadata

        if len(rates) == 0:
            rate = self._metadata.get("figure description", {}).get("scan rate", {})

            def metadata_rate_consistency():
                if "value" not in rate or "unit" not in rate:
                    logger.warning(
                        "No text with scan rate found in the SVG or provided metadata."
                    )
                    return False

                if not self.unit_is_astropy(rate["unit"]):
                    return False

                if (
                    not (1 * u.Unit(str(rate["unit"])) * u.s).si.unit
                    == (1 * u.Unit(self.xunit)).si.unit
                ):
                    logger.warning(
                        "The unit of the scan rate provided in the metadata is not compatible with the x-axis units."
                    )
                    return False

                return True

            if metadata_rate_consistency():
                return float(rate["value"]) * u.Unit(str(rate["unit"]))

            return None

        svg_rate_unit = rates[0].unit

        if not self.unit_is_astropy(svg_rate_unit):
            return None

        if (
            not (1 * u.Unit(svg_rate_unit) * u.s).si.unit
            == (1 * u.Unit(self.xunit)).si.unit
        ):
            logger.warning(
                "The unit of the scan rate provided in the SVG is not compatible with the x-axis units."
            )
            return None

        return float(rates[0].value) * u.Unit(svg_rate_unit)

    @cached_property
    def data_schema(self):
        # TODO: use intersphinx to link Schema and Fields to frictionless docu (see #151).
        r"""
        A frictionless `Schema` object, including a `Field` object
        describing the data generated with :meth:`df`.
        When the units of the axis in the columns of the :meth:`df` remain unchanged
        and no axis was added, such as a time axis reconstructed from a scan rate,
        ``data_schema`` is almost identical to ``figure_schema``. In the individual fields
        the key `orientation` was removed.
        The units of the individual fields are updated upon transformation of the plot
        to SI units.

        EXAMPLES:

        A plot without a scan rate::

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
            >>> from svgdigitizer.svgfigure import SVGFigure
            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 100 L 100 0" />
            ...     <text x="0" y="0">curve: 0</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 0 200 L 0 100" />
            ...     <text x="0" y="200">E1: 0 V</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">E2: 1 V</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">j1: 0 uA / cm2</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">j2: 1 uA / cm2</text>
            ...   </g>
            ... </svg>'''))
            >>> figure = SVGFigure(SVGPlot(svg))
            >>> figure.data_schema  # doctest: +NORMALIZE_WHITESPACE
            {'fields': [{'name': 'E', 'type': 'number', 'unit': 'V'},
                        {'name': 'j', 'type': 'number', 'unit': 'uA / cm2'}]}

        A plot without a scan rate but incompatible x axis units::

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
            >>> from svgdigitizer.svgfigure import SVGFigure
            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 100 L 100 0" />
            ...     <text x="0" y="0">curve: 0</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 0 200 L 0 100" />
            ...     <text x="0" y="200">E1: 0 V vs. RHE</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">E2: 1 V vs. RHE</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">j1: 0 uA / cm2</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">j2: 1 uA / cm2</text>
            ...   </g>
            ... </svg>'''))
            >>> figure1 = SVGFigure(SVGPlot(svg))
            >>> figure1.data_schema  # doctest: +NORMALIZE_WHITESPACE
            {'fields': [{'name': 'E', 'type': 'number', 'unit': 'V vs. RHE'},
                        {'name': 'j', 'type': 'number', 'unit': 'uA / cm2'}]}

        A plot with a scan rate:

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
            >>> from svgdigitizer.svgfigure import SVGFigure
            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 100 L 100 0" />
            ...     <text x="0" y="0">curve: 0</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 0 200 L 0 100" />
            ...     <text x="0" y="200">E1: 0 V</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">E2: 1 V</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">j1: 0 uA / cm2</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">j2: 1 uA / cm2</text>
            ...   </g>
            ...   <text x="-200" y="330">scan rate: 50 V/s</text>
            ... </svg>'''))
            >>> figure_rate = SVGFigure(SVGPlot(svg))
            >>> figure_rate.data_schema  # doctest: +NORMALIZE_WHITESPACE
            {'fields': [{'name': 'E', 'type': 'number', 'unit': 'V'},
                        {'name': 'j', 'type': 'number', 'unit': 'uA / cm2'},
                        {'name': 't', 'type': 'number', 'unit': 's'}]}

        A plot with a scan rate and converted to SI units:

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
            >>> from svgdigitizer.svgfigure import SVGFigure
            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 100 L 100 0" />
            ...     <text x="0" y="0">curve: 0</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 0 200 L 0 100" />
            ...     <text x="0" y="200">T1: 0 mK</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">T2: 1 mK</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">j1: 0 uA / cm2</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">j2: 1 uA / cm2</text>
            ...   </g>
            ...   <text x="-200" y="330">scan rate: 50 K/s</text>
            ... </svg>'''))
            >>> figure_rate_si = SVGFigure(SVGPlot(svg), force_si_units=True)
            >>> figure_rate_si.data_schema  # doctest: +NORMALIZE_WHITESPACE
            {'fields': [{'name': 'T', 'type': 'number', 'unit': 'K'},
                        {'name': 'j', 'type': 'number', 'unit': 'A / m2'},
                        {'name': 't', 'type': 'number', 'unit': 's'}]}

        """
        from frictionless import Schema, fields

        schema = Schema.from_descriptor(self.figure_schema.to_dict())
        for name in schema.field_names:
            if "orientation" in schema.get_field(name).to_dict():
                del schema.get_field(name).custom["orientation"]

        if self.force_si_units:
            for name in schema.field_names:
                field_unit = schema.get_field(name).custom["unit"]
                if self.unit_is_astropy(field_unit):
                    si_unit = (1 * u.Unit(field_unit)).si.unit.to_string()
                    schema.update_field(name, {"unit": si_unit})

        if self.scan_rate is not None:
            schema.add_field(fields.NumberField(name="t"))
            schema.update_field("t", {"unit": "s"})

        return schema

    @cached_property
    def figure_schema(self):
        # TODO: use intersphinx to link Schema and Fields to frictionless docu (see #151).
        r"""
        A frictionless `Schema` object, including a `Fields` object
        describing the axis of the original plot
        including original units.

        EXAMPLES::

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
            >>> from svgdigitizer.svgfigure import SVGFigure
            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 100 L 100 0" />
            ...     <text x="0" y="0">curve: 0</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 0 200 L 0 100" />
            ...     <text x="0" y="200">E1: 0 V</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">E2: 1 V</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">j1: 0 uA / cm2</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">j2: 1 uA / cm2</text>
            ...   </g>
            ...   <text x="-200" y="330">scan rate: 50 V/s</text>
            ... </svg>'''))
            >>> figure = SVGFigure(SVGPlot(svg))
            >>> figure.figure_schema  # doctest: +NORMALIZE_WHITESPACE
            {'fields': [{'name': 'E', 'type': 'number', 'unit': 'V', 'orientation': 'horizontal'},
                        {'name': 'j', 'type': 'number', 'unit': 'uA / cm2', 'orientation': 'vertical'}]}

        A plot without axis units::

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
            >>> from svgdigitizer.svgfigure import SVGFigure
            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 100 L 100 0" />
            ...     <text x="0" y="0">curve: 0</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 0 200 L 0 100" />
            ...     <text x="0" y="200">E1: 0</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">E2: 1</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">j1: 0</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">j2: 1</text>
            ...   </g>
            ... </svg>'''))
            >>> figure = SVGFigure(SVGPlot(svg))
            >>> figure.figure_schema  # doctest: +NORMALIZE_WHITESPACE
            {'fields': [{'name': 'E', 'type': 'number', 'unit': '', 'orientation': 'horizontal'},
                        {'name': 'j', 'type': 'number', 'unit': '', 'orientation': 'vertical'}]}


        """
        from frictionless import Schema

        schema = Schema.from_descriptor(self.svgplot.figure_schema.to_dict())

        for field in schema.field_names:
            if not schema.get_field(field).custom["unit"]:
                schema.get_field(field).custom["unit"] = ""

        return schema

    @property
    def tags(self):
        r"""
        A list of acronyms commonly used in the community to describe
        the measurement.

        The names are read from a ``<text>`` in the SVG file such as
        ``<text>tags: BCV, HER, OER </text>``.

        EXAMPLES::

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
            >>> from svgdigitizer.svgfigure import SVGFigure
            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 200 L 0 100" />
            ...     <text x="0" y="200">x1: 0 V</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">x2: 1 V</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">j1: A / cm2</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">j2: 1 A / cm2</text>
            ...   </g>
            ...   <text x="-200" y="330">scan rate: 50 V/s</text>
            ...   <text x="-300" y="330">tags: BCV, HER, OER</text>
            ... </svg>'''))
            >>> figure = SVGFigure(SVGPlot(svg))
            >>> figure.tags
            ['BCV', 'HER', 'OER']

        """
        tags = self.svgplot.svg.get_texts("(?:tags): (?P<value>.*)")

        if len(tags) > 1:
            logger.warning(
                f"More than one text field with tags. Ignoring all text fields except for the first: {tags[0]}."
            )

        if not tags:
            return self._metadata.get("experimental", {}).get("tags", [])

        return [i.strip() for i in tags[0].value.split(",")]

    @property
    def simultaneous_measurements(self):
        r"""
        A list of names of additional measurements which are plotted
        along with the digitized data in the same figure or subplot.

        The names are read from a ``<text>`` in the SVG file such as
        ``<text>simultaneous measurements: SXRD, SHG</text>``.
        Besides `simultaneous measurements`, also `linked measurement`
        or simply `linked` are acceptable in the text field.

        EXAMPLES::

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
            >>> from svgdigitizer.svgfigure import SVGFigure
            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 200 L 0 100" />
            ...     <text x="0" y="200">x1: 0 V</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">x2: 1 V</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">j1: A / cm2</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">j2: 1 A / cm2</text>
            ...   </g>
            ...   <text x="-200" y="330">scan rate: 50 V/s</text>
            ...   <text x="-400" y="430">linked: SXRD, SHG</text>
            ... </svg>'''))
            >>> figure = SVGFigure(SVGPlot(svg))
            >>> figure.simultaneous_measurements
            ['SXRD', 'SHG']

        """
        linked = self.svgplot.svg.get_texts(
            "(?:simultaneous measurement|linked|linked measurement): (?P<value>.*)"
        )

        if len(linked) > 1:
            logger.warning(
                f"More than one text field with linked measurements. Ignoring all text fields except for the first: {linked[0]}."
            )

        # if not linked:
        if len(linked) == 0:
            return self._metadata.get("figure description", {}).get(
                "simultaneous measurements", []
            )

        return [i.strip() for i in linked[0].value.split(",")]

    @property
    def metadata(self):
        r"""
        A dict with properties of the original figure derived from
        textlabels in the SVG file, as well as properties of the dataframe
        created with :meth:`df`.

        EXAMPLES::

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
            >>> from svgdigitizer.svgfigure import SVGFigure
            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 100 L 100 0" />
            ...     <text x="0" y="0">curve: 0</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 0 200 L 0 100" />
            ...     <text x="0" y="200">E1: 0 mV</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">E2: 1 mV</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">j1: 0 uA / cm2</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">j2: 1 uA / cm2</text>
            ...   </g>
            ...   <text x="-200" y="330">scan rate: 50 V/s</text>
            ...   <text x="-400" y="430">comment: noisy data</text>
            ...   <text x="-400" y="530">linked: SXRD, SHG</text>
            ...   <text x="-200" y="630">Figure: 2b</text>
            ...   <text x="-200" y="730">tags: BCV, HER, OER</text>
            ... </svg>'''))
            >>> figure = SVGFigure(SVGPlot(svg))
            >>> figure.metadata == \
            ... {'experimental': {'tags': ['BCV', 'HER', 'OER']},
            ...  'source': {'figure': '2b', 'curve': '0'},
            ...  'figure description': {'type': 'digitized',
            ...  'measurement type': 'custom',
            ...  'fields': [{'name': 'E', 'type': 'number', 'orientation': 'horizontal', 'unit': 'mV'},
            ...             {'name': 'j', 'type': 'number', 'orientation': 'vertical', 'unit': 'uA / cm2'}],
            ...  'comment': 'noisy data',
            ...  'scan rate': {'value': 50.0, 'unit': 'V / s'},
            ...  'simultaneous measurements': ['SXRD', 'SHG']},
            ...  'data description': {'type': 'digitized', 'measurement type': 'custom', 'fields':
            ...                       [{'name': 'E', 'type': 'number', 'unit': 'mV'},
            ...                       {'name': 'j', 'type': 'number', 'unit': 'uA / cm2'},
            ...                       {'name': 't', 'type': 'number', 'unit': 's'}]}}
            True

        TESTS::

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
            >>> from svgdigitizer.svgfigure import SVGFigure
            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 100 L 100 0" />
            ...     <text x="0" y="0">curve: 0</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 0 200 L 0 100" />
            ...     <text x="0" y="200">E1: 0 mV</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">E2: 1 mV</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">j1: 0 uA / cm2</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">j2: 1 uA / cm2</text>
            ...   </g>
            ...   <text x="-400" y="430">comment: noisy data</text>
            ...   <text x="-400" y="530">linked: SXRD, SHG</text>
            ...   <text x="-200" y="630">Figure: 2b</text>
            ...   <text x="-200" y="730">tags: BCV, HER, OER</text>
            ... </svg>'''))
            >>> figure = SVGFigure(SVGPlot(svg))
            >>> figure.metadata == \
            ... {'experimental': {'tags': ['BCV', 'HER', 'OER']},
            ...  'source': {'figure': '2b', 'curve': '0'},
            ...  'figure description': {'type': 'digitized',
            ...  'measurement type': 'custom',
            ...  'fields': [{'name': 'E', 'type': 'number', 'orientation': 'horizontal', 'unit': 'mV'},
            ...             {'name': 'j', 'type': 'number', 'orientation': 'vertical', 'unit': 'uA / cm2'}],
            ...  'comment': 'noisy data',
            ...  'simultaneous measurements': ['SXRD', 'SHG']},
            ...  'data description': {'type': 'digitized', 'measurement type': 'custom', 'fields':
            ...                       [{'name': 'E', 'type': 'number', 'unit': 'mV'},
            ...                       {'name': 'j', 'type': 'number', 'unit': 'uA / cm2'}]}}
            True

        """
        metadata = {
            "experimental": {
                "tags": self.tags,
            },
            "source": {
                "figure": self.figure_label,
                "curve": self.curve_label,
            },
            "figure description": {
                "type": "digitized",
                "simultaneous measurements": self.simultaneous_measurements,
                "measurement type": self.measurement_type,
                "fields": self.figure_schema.to_dict()["fields"],
                "comment": self.comment,
            },
            "data description": {
                "type": "digitized",
                "measurement type": self.measurement_type,
                "fields": self.data_schema.to_dict()["fields"],
            },
        }

        if self.scan_rate is not None:
            metadata["figure description"].setdefault(
                "scan rate",
                {
                    "value": float(self.scan_rate.value),
                    "unit": str(self.scan_rate.unit),
                },
            )

        from mergedeep import merge

        return merge({}, self._metadata, metadata)

    def plot(self):
        r"""Visualize the data in the figure.

        EXAMPLES::

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
            >>> from svgdigitizer.svgfigure import SVGFigure
            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 100 L 100 0" />
            ...     <text x="0" y="0">curve: 0</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 0 200 L 0 100" />
            ...     <text x="0" y="200">E1: 0 V</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">E2: 1 V</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">j1: 0 A / cm2</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">j2: 1 A / cm2</text>
            ...   </g>
            ...   <text x="-200" y="330">scan rate: 50 mV / s</text>
            ... </svg>'''))
            >>> figure = SVGFigure(SVGPlot(svg))
            >>> figure.plot()

        """

        self.df.plot(
            x=self.svgplot.xlabel,
            y=self.svgplot.ylabel,
        )

        plt.xlabel(self.svgplot.xlabel + " [" + self.xunit + "]")
        plt.ylabel(self.svgplot.ylabel + " [" + self.yunit + "]")


# Ensure that cached properties are tested, see
# https://stackoverflow.com/questions/69178071/cached-property-doctest-is-not-detected/72500890#72500890
__test__ = {
    "SVGFigure.measurement_type": SVGFigure.measurement_type,
    "SVGFigure.figure_label": SVGFigure.figure_label,
    "SVGFigure.curve_label": SVGFigure.curve_label,
    "SVGFigure.xunit": SVGFigure.xunit,
    "SVGFigure.yunit": SVGFigure.yunit,
    "SVGFigure.comment": SVGFigure.comment,
    "SVGFigure.df": SVGFigure.df,
    "SVGFigure.scan_rate_labels": SVGFigure.scan_rate_labels,
    "SVGFigure.scan_rate": SVGFigure.scan_rate,
    "SVGFigure.data_schema": SVGFigure.data_schema,
    "SVGFigure.figure_schema": SVGFigure.figure_schema,
}

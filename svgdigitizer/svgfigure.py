r"""
Reconstructed scientific plot with special units and/or time axis.

A :class:`FigurePlot` wraps a plot in SVG format consisting of a curve, axis
labels and (optionally) additional metadata provided as text fields in the SVG.

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

from svgdigitizer.exceptions import SVGAnnotationError

logger = logging.getLogger("svgfigure")


class SVGFigure:
    """
    TODO:: Add description and docstring (see issue #177)
    """

    def __init__(self, svgplot, metadata=None, si_units=False):
        self.svgplot = svgplot
        self._metadata = metadata or {}
        self.si_units = si_units

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
        """
        TODO:: Add description and docstring (see issue #177)
        """
        return "custom"

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
        from other curves in the same plot.

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
            'V'

        """
        if self.si_units:
            return self.xunits['unit si']['unit']

        return self.xunits['unit original']
        #return self.data_schema.get_field(self.svgplot.xlabel).custom["unit"]

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

        """
        if self.si_units:
            return self.yunits['unit si']['unit']

        return self.yunits['unit original']
        #return self.data_schema.get_field(self.svgplot.ylabel).custom["unit"]


    @property
    def xunits(self):
        r"""Returns different formats of the x-axis unit.

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
            ...     <text x="0" y="200">E1: 0 mV / cm</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">E2: 1 mV / cm</text>
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
            >>> figure.xunits  # doctest: +NORMALIZE_WHITESPACE
            {'unit original': 'mV / cm',
            'unit si': {'unit': 'V / m', 'scale': 0.1}}

        """
        return Units(self.figure_schema.get_field(self.svgplot.xlabel).custom["unit"]).units

    @property
    def yunits(self):
        r"""Returns different formats of the y-axis unit.

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
            ...     <text x="0" y="200">E1: 0 mV / cm</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">E2: 1 mV / cm</text>
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
            >>> figure.yunits  # doctest: +NORMALIZE_WHITESPACE
            {'unit original': 'A / cm2',
            'unit si': {'unit': 'A / m2', 'scale': 10000.0}}

        """
        return Units(self.figure_schema.get_field(self.svgplot.ylabel).custom["unit"]).units

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

        TODO:: If a scan rate is given, add a time axis `t` (see issue #177)
        TODO:: If units are supposed to be in SI, modify the df (see issue #177)

        EXAMPLES:

        A simple x vs. y plot::

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
            ...   <text x="-200" y="330">scan rate: 50 mV / s</text>
            ... </svg>'''))
            >>> figure1 = SVGFigure(SVGPlot(svg))
            >>> figure1.df
                  t    E    j
            0   0.0  0.0  0.0
            1  20.0  1.0  1.0

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
            >>> figure1 = SVGFigure(SVGPlot(svg), si_units=True)
            >>> figure1.df
                  t      E     j
            0  0.00  0.000  0.00
            1  0.02  0.001  0.01

        TESTS::

        A dataframe with a time axis, reconstructed with a given scan rate
        and in SI units, where one axis does not have compatible astropy units::

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
            >>> figure1 = SVGFigure(SVGPlot(svg), si_units=True)
            >>> figure1.df
                  t      E    j
            0  0.00  0.000  0.0
            1  0.02  0.001  1.0

        """
        df = self.svgplot.df.copy()

        if self.si_units:
            for column in df.columns:
                column_unit = self.figure_schema.get_field(column).custom["unit"]
                if self.unit_is_astropy(column_unit):
                    self._convert_axis_to_si(df, column)

        if self.scan_rate:
            self._add_time_axis(df)
            return df[["t", self.svgplot.xlabel, self.svgplot.ylabel]]

        return df[[self.svgplot.xlabel, self.svgplot.ylabel]]

    def _convert_axis_to_si(self, df, label):
        r"""
        Add a voltage column to the dataframe `df`.

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
        quantity = 1 * u.Unit(
            self.figure_schema.get_field(label).custom["unit"]
        )
        # Convert the axis unit to SI unit V and use the value
        # to convert the potential values in the df to V
        df[label] = df[label] * quantity.si.value

    def _add_time_axis(self, df):
        r"""
        Add a time column to the dataframe `df`, based on the :meth:`rate`.

        EXAMPLES::

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
            >>> from svgdigitizer.electrochemistry.cv import CV
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
            ...   <text x="-200" y="330">scan rate: 50 mV/s</text>
            ... </svg>'''))
            >>> cv = CV(SVGPlot(svg))
            >>> df = cv.svgplot.df.copy()
            >>> cv._add_voltage_axis(df)
            >>> cv._add_time_axis(df)

        """

        df["delta_x"] = abs(df[self.svgplot.xlabel].diff().fillna(0))
        df["cumdelta_x"] = df["delta_x"].cumsum()
        df["t"] = df["cumdelta_x"] / float(self.scan_rate.si.value)

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
            >>> figure.scan_rate
            <Quantity 50. mV / s>

        TESTS::

        A plot without a scan rate:

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

    @property
    def data_schema(self):
        # TODO: use intersphinx to link Schema and Fields to frictionless docu (see #151).
        r"""
        A frictionless `Schema` object, including a `Field` object
        describing the data generated with :meth:`df`.
        Unless the units of the axis in the columns of the :meth:`df` remain unchanged
        and no axis was added, such as a time axis reconstructed from a scan rate,
        ``data_schema`` is almost identical to ``figure_schema``. In the individual fields
        the key `orientation` was removed.

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
            >>> figure_rate_si = SVGFigure(SVGPlot(svg), si_units=True)
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

        if self.si_units:
            for name in self.figure_schema.field_names:
                field_unit = self.figure_schema.get_field(name).custom["unit"]
                if self.unit_is_astropy(field_unit):
                    si_unit = (1* u.Unit(field_unit)).si.unit.to_string()
                    schema.update_field(name, {"unit": si_unit})

        if self.scan_rate:
            schema.add_field(fields.NumberField(name="t"))
            schema.update_field("t", {"unit": "s"})

        return schema

    @cached_property
    def figure_schema(self):
        # TODO: use intersphinx to link Schema and Fields to frictionless docu (see #151).
        r"""
        A frictionless `Schema` object, including a `Fields` object
        describing the voltage and current axis of the original plot
        including original units. The reference electrode of the
        potential/voltage axis is also given (if available).

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
            {'fields': [{'name': 'E', 'type': 'number', 'unit': 'V', 'orientation': 'x'},
                        {'name': 'j', 'type': 'number', 'unit': 'uA / cm2', 'orientation': 'y'}]}

        """
        from frictionless import Schema

        return Schema.from_descriptor(self.svgplot.figure_schema.to_dict())

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
            return None
            # return self._metadata.get("figure description", {}).get(
            #     "simultaneous measurements", []
            # )

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
            ...  'figure description': {'version': 1,
            ...  'type': 'digitized',
            ...  'measurement type': 'custom',
            ...  'fields': [{'name': 'E', 'type': 'number', 'orientation': 'x', 'unit': 'mV'},
            ...             {'name': 'j', 'type': 'number', 'orientation': 'y', 'unit': 'uA / cm2'}],
            ...  'comment': 'noisy data',
            ...  'scan rate': {'value': 50.0, 'unit': 'V / s'},
            ...  'simultaneous measurements': ['SXRD', 'SHG']},
            ...  'data description': {'version': 1, 'type': 'digitized', 'measurement type': 'custom', 'fields':
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
            ...  'figure description': {'version': 1,
            ...  'type': 'digitized',
            ...  'measurement type': 'custom',
            ...  'fields': [{'name': 'E', 'type': 'number', 'orientation': 'x', 'unit': 'mV'},
            ...             {'name': 'j', 'type': 'number', 'orientation': 'y', 'unit': 'uA / cm2'}],
            ...  'comment': 'noisy data',
            ...  'simultaneous measurements': ['SXRD', 'SHG']},
            ...  'data description': {'version': 1, 'type': 'digitized', 'measurement type': 'custom', 'fields':
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
                "version": 1,
                "type": "digitized",
                "measurement type": self.measurement_type,
                "fields": self.figure_schema.to_dict()["fields"],
                "comment": self.comment,
            },
            "data description": {
                "version": 1,
                "type": "digitized",
                "measurement type": self.measurement_type,
                "fields": self.data_schema.to_dict()["fields"],
            },
        }

        if self.scan_rate:
            metadata["figure description"].setdefault(
                "scan rate",
                {
                    "value": float(self.scan_rate.value),
                    "unit": str(self.scan_rate.unit),
                },
            )

        if self.simultaneous_measurements:
            metadata["figure description"].setdefault(
                "simultaneous measurements", self.simultaneous_measurements
            )

        from mergedeep import merge

        return merge({}, self._metadata, metadata)

    def plot(self):
        r"""Visualize the data in the figure.

        TODO:: Refactor once scan rate and SI is implemented (see issue #177)
        """
        return self.svgplot.plot()


class Units:
    r"""
    EXAMPLES::

        >>> from svgdigitizer.svgfigure import Units
        >>> units = Units('mV / cm')
        >>> units.unit
        Unit("mV / cm")
        >>> units.unit_si
        Unit("0.1 V / m")

        SI is rather ambiguous since in the above example "V" is maintained in the unit.
        If one simply parses ``V``, the results might be ``Unit("W / A")`` or ``Unit("A Ohm")``.

    """
    def __init__(self, unit):
        self._unit = unit

    @cached_property
    def unit(self):
        r"""
        Return the original unit as an astropy unit.

        EXAMPLES::

            >>> from svgdigitizer.svgfigure import Units
            >>> units = Units('mV / cm')
            >>> units.unit
            Unit("mV / cm")

        """
        return u.Unit(self._unit)

    @cached_property
    def unit_si(self):
        r"""
        Returns the original unit as SI unit.

        EXAMPLES::

            >>> from svgdigitizer.svgfigure import Units
            >>> units = Units('km / h')
            >>> units.unit_si
            Unit("0.277778 m / s")

        """
        return self.unit.si

    @property
    def non_prefix_unit(self):
        r"""
        Returns a rescaled astropy unit after removing the unit prefixes.

        EXAMPLES::

            # >>> from svgdigitizer.svgfigure import Units
            # >>> import astropy.units as u
            # >>> Units.remove_unit_prefix(u.Unit('mV / cm'))
            # Unit("0.1 V / m")

        """

        return self.remove_unit_prefix(self.unit)

    @property
    def units(self):
        r"""
        EXAMPLES::

            >>> from svgdigitizer.svgfigure import Units
            >>> units = Units('mV / cm')
            >>> units.units ==\
            ... {'unit original': 'mV / cm',
            ... 'unit si': {'unit': 'V / m', 'scale': 0.1}}
            True

            >>> units = Units('V / (cm h)')
            >>> units.units  == \
            ... {'unit original': 'V / (cm h)',
            ... 'unit si': {'unit': 'm T / s2', 'scale': 0.027777777777777776}}
            True

        """
        # TODO: Support composite axis units such as "1000 1/K"
        units = {'unit original': self.unit.to_string(),
        'unit si': {'unit': self.compositeunit_unit(self.unit_si).to_string(),
                    'scale': self.unit_si.scale},
        # 'unit without prefix': {'unit': self.compositeunit_unit(self.non_prefix_unit).to_string(),
        #                     'scale': self.non_prefix_unit.scale},
        }

        return units

    @classmethod
    def remove_unit_prefix(cls, unit):
        r"""
        Returns a rescaled astropy unit after removing the unit prefixes.

        EXAMPLES::

            # >>> from svgdigitizer.svgfigure import Units
            # >>> import astropy.units as u
            # >>> Units.remove_unit_prefix(u.Unit('mV / cm'))
            Unit("0.1 V / m")

        """
        import astropy
        import math

        # unit_parts = []
        # for unit_, power in zip(unit.bases, unit.powers):
        #     if isinstance(unit_, astropy.units.core.PrefixUnit):
        #         unit_parts.append(unit_.represents**power)
        #     else:
        #         unit_parts.append(unit_**power)

        # new_unit = u.Unit('')
        # for unit in unit_parts:
        #     new_unit *= unit

        # return new_unit
        unit_parts = []
        for unit_, power in zip(unit.bases, unit.powers):
            #print(isinstance(unit_, astropy.units.core.Unit))
            print(unit_)
            print(type(unit_))
            if isinstance(unit_, astropy.units.core.PrefixUnit):
                #print('tested')
                unit_parts.append(unit_.represents**power)
            else:
                unit_parts.append(unit_**power)

            # print(unit_, '   ', type(unit_), '    ', power)
            # print(unit_.represents**power)

        print(unit_parts)
        return math.prod(unit_parts).unit




        #return math.prod(unit_parts).unit

    @classmethod
    def compositeunit_unit(cls, unit):
        r"""
        Returns the unit of an astropy composite unit.

        In astropy a composite unit can consist of a scale and a unit, such as '0.01 m / s'.

        EXAMPLES::

            >>> from svgdigitizer.svgfigure import Units
            >>> import astropy.units as u
            >>> composite_unit = u.Unit('0.01 km / h')
            >>> composite_unit
            Unit("0.01 km / h")
            >>> Units.compositeunit_unit(composite_unit)
            Unit("km / h")
            >>> Units.compositeunit_unit(u.Unit('0.01 km / h').si)
            Unit("m / s")

        """
        import math
        return math.prod([((unit_**power)) for unit_, power in zip(unit.bases, unit.powers)]).unit


# Ensure that cached properties are tested, see
# https://stackoverflow.com/questions/69178071/cached-property-doctest-is-not-detected/72500890#72500890
__test__ = {
    "SVGFigure.figure_label": SVGFigure.figure_label,
    "SVGFigure.curve_label": SVGFigure.curve_label,
    "SVGFigure.comment": SVGFigure.comment,
    "SVGFigure.df": SVGFigure.df,
    "SVGFigure.figure_schema": SVGFigure.figure_schema,
    "SVGFigure.scan_rate_labels": SVGFigure.scan_rate_labels,
    "SVGFigure.scan_rate": SVGFigure.scan_rate,
    "SVGFigure.xunit": SVGFigure.xunit,
    "SVGFigure.yunit": SVGFigure.yunit,
}

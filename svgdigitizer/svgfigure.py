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

logger = logging.getLogger("figureplot")


class SVGFigure:
    """
    TODO:: Add description and docstring (see issue #177)
    """

    def __init__(self, svgplot, metadata=None):
        self.svgplot = svgplot
        self._metadata = metadata or {}

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
            ...   <text x="-200" y="330">scan rate: 50 mV/s</text>
            ... </svg>'''))
            >>> figure = SVGFigure(SVGPlot(svg))
            >>> figure.df
                 E    j
            0  0.0  0.0
            1  1.0  1.0

        """
        return self.svgplot.df.copy()

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
            ...   <text x="-200" y="330">scan rate: 50 V / s</text>
            ... </svg>'''))
            >>> figure = SVGFigure(SVGPlot(svg))
            >>> figure.scan_rate
            <Quantity 50. V / s>

        """
        rates = self.svgplot.svg.get_texts(
            "(?:scan rate): (?P<value>-?[0-9.]+) *(?P<unit>.*)"
        )

        if len(rates) > 1:
            raise SVGAnnotationError(
                "Multiple text fields with a scan rate were provided in the SVG. Remove all but one."
            )

        if not rates:
            rate = self._metadata.get("figure description", {}).get("scan rate", {})

            if "value" not in rate or "unit" not in rate:
                raise SVGAnnotationError("No text with scan rate found in the SVG.")

            return float(rate["value"]) * u.Unit(str(rate["unit"]))

        return float(rates[0].value) * u.Unit(rates[0].unit)

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
            ...   <text x="-200" y="330">scan rate: 50 V/s</text>
            ... </svg>'''))
            >>> figure = SVGFigure(SVGPlot(svg))
            >>> figure.data_schema  # doctest: +NORMALIZE_WHITESPACE
            {'fields': [{'name': 'E', 'type': 'number', 'unit': 'V vs. RHE'},
                        {'name': 'j', 'type': 'number', 'unit': 'uA / cm2'}]}

        """
        from frictionless import Schema

        schema = Schema.from_descriptor(self.figure_schema.to_dict())
        for name in schema.field_names:
            if "orientation" in schema.get_field(name).to_dict():
                del schema.get_field(name).custom["orientation"]

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
            ...   <text x="-200" y="330">scan rate: 50 V/s</text>
            ... </svg>'''))
            >>> figure = SVGFigure(SVGPlot(svg))
            >>> figure.figure_schema  # doctest: +NORMALIZE_WHITESPACE
            {'fields': [{'name': 'E', 'type': 'number', 'unit': 'V vs. RHE', 'orientation': 'x'},
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

        if not linked:
            return self._metadata.get("figure description", {}).get(
                "simultaneous measurements", []
            )

        return [i.strip() for i in linked[0].value.split(",")]

    # @property
    # def metadata(self):
    #     r"""
    #     A dict with properties of the original figure derived from
    #     textlabels in the SVG file, as well as properties of the dataframe
    #     created with :meth:`df`.

    #     EXAMPLES::

    #         >>> from svgdigitizer.svg import SVG
    #         >>> from svgdigitizer.svgplot import SVGPlot
    #         >>> from svgdigitizer.svgfigure import SVGFigure
    #         >>> from io import StringIO
    #         >>> svg = SVG(StringIO(r'''
    #         ... <svg>
    #         ...   <g>
    #         ...     <path d="M 0 100 L 100 0" />
    #         ...     <text x="0" y="0">curve: 0</text>
    #         ...   </g>
    #         ...   <g>
    #         ...     <path d="M 0 200 L 0 100" />
    #         ...     <text x="0" y="200">E1: 0 mV vs. RHE</text>
    #         ...   </g>
    #         ...   <g>
    #         ...     <path d="M 100 200 L 100 100" />
    #         ...     <text x="100" y="200">E2: 1 mV vs. RHE</text>
    #         ...   </g>
    #         ...   <g>
    #         ...     <path d="M -100 100 L 0 100" />
    #         ...     <text x="-100" y="100">j1: 0 uA / cm2</text>
    #         ...   </g>
    #         ...   <g>
    #         ...     <path d="M -100 0 L 0 0" />
    #         ...     <text x="-100" y="0">j2: 1 uA / cm2</text>
    #         ...   </g>
    #         ...   <text x="-200" y="330">scan rate: 50 V/s</text>
    #         ...   <text x="-400" y="430">comment: noisy data</text>
    #         ...   <text x="-400" y="530">linked: SXRD, SHG</text>
    #         ...   <text x="-200" y="630">Figure: 2b</text>
    #         ...   <text x="-200" y="730">tags: BCV, HER, OER</text>
    #         ... </svg>'''))
    #         >>> figure = SVGFigure(SVGPlot(svg))
    #         >>> figure.metadata
    #         {}

    #     """
    #     from mergedeep import merge

    #     return merge({}, self._metadata)

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
            ...     <text x="0" y="200">E1: 0 mV vs. RHE</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">E2: 1 mV vs. RHE</text>
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
            ...  'simultaneous measurements': ['SXRD', 'SHG'],
            ...  'measurement type': 'custom',
            ...  'scan rate': {'value': 50.0, 'unit': 'V / s'},
            ...  'fields': [{'name': 'E', 'type': 'number', 'orientation': 'x', 'unit': 'mV vs. RHE'},
            ...             {'name': 'j', 'type': 'number', 'orientation': 'y', 'unit': 'uA / cm2'}],
            ...  'comment': 'noisy data'},
            ...  'data description': {'version': 1, 'type': 'digitized', 'measurement type': 'custom', 'fields':
            ...                       [{'name': 'E', 'type': 'number', 'unit': 'mV vs. RHE'},
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
                "simultaneous measurements": self.simultaneous_measurements,
                "measurement type": self.measurement_type,
                "scan rate": {
                    "value": float(self.scan_rate.value),
                    "unit": str(self.scan_rate.unit),
                },
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

        from mergedeep import merge

        return merge({}, self._metadata, metadata)

    def plot(self):
        r"""Visualize the data in the figure.

        TODO:: Refactor once scan rate and SI is implemented (see issue #177)
        """
        return self.svgplot.plot()


# Ensure that cached properties are tested, see
# https://stackoverflow.com/questions/69178071/cached-property-doctest-is-not-detected/72500890#72500890
__test__ = {
    "SVGFigure.figure_label": SVGFigure.figure_label,
    "SVGFigure.curve_label": SVGFigure.curve_label,
    "SVGFigure.comment": SVGFigure.comment,
    "SVGFigure.df": SVGFigure.df,
    "SVGFigure.figure_schema": SVGFigure.figure_schema,
}

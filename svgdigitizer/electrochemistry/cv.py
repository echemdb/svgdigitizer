r"""
This module contains specific functions to digitize cyclic voltammograms.
Cyclic voltammograms represent current-voltage curves, where the voltage applied
at an electrochemical working electrode is modulated by a triangular wave potential
(applied vs. a known reference potential). An example is shown in the top part of
the following Figure.

.. image:: ../../doc/files/images/sample_data_2.png
  :width: 400
  :alt: Alternative text

These curves were recorded with a constant scan rate given in units of ``V / s``.
This quantity is usually provided in the scientific publication.
With this information the time axis can be reconstructed.

The CV can be digitized by importing the plot in an SVG editor, such as Inkscape,
where the curve is traced, the axes are labeled and the scan rate is provided.
This SVG file can then be analyzed by this class to produce the coordinates
corresponding to the original measured values.

A more detailed description on preparing the SVG files is provided in the :class:`CV`
or ...

TODO:: Link to workflow.md (see issue #73)

For the documentation below, the path of a CV is presented simply as a line.

"""
# ********************************************************************
#  This file is part of svgdigitizer.
#
#        Copyright (C) 2021-2023 Albert Engstfeld
#        Copyright (C) 2021      Johannes Hermann
#        Copyright (C) 2021-2023 Julian Rüth
#        Copyright (C) 2021      Nicolas Hörmann
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

import matplotlib.pyplot as plt
from astropy import units as u

from svgdigitizer.svgfigure import SVGFigure

logger = logging.getLogger("cv")


class CV(SVGFigure):
    r"""
    A digitized cyclic voltammogram (CV) derived from an SVG file,
    which provides access to the objects of the CV.

    Typically, the SVG input has been created by tracing a CV from
    a publication with a `<path>` in an SVG editor such as Inkscape. Such a
    path can then be analyzed by this class to produce the coordinates
    corresponding to the original measured values.

    TODO:: Link to workflow.md (see issue #73)

    EXAMPLES:

    An instance of this class can be created from a specially prepared SVG file.
    It requires:

    * | that the x-axis is labeled with U or E (V) and the y-axis
      | is labeled by I (A) or j (A / cm2)
    * | that the label of the second point (furthest from the origin)
      | on the x- or y-axis contains a value and a unit
      | such as ``<text>j2: 1 mA / cm2</text>`` or ``<text>E2: 1 mV</text>``.
      | Optionally, the text of the E/U scale also indicates the
      | reference scale, e.g., ``<text>E2: 1 mV vs. RHE</text>`` for RHE scale.
    * | that a scan rate is provided in a text field such as
      | ``<text">scan rate: 50 mV / s</text>``, placed anywhere in the SVG file.

    In addition the following text fields are accessible with this class

    * | A comment describing the data, i.e.,
      | ``<text>comment: noisy data</text>``
    * | Other measurements linked to this measurement or performed simultaneously, i.e.,
      | ``<text>linked: SXRD, DEMS</text>``
    * | A list of tags describing the content of a plot, i.e.,
      | ``<text>tags: BCV, HER, OER</text>``
    * | The figure label provided in the original plot, i.e.,
      | ``<text>figure: 1b</text>``

    A sample file looks as follows::

        >>> from svgdigitizer.svg import SVG
        >>> from svgdigitizer.svgplot import SVGPlot
        >>> from svgdigitizer.electrochemistry.cv import CV
        >>> from io import StringIO
        >>> svg = SVG(StringIO(r'''
        ... <svg>
        ...   <g>
        ...     <path d="M 0 100 L 100 0" />
        ...     <text x="0" y="0">curve: solid</text>
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
        ...   <text x="-300" y="330">comment: noisy data</text>
        ...   <text x="-400" y="330">figure: 2b</text>
        ...   <text x="-400" y="530">linked: SXRD, SHG</text>
        ...   <text x="-400" y="330">tags: BCV, HER, OER</text>
        ... </svg>'''))
        >>> cv = CV(SVGPlot(svg), si_units=True)

    The data of the CV can be returned as a dataframe
    with axis 't', 'E' or 'U', and 'I' (current) or 'j' (current density).
    The dimensions are in SI units 's', 'V' and 'A' or 'A / m2'.::

        >>> cv.df
                 t      E     j
        0  0.00000  0.000  0.00
        1  0.00002  0.001  0.01

    The data of this dataframe can also be visualized in a plot,
    where the axis labels and the data are provided in SI units
    (not in the dimensions of the original cyclic voltammogram).::

        >>> cv.plot()

    The properties of the original plot and the dataframe can be returned as a dict::

        >>> cv.metadata  == \
        ... {'experimental': {'tags': ['BCV', 'HER', 'OER']},
        ...  'source': {'figure': '2b', 'curve': 'solid'},
        ...  'figure description': {'version': 1,
        ...                         'type': 'digitized',
        ...                         'simultaneous measurements': ['SXRD', 'SHG'],
        ...                         'measurement type': 'CV',
        ...                         'scan rate': {'value': 50.0, 'unit': 'V / s'},
        ...                         'fields': [{'name': 'E','unit': 'mV', 'orientation': 'x', 'reference': 'RHE', 'type': 'number'},
        ...                                    {'name': 'j', 'unit': 'uA / cm2', 'orientation': 'y', 'type': 'number'}],
        ...                         'comment': 'noisy data'},
        ...  'data description': {'version': 1,
        ...                       'type': 'digitized',
        ...                       'measurement type': 'CV',
        ...                       'fields': [{'name': 'E', 'type': 'number', 'unit': 'V', 'reference': 'RHE'},
        ...                                  {'name': 'j', 'type': 'number', 'unit': 'A / m2'},
        ...                                  {'name': 't', 'type': 'number', 'unit': 's'}]}}
        True

    """

    def __init__(self, svgplot, metadata=None, si_units=False):
        super().__init__(svgplot=svgplot, metadata=metadata, si_units=si_units)
        assert self.svgplot.xlabel in [
            "U",
            "E",
        ], f"The y-label must be 'E' or 'U and not '{self.svgplot.xlabel}'."
        assert self.svgplot.ylabel in [
            "I",
            "j",
        ], f"The y-label must be 'I' or 'j and not '{self.svgplot.ylabel}'."

    @cached_property
    def measurement_type(self):
        return "CV"

    # @property
    # def voltage_dimension(self):
    #     r"""
    #     The dimension of the voltage axis given as ``U`` (voltage) or ``E`` (potential).

    #     EXAMPLES::

    #         >>> from svgdigitizer.svg import SVG
    #         >>> from svgdigitizer.svgplot import SVGPlot
    #         >>> from svgdigitizer.electrochemistry.cv import CV
    #         >>> from io import StringIO
    #         >>> svg = SVG(StringIO(r'''
    #         ... <svg>
    #         ...   <g>
    #         ...     <path d="M 0 100 L 100 0" />
    #         ...     <text x="0" y="0">curve: 0</text>
    #         ...   </g>
    #         ...   <g>
    #         ...     <path d="M 0 200 L 0 100" />
    #         ...     <text x="0" y="200">E1: 0 V vs. RHE</text>
    #         ...   </g>
    #         ...   <g>
    #         ...     <path d="M 100 200 L 100 100" />
    #         ...     <text x="100" y="200">E2: 1 V vs. RHE</text>
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
    #         ... </svg>'''))
    #         >>> cv = CV(SVGPlot(svg))
    #         >>> cv.voltage_dimension
    #         'E'

    #     The following example is not valid, since the voltage is on the y-axis
    #     and current on the x-axis.

    #         >>> from svgdigitizer.svg import SVG
    #         >>> from svgdigitizer.svgplot import SVGPlot
    #         >>> from svgdigitizer.electrochemistry.cv import CV
    #         >>> from io import StringIO
    #         >>> svg = SVG(StringIO(r'''
    #         ... <svg>
    #         ...   <g>
    #         ...     <path d="M 0 100 L 100 0" />
    #         ...     <text x="0" y="0">curve: 0</text>
    #         ...   </g>
    #         ...   <g>
    #         ...     <path d="M 0 200 L 0 100" />
    #         ...     <text x="0" y="200">j1: 0 uA / cm2</text>
    #         ...   </g>
    #         ...   <g>
    #         ...     <path d="M 100 200 L 100 100" />
    #         ...     <text x="100" y="200">j2: 1 uA / cm2</text>
    #         ...   </g>
    #         ...   <g>
    #         ...     <path d="M -100 100 L 0 100" />
    #         ...     <text x="-100" y="100">E1: 0 V vs. RHE</text>
    #         ...   </g>
    #         ...   <g>
    #         ...     <path d="M -100 0 L 0 0" />
    #         ...     <text x="-100" y="0">E2: 1 V vs. RHE</text>
    #         ...   </g>
    #         ...   <text x="-200" y="330">scan rate: 50 V/s</text>
    #         ... </svg>'''))
    #         >>> cv = CV(SVGPlot(svg))
    #         >>> cv.voltage_dimension
    #         UNEXPECTED EXCEPTION: AssertionError("The y-label must be 'E' or 'U and not 'j'.")
    #         Traceback (most recent call last):
    #         File "C:\Miniconda3\envs\svgdigitizer-build\lib\doctest.py", line 1350, in __run
    #             exec(compile(example.source, filename, "single",
    #         File "<doctest svgdigitizer.electrochemistry.cv.CV.voltage_dimension[12]>", line 1, in <module>
    #         File "X:\github\svgdigitizer\svgdigitizer\electrochemistry\cv.py", line 176, in __init__
    #             assert self.svgplot.xlabel in [
    #         AssertionError: The y-label must be 'E' or 'U and not 'j'.

    #     """
    #     dimensions = list(set(["E", "U"]).intersection(self.figure_schema.field_names))

    #     if len(dimensions) == 1:
    #         if self.figure_schema.get_field(dimensions[0]).custom["orientation"] == "x":
    #             return dimensions[0]
    #         raise SVGAnnotationError("The voltage must be on the x-axis in the SVG.")

    #     raise SVGAnnotationError(
    #         "No voltage axis or more than one voltage axis found in the SVG."
    #     )

    # @property
    # def current_dimension(self):
    #     r"""
    #     The dimension of the current axis given as
    #     ``I`` (current) or ``j`` (current density).

    #     EXAMPLES::

    #         >>> from svgdigitizer.svg import SVG
    #         >>> from svgdigitizer.svgplot import SVGPlot
    #         >>> from svgdigitizer.electrochemistry.cv import CV
    #         >>> from io import StringIO
    #         >>> svg = SVG(StringIO(r'''
    #         ... <svg>
    #         ...   <g>
    #         ...     <path d="M 0 100 L 100 0" />
    #         ...     <text x="0" y="0">curve: 0</text>
    #         ...   </g>
    #         ...   <g>
    #         ...     <path d="M 0 200 L 0 100" />
    #         ...     <text x="0" y="200">E1: 0 V vs. RHE</text>
    #         ...   </g>
    #         ...   <g>
    #         ...     <path d="M 100 200 L 100 100" />
    #         ...     <text x="100" y="200">E2: 1 V vs. RHE</text>
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
    #         ... </svg>'''))
    #         >>> cv = CV(SVGPlot(svg))
    #         >>> cv.current_dimension
    #         'j'

    #     """
    #     dimensions = list(set(["I", "j"]).intersection(self.figure_schema.field_names))

    #     if len(dimensions) == 1:
    #         if self.figure_schema.get_field(dimensions[0]).custom["orientation"] == "y":
    #             return dimensions[0]
    #         raise SVGAnnotationError("The current must be on the y-axis in the SVG.")

    #     raise SVGAnnotationError(
    #         "No current axis or more than one current axis found in the SVG."
    # )

    @property
    def data_schema(self):
        # TODO: use intersphinx to link Schema and Fields to frictionless docu (see #151).
        r"""
        A frictionless `Schema` object, including a `Field` object
        describing the data generated with :meth:`df`.
        Compared to :meth:`figure_schema` all fields are given in SI units.
        A time axis is also included.

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
            >>> cv = CV(SVGPlot(svg), si_units=True)
            >>> cv.data_schema  # doctest: +NORMALIZE_WHITESPACE
            {'fields': [{'name': 'E', 'type': 'number', 'unit': 'V', 'reference': 'RHE'},
                        {'name': 'j', 'type': 'number', 'unit': 'A / m2'},
                        {'name': 't', 'type': 'number', 'unit': 's'}]}

        An SVG with a current axis with dimension I and
        a voltage axis with dimension U.::

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
            ...     <text x="0" y="200">U1: 0 V</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">U2: 1 V</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">I1: 0 uA</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">I2: 1 uA</text>
            ...   </g>
            ...   <text x="-200" y="330">scan rate: 50 V/s</text>
            ... </svg>'''))
            >>> cv = CV(SVGPlot(svg), si_units=True)
            >>> cv.data_schema  # doctest: +NORMALIZE_WHITESPACE
            {'fields': [{'name': 'U', 'type': 'number', 'unit': 'V', 'reference': 'unknown'},
                        {'name': 'I', 'type': 'number', 'unit': 'A'},
                        {'name': 't', 'type': 'number', 'unit': 's'}]}

        """
        # from frictionless import Schema, fields

        # schema = Schema.from_descriptor(self.figure_schema.to_dict())

        # schema.get_field(self.voltage_dimension).custom["unit"] = "V"
        # del schema.get_field(self.voltage_dimension).custom["orientation"]
        # if self.current_dimension == "I":
        #     schema.get_field(self.current_dimension).custom["unit"] = "A"
        # elif self.current_dimension == "j":
        #     schema.get_field(self.current_dimension).custom["unit"] = "A / m2"
        # else:
        #     raise SVGAnnotationError(
        #         "None of the axis labels in the SVG have a dimension current 'I' or current density 'j'."
        #     )

        # del schema.get_field(self.current_dimension).custom["orientation"]

        # schema.add_field(fields.NumberField(name="t"))
        # schema.update_field("t", {"unit": "s"})
        schema = super().data_schema

        # astropy SI conversion turns `V` into `W / A` or `Ohm m`,
        # thus we need to set it manually to `V`.
        if self.si_units:
            if u.allclose(
                1 * u.Unit(schema.get_field(self.svgplot.xlabel).custom["unit"]),
                1 * u.V,
            ):
                schema.update_field(self.svgplot.xlabel, {"unit": "V"})
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
            >>> cv = CV(SVGPlot(svg))
            >>> cv.figure_schema  # doctest: +NORMALIZE_WHITESPACE
            {'fields': [{'name': 'E', 'type': 'number', 'unit': 'V', 'orientation': 'x', 'reference': 'RHE'},
                        {'name': 'j', 'type': 'number', 'unit': 'uA / cm2', 'orientation': 'y'}]}

        """
        import re

        from frictionless import Schema

        schema = Schema.from_descriptor(super().figure_schema.to_dict())

        pattern = r"^(?P<unit>.+?)? *(?:(?:@|vs\.?) *(?P<reference>.+))?$"
        match = re.match(
            pattern,
            schema.get_field(self.svgplot.xlabel).custom["unit"],
            re.IGNORECASE,
        )

        schema.update_field(
            self.svgplot.xlabel,
            {"unit": match[1], "reference": match[2] or "unknown"},
        )

        return schema

    # @cached_property
    # def df(self):
    #     # TODO: Add a more meaningful curve that reflects the shape of a cyclic voltammogram and which is displayed in the documentation (see issue #73).
    #     r"""
    #     Return a dataframe with axis 't', 'E' (or 'U'), and 'I' (or 'j).
    #     The dimensions are in SI units 's', 'V' and 'A' (or 'A / m2').

    #     The dataframe is constructed based on the units and values,
    #     determined from ``svgplot``. These are usually not in SI units
    #     and will be converted in the process of creating the df.

    #     The time axis can only be created when a scan rate is given
    #     in the plot, i.e., '50 mV /s'.

    #     EXAMPLES::

    #         >>> from svgdigitizer.svg import SVG
    #         >>> from svgdigitizer.svgplot import SVGPlot
    #         >>> from svgdigitizer.electrochemistry.cv import CV
    #         >>> from io import StringIO
    #         >>> svg = SVG(StringIO(r'''
    #         ... <svg>
    #         ...   <g>
    #         ...     <path d="M 0 100 L 100 0" />
    #         ...     <text x="0" y="0">curve: 0</text>
    #         ...   </g>
    #         ...   <g>
    #         ...     <path d="M 0 200 L 0 100" />
    #         ...     <text x="0" y="200">E1: 0 V vs. RHE</text>
    #         ...   </g>
    #         ...   <g>
    #         ...     <path d="M 100 200 L 100 100" />
    #         ...     <text x="100" y="200">E2: 1 V vs. RHE</text>
    #         ...   </g>
    #         ...   <g>
    #         ...     <path d="M -100 100 L 0 100" />
    #         ...     <text x="-100" y="100">j1: 0 uA / cm2</text>
    #         ...   </g>
    #         ...   <g>
    #         ...     <path d="M -100 0 L 0 0" />
    #         ...     <text x="-100" y="0">j2: 1 uA / cm2</text>
    #         ...   </g>
    #         ...   <text x="-200" y="330">scan rate: 50 mV/s</text>
    #         ... </svg>'''))
    #         >>> cv = CV(SVGPlot(svg))
    #         >>> cv.df
    #               t    E     j
    #         0   0.0  0.0  0.00
    #         1  20.0  1.0  0.01

    #     The same cv but now sampled at 0.1 V increments on the voltage axis (x-axis)::

    #         >>> cv = CV(SVGPlot(svg, sampling_interval=.1))
    #         >>> cv.df
    #                t    E      j
    #         0    0.0  0.0  0.000
    #         1    2.0  0.1  0.001
    #         2    4.0  0.2  0.002
    #         3    6.0  0.3  0.003
    #         4    8.0  0.4  0.004
    #         5   10.0  0.5  0.005
    #         6   12.0  0.6  0.006
    #         7   14.0  0.7  0.007
    #         8   16.0  0.8  0.008
    #         9   18.0  0.9  0.009
    #         10  20.0  1.0  0.010

    #     """
    #     df = self.svgplot.df.copy()
    #     self._add_voltage_axis(df)

    #     self._add_current_axis(df)

    #     self._add_time_axis(df)

    #     # Rearrange columns.
    #     return df[["t", self.voltage_dimension, self.current_dimension]]

    # def _add_voltage_axis(self, df):
    #     r"""
    #     Add a voltage column to the dataframe `df`.

    #     EXAMPLES::

    #         >>> from svgdigitizer.svg import SVG
    #         >>> from svgdigitizer.svgplot import SVGPlot
    #         >>> from svgdigitizer.electrochemistry.cv import CV
    #         >>> from io import StringIO
    #         >>> svg = SVG(StringIO(r'''
    #         ... <svg>
    #         ...   <g>
    #         ...     <path d="M 0 100 L 100 0" />
    #         ...     <text x="0" y="0">curve: 0</text>
    #         ...   </g>
    #         ...   <g>
    #         ...     <path d="M 0 200 L 0 100" />
    #         ...     <text x="0" y="200">E1: 0 V vs. RHE</text>
    #         ...   </g>
    #         ...   <g>
    #         ...     <path d="M 100 200 L 100 100" />
    #         ...     <text x="100" y="200">E2: 1 V vs. RHE</text>
    #         ...   </g>
    #         ...   <g>
    #         ...     <path d="M -100 100 L 0 100" />
    #         ...     <text x="-100" y="100">j1: 0 uA / cm2</text>
    #         ...   </g>
    #         ...   <g>
    #         ...     <path d="M -100 0 L 0 0" />
    #         ...     <text x="-100" y="0">j2: 1 uA / cm2</text>
    #         ...   </g>
    #         ...   <text x="-200" y="330">scan rate: 50 mV / s</text>
    #         ... </svg>'''))
    #         >>> cv = CV(SVGPlot(svg))
    #         >>> cv._add_voltage_axis(df = cv.svgplot.df.copy())

    #     """
    #     voltage = 1 * u.Unit(
    #         self.figure_schema.get_field(self.voltage_dimension).custom["unit"]
    #     )
    #     # Convert the axis unit to SI unit V and use the value
    #     # to convert the potential values in the df to V
    #     df[self.voltage_dimension] = df[self.voltage_dimension] * voltage.si

    # def _add_current_axis(self, df):
    #     r"""
    #     Add a current 'I' or current density 'j' column to the dataframe `df`.

    #     EXAMPLES::

    #         >>> from svgdigitizer.svg import SVG
    #         >>> from svgdigitizer.svgplot import SVGPlot
    #         >>> from svgdigitizer.electrochemistry.cv import CV
    #         >>> from io import StringIO
    #         >>> svg = SVG(StringIO(r'''
    #         ... <svg>
    #         ...   <g>
    #         ...     <path d="M 0 100 L 100 0" />
    #         ...     <text x="0" y="0">curve: 0</text>
    #         ...   </g>
    #         ...   <g>
    #         ...     <path d="M 0 200 L 0 100" />
    #         ...     <text x="0" y="200">E1: 0 V vs. RHE</text>
    #         ...   </g>
    #         ...   <g>
    #         ...     <path d="M 100 200 L 100 100" />
    #         ...     <text x="100" y="200">E2: 1 V vs. RHE</text>
    #         ...   </g>
    #         ...   <g>
    #         ...     <path d="M -100 100 L 0 100" />
    #         ...     <text x="-100" y="100">j1: 0 uA / cm2</text>
    #         ...   </g>
    #         ...   <g>
    #         ...     <path d="M -100 0 L 0 0" />
    #         ...     <text x="-100" y="0">j2: 1 uA / cm2</text>
    #         ...   </g>
    #         ...   <text x="-200" y="330">scan rate: 50 mV / s</text>
    #         ... </svg>'''))
    #         >>> cv = CV(SVGPlot(svg))
    #         >>> cv._add_current_axis(df = cv.svgplot.df.copy())

    #     """
    #     current = 1 * u.Unit(
    #         self.figure_schema.get_field(self.current_dimension).custom["unit"]
    #     )

    #     # Distinguish whether the y data is current ('A') or current density ('A / cm2')
    #     if "m2" in str(current.unit):
    #         conversion_factor = current.si
    #     else:
    #         conversion_factor = current.si

    #     df[self.current_dimension] = df[self.current_dimension] * conversion_factor

    def plot(self):
        r"""
        Visualize the digitized cyclic voltammogram with values in SI units.

        EXAMPLES::

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
            >>> from svgdigitizer.electrochemistry.cv import CV
            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 100 L 100 0" />
            ...     <text x="0" y="0">curve: solid</text>
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
            ... </svg>'''))
            >>> cv = CV(SVGPlot(svg))
            >>> cv.plot()

        """
        self.df.plot(
            x=self.svgplot.xlabel,
            y=self.svgplot.ylabel,
        )
        plt.axhline(linewidth=1, linestyle=":", alpha=0.5)
        plt.xlabel(
            self.svgplot.xlabel
            + " ["
            + str(self.data_schema.get_field(self.svgplot.xlabel).custom["unit"])
            + " vs. "
            + self.data_schema.get_field(self.svgplot.xlabel).custom["reference"]
            + "]"
        )
        plt.ylabel(
            self.svgplot.ylabel
            + " ["
            + str(self.data_schema.get_field(self.svgplot.ylabel).custom["unit"])
            + "]"
        )


# Ensure that cached properties are tested, see
# https://stackoverflow.com/questions/69178071/cached-property-doctest-is-not-detected/72500890#72500890
__test__ = {
    # "CV.df": CV.df,
    "CV.figure_schema": CV.figure_schema,
}

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

A more detailed description on preparing the SVG files is provieded in the :class:`CV`
or ...

TODO:: Link to workflow.md (see issue #73)

For the documentation below, the path of a CV is presented simply as line.

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
from collections import namedtuple
from functools import cache

import matplotlib.pyplot as plt
from astropy import units as u

logger = logging.getLogger("cv")


class CV:
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

    * that the label of the point x2 on the x-axis contains a value and a unit such as ``<text>x2: 1 mV</text>``.  Optionally, this text also indicates the reference scale, e.g. ``<text>x2: 1 mV vs. RHE</text>`` for RHE scale.
    * that the label of the point x2 on the y-axis contains a value and a unit such as ``<text>y2: 1 uA / cm2</text>``.
    * that a rate is provided in a text field such as ``<text">scan rate: 50 V / s</text>`` or ``<text>rate: 50 mV / s</text>`` placed anywhere in the SVG file.

    The data of the CV can be returned as a dataframe with axis 't', 'U', and 'I' (current) or 'j' (current density).
    The dimensions are in SI units 's', 'V' and 'A' or 'A / m2'::

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
        ...     <text x="0" y="200">x1: 0 mV vs. RHE</text>
        ...   </g>
        ...   <g>
        ...     <path d="M 100 200 L 100 100" />
        ...     <text x="100" y="200">x2: 1 mV vs. RHE</text>
        ...   </g>
        ...   <g>
        ...     <path d="M -100 100 L 0 100" />
        ...     <text x="-100" y="100">y1: 0 uA / cm2</text>
        ...   </g>
        ...   <g>
        ...     <path d="M -100 0 L 0 0" />
        ...     <text x="-100" y="0">y2: 1 uA / cm2</text>
        ...   </g>
        ...   <text x="-200" y="330">scan rate: 50 V/s</text>
        ... </svg>'''))
        >>> cv = CV(SVGPlot(svg))
        >>> cv.df
                 t      U     j
        0  0.00000  0.000  0.00
        1  0.00002  0.001  0.01

    The data of this dataframe can also be visualized in a plot,
    where the axis labels and the data are provided in SI units
    (not in the dimensions of the original cyclic voltammogram).::

        >>> cv.plot()

    The properties of the original plot can be returned as a dict::

        >>> cv.metadata
        {'figure description': {'type': 'digitized', 'measurement type': 'CV', 'scan rate': {'value': 50.0, 'unit': 'V / s'}, 'potential scale': {'unit': 'mV', 'reference': 'RHE'}, 'current': {'unit': 'uA / cm2'}, 'comment': ''}}

    """

    def __init__(self, svgplot, metadata=None):
        self.svgplot = svgplot
        self._metadata = metadata or {}

    @property
    @cache
    def axis_properties(self):
        r"""
        Return the dimension and the SI units of the x- and y-axis.

        * The x-axis dimension 'U' is given in 'V'.
        * The y-axis dimension can either be 'I' (current) or 'j' (current density), given in 'A' or 'A / m²', respectively.
        * The latter dimension and unit are derived from the ``<text>`` associated with the y-axis labels in the SVG file such as ``<text x="-100" y="0">y2: 1 A</text>``.
        * Labels in `x1` and `y1` position are ignored.

        EXAMPLES:

        In this first example a current I is plotted on the y-axis in `mA`.::

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
            >>> from svgdigitizer.electrochemistry.cv import CV
            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 200 L 0 100" />
            ...     <text x="0" y="200">x1: 0 V vs. RHE</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">x2: 1 V vs. RHE</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">y1: 0 mA</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">y2: 1 mA</text>
            ...   </g>
            ...   <text x="-200" y="330">scan rate: 50 V/s</text>
            ... </svg>'''))
            >>> cv = CV(SVGPlot(svg))
            >>> cv.axis_properties
            {'x': {'dimension': 'U', 'unit': 'V'}, 'y': {'dimension': 'I', 'unit': 'A'}}

        In this second example a current density 'j' is plotted on the y-axis in `uA / cm2`::

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
            >>> from svgdigitizer.electrochemistry.cv import CV
            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 200 L 0 100" />
            ...     <text x="0" y="200">x1: 0 V vs. RHE</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">x2: 1 V vs. RHE</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">y1: 0 uA / cm2</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">y2: 1  uA / cm2</text>
            ...   </g>
            ...   <text x="-200" y="330">scan rate: 50 V/s</text>
            ... </svg>'''))
            >>> cv = CV(SVGPlot(svg))
            >>> cv.axis_properties
            {'x': {'dimension': 'U', 'unit': 'V'}, 'y': {'dimension': 'j', 'unit': 'A / m2'}}

        """
        return {
            "x": {"dimension": "U", "unit": "V"},
            "y": {
                "dimension": "j"
                if "m2" in str(CV.get_axis_unit(self.svgplot.axis_labels["y"]))
                else "I",
                "unit": "A / m2"
                if "m2" in str(CV.get_axis_unit(self.svgplot.axis_labels["y"]))
                else "A",
            },
        }

    @classmethod
    def get_axis_unit(cls, unit):
        r"""
        Return `unit` as an `astropy <https://docs.astropy.org/en/stable/units/>`_ unit.

        This method normalizes unit names, e.g., it rewrites 'uA cm-2' to 'uA / cm2' which astropy understands.

        EXAMPLES::

            >>> from svgdigitizer.electrochemistry.cv import CV
            >>> unit = 'uA cm-2'
            >>> CV.get_axis_unit(unit)
            Unit("uA / cm2")

        """
        unit_typos = {
            "uA / cm2": [
                "uA / cm2",
                "uA / cm²",
                "µA / cm²",
                "uA/cm2",
                "uA/cm²",
                "µA/cm²",
                "µA cm⁻²",
                "uA cm-2",
            ],
            "mA / cm2": [
                "mA / cm2",
                "mA / cm²",
                "mA cm⁻²",
                "mA/cm2",
                "mA/cm²",
                "mA cm-2",
            ],
            "A / cm2": ["A / cm2", "A/cm2", "A cm⁻²", "A cm-2"],
            "uA": ["uA", "µA", "microampere"],
            "mA": ["mA", "milliampere"],
            "A": ["A", "ampere", "amps", "amp"],
            "mV": ["milliV", "millivolt", "milivolt", "miliv", "mV"],
            "V": ["V", "v", "Volt", "volt"],
            "V / s": ["V s-1", "V/s", "V / s"],
            "mV / s": ["mV / s", "mV s-1", "mV/s"],
        }

        for correct_unit, typos in unit_typos.items():
            for typo in typos:
                if unit == typo:
                    return u.Unit(correct_unit)

        raise ValueError(f"Unknown Unit {unit}")

    @property
    def x_label(self):
        r"""
        Return the label on the x-axis of the SVG plot.
        Usually the label on an axis only consits of a unit.
        In the case of electrochemical data the x-label
        usually consists of a unit and a reference.
        The unit and the reference are united in a single string,
        which are separated by ``x_label`` providing access to
        the unit and the reference.

        EXAMPLES::

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
            >>> from svgdigitizer.electrochemistry.cv import CV
            >>> from io import StringIO
            >>> svg = SVG(StringIO(r'''
            ... <svg>
            ...   <g>
            ...     <path d="M 0 200 L 0 100" />
            ...     <text x="0" y="200">x1: 0 V vs. RHE</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">x2: 1 V vs. RHE</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">y1: 0 uA / cm2</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">y2: 1  uA / cm2</text>
            ...   </g>
            ...   <text x="-200" y="330">scan rate: 50 V/s</text>
            ... </svg>'''))
            >>> cv = CV(SVGPlot(svg))
            >>> cv.x_label
            Label(label='V vs. RHE', unit='V', reference='RHE')

        Label and unit can be obtained by::

            >>> cv.x_label.unit
            'V'
            >>> cv.x_label.reference
            'RHE'

        """
        pattern = r"^(?P<unit>.+?)? *(?:(?:@|vs\.?) *(?P<reference>.+))?$"
        match = re.match(pattern, self.svgplot.axis_labels["x"], re.IGNORECASE)

        return namedtuple("Label", ["label", "unit", "reference"])(
            match[0], match[1], match[2] or "unknown"
        )

    @property
    @cache
    def rate(self):
        r"""
        Return the scan rate of the plot.

        The scan rate is read from a ``<text>`` in the SVG file such as ``<text>scan rate: 50 V/s</text>``.

        EXAMPLES::

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
            >>> from svgdigitizer.electrochemistry.cv import CV
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
            ...   <text x="-200" y="330">scan rate: 50 V/s</text>
            ... </svg>'''))
            >>> cv = CV(SVGPlot(svg))
            >>> cv.rate
            <Quantity 50. V / s>

        """
        rates = self.svgplot.svg.get_texts(
            "(?:scan rate|rate): (?P<value>-?[0-9.]+) *(?P<unit>.*)"
        )

        if len(rates) == 0:
            raise ValueError("No text with scan rate found in the SVG.")

        if len(rates) > 1:
            raise ValueError(
                "Multiple text fields with a scan rate were provided in the SVG file. Remove all but one."
            )

        # Convert to astropy unit
        rates[0].unit = CV.get_axis_unit(rates[0].unit)
        rate = float(rates[0].value) * rates[0].unit

        return rate

    @property
    @cache
    def df(self):
        # TODO: Add a more meaningful curve that reflects the shape of a cyclic voltammogram and which is displayed in the documentation (see issue #73).
        r"""
        Return a dataframe with axis 't', 'U', and 'I' (or 'j).
        The dimensions are in SI units 's', 'V' and 'A' (or 'A / m2').

        The dataframe is constructed from the 'x' and 'y' axis of 'svgplot.df',
        which are usually not in SI units.

        The time axis can only be created when a (scan) rate is given in the plot, i.e., '50 mV /s'.

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
            ...     <text x="0" y="200">x1: 0 V vs. RHE</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">x2: 1 V vs. RHE</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">y1: 0 uA / cm2</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">y2: 1  uA / cm2</text>
            ...   </g>
            ...   <text x="-200" y="330">scan rate: 50 mV/s</text>
            ... </svg>'''))
            >>> cv = CV(SVGPlot(svg))
            >>> cv.df
                  t    U     j
            0   0.0  0.0  0.00
            1  20.0  1.0  0.01

        The same cv but now sampled at 0.1 V increments on the voltage axis (x-axis)::

            >>> cv = CV(SVGPlot(svg, sampling_interval=.1))
            >>> cv.df
                   t    U      j
            0    0.0  0.0  0.000
            1    2.0  0.1  0.001
            2    4.0  0.2  0.002
            3    6.0  0.3  0.003
            4    8.0  0.4  0.004
            5   10.0  0.5  0.005
            6   12.0  0.6  0.006
            7   14.0  0.7  0.007
            8   16.0  0.8  0.008
            9   18.0  0.9  0.009
            10  20.0  1.0  0.010

        """
        df = self.svgplot.df.copy()
        self._add_voltage_axis(df)

        self._add_current_axis(df)

        self._add_time_axis(df)

        # Rearrange columns.
        return df[["t", "U", self.axis_properties["y"]["dimension"]]]

    def _add_voltage_axis(self, df):
        r"""
        Add a voltage column to the dataframe `df`, based on the :meth:`get_axis_unit` of the x axis.

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
            ...     <text x="0" y="200">x1: 0 V vs. RHE</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">x2: 1 V vs. RHE</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">y1: 0 uA / cm2</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">y2: 1  uA / cm2</text>
            ...   </g>
            ...   <text x="-200" y="330">scan rate: 50 mV/s</text>
            ... </svg>'''))
            >>> cv = CV(SVGPlot(svg))
            >>> cv._add_voltage_axis(df = cv.svgplot.df.copy())

        """
        voltage = 1 * CV.get_axis_unit(self.x_label.unit)
        # Convert the axis unit to SI unit V and use the value
        # to convert the potential values in the df to V
        df["U"] = df["x"] * voltage.to(u.V).value  # pylint: disable=E1101

    def _add_current_axis(self, df):
        r"""
        Add a current 'I' or current density 'j' column to the dataframe `df`, based on the :meth:`get_axis_unit` of the y axis.

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
            ...     <text x="0" y="200">x1: 0 V vs. RHE</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">x2: 1 V vs. RHE</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">y1: 0 uA / cm2</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">y2: 1  uA / cm2</text>
            ...   </g>
            ...   <text x="-200" y="330">scan rate: 50 mV/s</text>
            ... </svg>'''))
            >>> cv = CV(SVGPlot(svg))
            >>> cv._add_current_axis(df = cv.svgplot.df.copy())

        """
        current = 1 * CV.get_axis_unit(self.svgplot.axis_labels["y"])

        # Distinguish whether the y data is current ('A') or current density ('A / cm2')
        if "m2" in str(current.unit):
            conversion_factor = current.to(u.A / u.m ** 2)
        else:
            conversion_factor = current.to(u.A)

        df[self.axis_properties["y"]["dimension"]] = df["y"] * conversion_factor

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
            ...     <text x="0" y="200">x1: 0 V vs. RHE</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">x2: 1 V vs. RHE</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">y1: 0 uA / cm2</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">y2: 1  uA / cm2</text>
            ...   </g>
            ...   <text x="-200" y="330">scan rate: 50 mV/s</text>
            ... </svg>'''))
            >>> cv = CV(SVGPlot(svg))
            >>> df = cv.svgplot.df.copy()
            >>> cv._add_voltage_axis(df)
            >>> cv._add_time_axis(df)

        """
        df["deltaU"] = abs(df["U"].diff().fillna(0))
        df["cumdeltaU"] = df["deltaU"].cumsum()
        df["t"] = df["cumdeltaU"] / float(self.rate.to(u.V / u.s).value)

    def plot(self):
        r"""
        Visualize the digitized cyclic voltamogram with values in SI units.

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
            ...     <text x="0" y="200">x1: 0</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">x2: 1 mV</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">y1: 0</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">y2: 1 uA/cm2</text>
            ...   </g>
            ...   <text x="-200" y="330">scan rate: 50 V/s</text>
            ... </svg>'''))
            >>> cv = CV(SVGPlot(svg))
            >>> cv.plot()

        """
        self.df.plot(
            x=self.axis_properties["x"]["dimension"],
            y=self.axis_properties["y"]["dimension"],
        )
        plt.axhline(linewidth=1, linestyle=":", alpha=0.5)
        plt.xlabel(
            self.axis_properties["x"]["dimension"]
            + " ["
            + str(self.axis_properties["x"]["unit"])
            + " vs. "
            + self.x_label.reference
            + "]"
        )
        plt.ylabel(
            self.axis_properties["y"]["dimension"]
            + " ["
            + str(self.axis_properties["y"]["unit"])
            + "]"
        )

    @property
    @cache
    def comment(self):
        r"""
        Return a comment describing the plot.

        The comment is read from a ``<text>`` in the SVG file such as ``<text>comment: noisy data</text>``.

        EXAMPLES:

        This example contains a comment::

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
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
            ...   <text x="-200" y="330">scan rate: 50 V/s</text>
            ...   <text x="-400" y="430">comment: noisy data</text>
            ... </svg>'''))
            >>> cv = CV(SVGPlot(svg))
            >>> cv.comment
            'noisy data'

        This example does not contain a comment::

            >>> from svgdigitizer.svg import SVG
            >>> from svgdigitizer.svgplot import SVGPlot
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
            ...   <text x="-200" y="330">scan rate: 50 V/s</text>
            ... </svg>'''))
            >>> cv = CV(SVGPlot(svg))
            >>> cv.comment
            ''

        """
        comments = self.svgplot.svg.get_texts("(?:comment): (?P<value>.*)")

        if not comments:
            return ""

        if len(comments) > 1:
            logger.warning(
                f"More than one comment. Ignoring all comments except for the first: {comments[0]}."
            )

        return comments[0].value

    @property
    def metadata(self):
        r"""
        Returns a dict with properties of the original figure derived from textlabels in the SVG file.

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
            ...     <text x="0" y="200">x1: 0 mV vs. RHE</text>
            ...   </g>
            ...   <g>
            ...     <path d="M 100 200 L 100 100" />
            ...     <text x="100" y="200">x2: 1 mV vs. RHE</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 100 L 0 100" />
            ...     <text x="-100" y="100">y1: 0 uA / cm2</text>
            ...   </g>
            ...   <g>
            ...     <path d="M -100 0 L 0 0" />
            ...     <text x="-100" y="0">y2: 1 uA / cm2</text>
            ...   </g>
            ...   <text x="-200" y="330">scan rate: 50 V/s</text>
            ...   <text x="-400" y="430">comment: noisy data</text>
            ... </svg>'''))
            >>> cv = CV(SVGPlot(svg))
            >>> cv.metadata
            {'figure description': {'type': 'digitized', 'measurement type': 'CV', 'scan rate': {'value': 50.0, 'unit': 'V / s'}, 'potential scale': {'unit': 'mV', 'reference': 'RHE'}, 'current': {'unit': 'uA / cm2'}, 'comment': 'noisy data'}}

        """
        metadata = self._metadata.copy()
        metadata.setdefault("figure description", {})
        metadata["figure description"]["type"] = "digitized"
        metadata["figure description"]["measurement type"] = "CV"
        metadata["figure description"]["scan rate"] = {
            "value": float(self.rate.value),
            "unit": str(self.rate.unit),
        }
        metadata["figure description"].setdefault("potential scale", {})
        metadata["figure description"]["potential scale"]["unit"] = str(
            CV.get_axis_unit(self.x_label.unit)
        )
        metadata["figure description"]["potential scale"][
            "reference"
        ] = self.x_label.reference
        metadata["figure description"]["current"] = {
            "unit": str(CV.get_axis_unit(self.svgplot.axis_labels["y"]))
        }
        metadata["figure description"]["comment"] = self.comment

        return metadata

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
from collections import namedtuple
from functools import cache
import re
import matplotlib.pyplot as plt
from pathlib import Path
from astropy import units as u


class CV():
    # TODO: Add documentation with a usage example. #60
    # Until documentation is added, this class will not show in the auto-generated documentation.
    def __init__(self, svgplot, metadata=None):
        self.svgplot = svgplot
        self._metadata = metadata or {}

    @property
    @cache
    def axis_properties(self):
        return {'x': {'dimension': 'U',
                      'unit': 'V'},
                'y': {'dimension': 'j' if 'm2' in str(CV.get_axis_unit(self.svgplot.axis_labels['y'])) else 'I',
                      'unit': 'A / m2' if 'm2' in str(CV.get_axis_unit(self.svgplot.axis_labels['y'])) else 'A'}}

    @classmethod
    def get_axis_unit(cls, unit):
        r"""
        Return `unit` as an astropy unit.

        This method normalizes unit names, e.g., it rewrites 'uA cm-2' to 'uA / cm2' which astropy understands.

        EXAMPLES::

        >>> from svgdigitizer.electrochemistry.cv import CV
        >>> unit = 'uA cm-2'
        >>> CV.get_axis_unit(unit)
        Unit("uA / cm2")

        """
        unit_typos = {'uA / cm2': ['uA / cm2', 'uA / cm²', 'µA / cm²', 'uA/cm2', 'uA/cm²', 'µA/cm²', 'µA cm⁻²', 'uA cm-2'],
                      'mA / cm2': ['mA / cm2', 'mA / cm²', 'mA cm⁻²', 'mA/cm2', 'mA/cm²', 'mA cm-2'],
                      'A / cm2': ['A / cm2', 'A/cm2', 'A cm⁻²', 'A cm-2'],
                      'uA': ['uA', 'µA', 'microampere'],
                      'mA': ['mA', 'milliampere'],
                      'A': ['A', 'ampere', 'amps', 'amp'],
                      'mV': ['milliV', 'millivolt', 'milivolt', 'miliv', 'mV'],
                      'V': ['V', 'v', 'Volt', 'volt'],
                      'V / s': ['V s-1', 'V/s', 'V / s'],
                      'mV / s': ['mV / s', 'mV s-1', 'mV/s']}

        for correct_unit, typos in unit_typos.items():
            for typo in typos:
                if unit == typo:
                    return u.Unit(correct_unit)

        raise ValueError(f'Unknown Unit {unit}')

    @property
    def x_label(self):
        r"""
        Return the label on the x-axis of the SVG plot.
        In contrast to the y-label, which only consists of a unit, the x-label consists of a unit and a reference.
        The unit and the reference are united in a single string, which are separated by x_label.
        """
        pattern = r'^(?P<unit>.+?)? *(?:(?:@|vs\.?) *(?P<reference>.+))?$'
        match = re.match(pattern, self.svgplot.axis_labels['x'], re.IGNORECASE)

        return namedtuple('Label', ['label', 'unit', 'reference'])(match[0], match[1], match[2] or 'unknown')

    @property
    @cache
    def rate(self):
        r"""
        Return the scan rate of the plot.

        The scan rate is read from a `<text>` in the SVG file such as `<text>scan rate: 50 V/s</text>`.

        Examples::

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
        rates = self.svgplot.svg.get_texts('(?:scan rate|rate): (?P<value>-?[0-9.]+) *(?P<unit>.*)')
        # TODO: assert that only one label contains the scan rate (see issue #58)
        # TODO: assert that a rate is available at all (see issue #58)

        # Convert to astropy unit
        rates[0].unit = CV.get_axis_unit(rates[0].unit)
        rate = float(rates[0].value) * rates[0].unit

        return rate

    @property
    @cache
    def df(self):
        r"""
        Return a dataframe with axis 't', 'U', and 'I' (or 'j).
        The dimensions are in SI units 's', 'V' and 'A' (or 'A / m2').

        The dataframe is constructed from the 'x' and 'y' axis of 'svgplot.df',
        which are usually not in SI units.

        The time axis can only be created when a (scan) rate is given in the plot, i.e., 50 mV /s.
        """
        df = self.svgplot.df.copy()
        self._add_U_axis(df)

        self._add_I_axis(df)

        self._add_time_axis(df)

        # Rearrange columns.
        return df[['t', 'U', self.axis_properties['y']['dimension']]]

    def _add_U_axis(self, df):
        r'''
        Add a voltage column to the dataframe `df`, based on the :meth:`get_axis_unit` of the x axis.
        '''
        q = 1 * CV.get_axis_unit(self.x_label.unit)
        # Convert the axis unit to SI unit V and use the value
        # to convert the potential values in the df to V
        df['U'] = df['x'] * q.to(u.V).value

    def _add_I_axis(self, df):
        r'''
        Add a current or current desnity column to the dataframe `df`, based on the :meth:`get_axis_unit` of the y axis.
        '''
        q = 1 * CV.get_axis_unit(self.svgplot.axis_labels['y'])

        # Distinguish whether the y data is current ('A') or current density ('A / cm2')
        if 'm2' in str(q.unit):
            conversion_factor = q.to(u.A / u.m**2)
        else:
            conversion_factor = q.to(u.A)

        df[self.axis_properties['y']['dimension']] = df['y'] * conversion_factor

    def _add_time_axis(self, df):
        r'''
        Add a time column to the dataframe `df`, based on the :meth:`rate`.
        '''
        df['deltaU'] = abs(df['U'].diff().fillna(0))
        df['cumdeltaU'] = df['deltaU'].cumsum()
        df['t'] = df['cumdeltaU'] / float(self.rate.to(u.V / u.s).value)

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
        self.df.plot(x=self.axis_properties['x']['dimension'], y=self.axis_properties['y']['dimension'])
        plt.axhline(linewidth=1, linestyle=':', alpha=0.5)
        plt.xlabel(self.axis_properties['x']['dimension'] + ' [' + str(self.axis_properties['x']['unit']) + ' vs. ' + self.x_label.reference + ']')
        plt.ylabel(self.axis_properties['y']['dimension'] + ' [' + str(self.axis_properties['y']['unit']) + ']')

    @property
    def metadata(self, comment=''):
        metadata = self._metadata.copy()
        metadata.setdefault('figure description', {})
        metadata['figure description']['type'] = 'digitized'
        metadata['figure description']['measurement type'] = 'CV'
        metadata['figure description']['scan rate'] = {'value': float(self.rate.value), 'unit': str(self.rate.unit)}
        metadata['figure description'].setdefault('potential scale', {})
        metadata['figure description']['potential scale']['unit'] = str(CV.get_axis_unit(self.x_label.unit))
        metadata['figure description']['potential scale']['reference'] = self.x_label.reference
        metadata['figure description']['current'] = {'unit': str(CV.get_axis_unit(self.svgplot.axis_labels['y']))}
        metadata['figure description']['comment'] = str(comment)

        return metadata

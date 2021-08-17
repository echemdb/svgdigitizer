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
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path
from astropy import units as u

# The keys in this dict are unit strings that are identical to those
# obtained by using str() on an astropy unit of a quantity, i.e.,
# >>> from astropy import units as u
# >>> q = 10 * u.A / u.cm**2
# >>> str(q.unit)
# 'A / cm2'
# These string can directly be converted to a unit
# >>> u.Unit('uA / cm2')
unit_typos = {'uA / cm2': ['uA / cm2', 'uA / cm²', 'µA / cm²', 'µA cm⁻²', 'uA cm-2', 'uA / cm2'],
              'A / cm2': ['A / cm2', 'A cm⁻²', 'A cm-2', 'A / cm2'],
              'A': ['A', 'ampere', 'amps', 'amp'],
              'mV': ['milliV', 'millivolt', 'milivolt', 'miliv', 'mV'],
              'V': ['V', 'v', 'Volt', 'volt'],
              'V / s': ['V s-1', 'V / s'],
              'mV / s': ['mV / s', 'mV s-1', 'mV/s']}


class CV():
    def __init__(self, svgplot, metadata=None):
        """
        metadata: dict
        """
        self.svgplot = svgplot
        self.metadata = metadata or {}

    @property
    @cache
    def axis_properties(self):
        return {'x': {'dimension': 'U',
                      'unit': 'V'},
                'y': {'dimension': 'j' if 'm2' in str(self.get_axis_unit('y')) else 'I',
                      'unit': 'A / m2' if 'm2' in str(self.get_axis_unit('y')) else 'A'}}

    def get_axis_unit(self, axis):
        r'''
        Replaces the units derived from the svg file into astropy units.
        '''
        unit = self.svgplot.units[axis]

        return self.get_correct_unit(unit)

    @classmethod
    def get_correct_unit(cls, unit):
        for correct_unit, typos in unit_typos.items():
            if unit in typos:
                return u.Unit(correct_unit)

        raise ValueError(f'Unknown Unit {unit} on Axis {axis}')

    @property
    @cache
    def rate(self):
        r'''
        Return a rate based on a label in the SVG file.
        '''
        rates = self.svgplot.svg.get_texts('(?:scan rate|rate): (?P<value>-?[0-9.]+) *(?P<unit>.*)')
        # To Do
        # assert that only one label contains the scan rate
        # asstert that a rate is available at all

        # Convert to astropy unit
        rates[0].unit = CV.get_correct_unit(rates[0].unit)
        # Convert to SI astropy unit: V / s
        rate = float(rates[0].value) * rates[0].unit

        return rate

    @property
    @cache
    def cv_df(self):
        # Create potential column.
        df = self.create_df_U_axis(self.svgplot.df[['x']])

        # Create current or current density column.
        df = pd.concat([df, self.create_df_I_axis(self.svgplot.df[['y']])], axis=1)

        # Create time axis.
        df['t'] = self.create_df_time_axis(df)
        # Rearrange columns.
        df = df[['t', 'U', self.axis_properties['y']['dimension']]]

        return df

    def create_df_U_axis(self, df):
        r'''
        Create voltage axis in the dataframe based on the units given in the
        figure description.
        '''
        q = 1 * self.get_axis_unit('x')
        # Convert the axis unit to SI unit V and use the value
        # to convert the potential values in the df to V
        df['U'] = df['x'] * q.to(u.V).value

        return df[['U']]

    def create_df_I_axis(self, df):
        r'''
        Create current or current density axis in the dataframe based on the
        units given in the figure description.
        '''

        df_ = df.copy()
        q = 1 * self.get_axis_unit('y')

        # Verify if the y data is current ('A') or current density ('A / cm2')
        if 'm2' in str(q.unit):
            conversion_factor = q.to(u.A / u.m**2)
        else:
            conversion_factor = q.to(u.A)

        df_[self.axis_properties['y']['dimension']] = df_['y'] * conversion_factor

        return df_[[self.axis_properties['y']['dimension']]]

    def create_df_time_axis(self, df):
        r'''
        Create a time axis in the dataframe based on the scan rate given in the
        figure description.
        '''
        df = df.copy()
        df['deltaU'] = abs(df['U'].diff().fillna(0))
        df['cumdeltaU'] = df['deltaU'].cumsum()
        df['t'] = df['cumdeltaU']/float(self.rate.to(u.V / u.s).value)

        return df[['t']]

    def plot_cv(self):
        self.cv_df.plot(x=self.axis_properties['x']['dimension'], y=self.axis_properties['y']['dimension'])
        plt.axhline(linewidth=1, linestyle=':', alpha=0.5)
        plt.xlabel(self.axis_properties['x']['dimension'] + ' / ' + str(self.axis_properties['x']['unit']))
        plt.ylabel(self.axis_properties['y']['dimension'] + ' / ' + str(self.axis_properties['y']['unit']))

    @property
    def metadata_out(self, comment=''):
        # Add description
        assert type(comment) == str, 'Comment must be a string'
        metadata = self.metadata
        if 'figure description' not in self.metadata:
            metadata['figure description'] = {}

        metadata['figure description']['type'] = 'digitized'
        metadata['figure description']['measurement type'] = 'CV'
        metadata['figure description']['scan rate'] = {'value': self.rate.value, 'unit': str(self.rate.unit)}
        if 'potential scale' not in metadata['figure description']:
            metadata['figure description']['potential scale'] = {}
        metadata['figure description']['potential scale']['unit'] = str(self.get_axis_unit('x'))
        # Implement: Get the reference from the text labels of the axis
        # metadata['figure description']['potential scale']['reference'] = get_from_ax_labels
        metadata['figure description']['current'] = {'unit': str(self.get_axis_unit('y'))}
        metadata['figure description']['comment'] = comment

        return metadata

    def create_csv(self, filename):
        csvfile = Path(filename).with_suffix('.csv')
        self.cv_df.to_csv(csvfile, index=False)

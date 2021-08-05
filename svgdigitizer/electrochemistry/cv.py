#*********************************************************************
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
#*********************************************************************
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
unit_typos = {'uA / cm2': ['uA / cm2',
                           'uA / cm²',
                           'µA / cm²',
                           'µA cm⁻²',
                           'uA cm-2',
                           'uA / cm2'],
              'A / cm2': ['A / cm2',
                          'A cm⁻²',
                          'A cm-2',
                          'A / cm2'],
              'A': ['A',
                    'ampere',
                    'amps',
                    'amp'],
              'mV': ['milliV',
                     'millivolt',
                     'milivolt',
                     'miliv',
                     'mV'],
              'V': ['V',
                    'v',
                    'Volt',
                    'volt'],
              'V / s': ['V s-1',
                        'V / s']}


class CV():
    def __init__(self, metadata, svgplot):
        """
        metadata: dict
        """
        self.svgplot = svgplot
        self.metadata = metadata

    @property
    @cache
    def axis_properties(self):
        return {'x': {'dimension': 'U',
                      'unit': 'V'},
                'y': {'dimension': 'I' if 'm2' in str(self.get_axis_unit('y')) else 'j',
                      'unit': 'A / m2' if 'm2' in str(self.get_axis_unit('y')) else 'A'}}

    def get_axis_unit(self, axis):
        r'''
        Replaces the units derived from the svg file into astropy units.
        '''
        unit = self.svgplot.units[axis]
        for correct_unit, typos in unit_typos.items():
            if unit in typos:
                return u.Unit(correct_unit)

        raise ValueError(f'Unknown Unit {unit} on Axis {axis}')

    @property
    @cache
    def rate(self):  # TODO: probably not required
        r'''
        Return rate based on the x coordinate units.

        At the moment we simply use the value.
        '''
        # To Do:
        # Check unit of the rate.
        # Convert unit string to SI astropy unit: V / s
        return self.metadata['figure description']['scan rate']['value']

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
        df['t'] = df['cumdeltaU']/self.rate
        return df[['t']]

    def plot_cv(self):
        self.cv_df.plot(x=self.axis_properties['x']['dimension'], y=self.axis_properties['y']['dimension'])
        plt.axhline(linewidth=1, linestyle=':', alpha=0.5)
        plt.xlabel(self.axis_properties['x']['dimension'] + ' / ' + str(self.axis_properties['x']['unit']))
        plt.ylabel(self.axis_properties['y']['dimension'] + ' / ' + str(self.axis_properties['y']['unit']))

    def create_csv(self, filename):
        csvfile = Path(filename).with_suffix('.csv')
        self.cv_df.to_csv(csvfile, index=False)

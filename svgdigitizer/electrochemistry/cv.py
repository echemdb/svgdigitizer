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
unit_typos = {'uA / cm2':
            ['uA / cm2',
            'uA / cm²',
            'µA / cm²',
            'µA cm⁻²',
            'uA cm-2',
            'uA / cm2'],
        'A / cm2':
            ['A / cm2',
            'A cm⁻²',
            'A cm-2',
            'A / cm2'],
        'A':
            ['A',
            'ampere',
            'amps',
            'amp'],
        'mV':
            ['milliV',
            'millivolt',
            'milivolt',
            'miliv',
            'mV'],
        'V':
            ['V',
            'v',
            'Volt',
            'volt'],
        'V / s':
            ['V s-1',
            'V / s']}

class CV():
    def __init__(self, metadata, svgplot):
        """
        metadata: dict
        """
        self.svgplot = svgplot
        self.metadata = metadata
        self.svgplot.create_df()

        # TODO: All the rest in the init is presumably not necessary

        self.description = self.metadata['figure description']

        self.get_rate()

    @property
    @cache
    def axis_properties(self):
        return {'x': {
                            'dimension': 'U',
                            'unit': 'V'
                            },
                            'y': {
                            'dimension': 'I' if 'm2' in str(self.get_axis_unit('y')) else 'j',
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

    def get_rate(self):  # TODO: probably not required
        r'''
        Return rate based on the x coordinate units.

        At the moment we simply use the value.
        '''
        self.rate = self.metadata['figure description']['scan rate']['value']
        return self.rate

    @property
    @cache
    def cv_df(self):
        # Create potential column.
        df = self.create_df_U_axis(self.svgplot.dfs[0][['x']])

        # Create current or current density column.
        df = pd.concat([df, self.create_df_I_axis(self.svgplot.dfs[0][['y']])], axis=1)

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
        conversion_factor = q.to(u.V).value
        df['U'] = df['x'] * conversion_factor

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
        df['t'] = df['cumdeltaU']/self.get_rate()
        return df[['t']]

    def plot_cv(self):
        self.cv_df.plot(x=self.axis_properties['x']['dimension'], y=self.axis_properties['y']['dimension'])
        plt.axhline(linewidth=1, linestyle=':', alpha=0.5)
        plt.xlabel(self.axis_properties['x']['dimension'] + ' / ' + str(self.axis_properties['x']['unit']))
        plt.ylabel(self.axis_properties['y']['dimension'] + ' / ' + str(self.axis_properties['y']['unit']))

    def create_csv(self, filename):
        csvfile = Path(filename).with_suffix('.csv')
        self.cv_df.to_csv(csvfile, index=False)

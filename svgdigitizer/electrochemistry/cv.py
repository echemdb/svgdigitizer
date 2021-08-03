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
units = {'uA / cm2': ['uA / cm2',
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
                'miliv,' 
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
        self.svgplot.create_df()

        # TODO: These labels should either be extracted from the svg or yaml file
        self.xlabel = 'U'

        # TODO: should be j if both current and normalized to are given in the yaml file
        self.ylabel = 'I'

        # TODO: All the rest in the init is presumably not necessary
        self.description = self.metadata['figure description']

        self.xunit = self.description['potential scale']['unit']

        self.yunit = self.description['current']['unit']

        self.axis_units = self.get_axis_units()

        self.get_rate()

        #self.modify_df()

    def get_axis_units(self):
        '''replaces the units derived from the svg file into strings that can be used with astropy'''
        
        axis_unit_strings = self.svgplot.get_axis_unit_strings()
        axis_units ={}

        for idx, i in enumerate(axis_unit_strings):
            for unit in units:
                if axis_unit_strings[i] in units[unit]:
                    axis_units[i] = u.Unit(unit)
        
        return axis_units

    def get_rate(self):  # TODO: probably not required
        r'''
        Return rate based on the x coordinate units.

        At the moment we simply use the value.
        '''
        self.rate = self.description['scan rate']['value']
        return self.rate

    def create_cv_df(self):
        # Create potential column
        self.df = self.create_df_U_axis(self.svgplot.dfs[0][['x']])

        # Create current or current density column
        self.df = pd.concat([self.df, self.create_df_I_axis(self.svgplot.dfs[0][['y']])], axis=1)

        # create time axis
        self.df['t'] = self.create_df_time_axis(self.df)

    def create_df_U_axis(self, df):
        r'''
        Create voltage axis in the dataframe based on the units given in the
        figure description.
        '''
        q = 1 * self.axis_units['x']
        conversion_factor = q.to(u.V).value
        df['U'] = df['x'] * conversion_factor

        return df[['U']]

    def create_df_I_axis(self, df):
        r'''
        Create current or current density axis in the dataframe based on the
        units given in the figure description.
        '''

        df_ = df.copy()
        q = 1 * self.axis_units['y']
        
        # Verify if the y data is current ('A') or current density ('A / cm2')
        if 'm2' in str(q.unit):
            conversion_factor = q.to(u.A / u.m**2)
            column_name = 'j'
        else:
            conversion_factor = q.to(u.A)
            column_name = 'I'
        
        df_[column_name] = df_['y'] * conversion_factor

        return df_[[column_name]]

    def create_df_time_axis(self, df):
        r'''
        Create a time axis in the dataframe based on the scan rate given in the
        figure description.
        '''
        df_ = df.copy()
        df_['deltaU'] = abs(df_['U'].diff())
        df_['cumdeltaU'] = df_['deltaU'].cumsum()
        df_['t'] = df_['cumdeltaU']/self.get_rate()
        return df_[['t']]

    def plot_cv(self):
        for ylabel in ['I', 'j']:
            if ylabel in self.df.columns:
                self.df.plot(x='U', y=ylabel)
                plt.axhline(linewidth=1, linestyle=':', alpha=0.5)
                plt.xlabel(f'U / V')
                plt.ylabel(f'{ylabel} / undefined')

    def create_csv(self, filename):
        csvfile = Path(filename).with_suffix('.csv')
        self.df.to_csv(csvfile, index=False)

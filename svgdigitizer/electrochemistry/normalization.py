r"""
This module contains helper functions.

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
from astropy import units as u


def normalize_spelling(string, string_spellings):
    for correct_spelling, spellings in string_spellings.items():
        for spelling in spellings:
            if string == spelling:
                return correct_spelling
    raise ValueError(f'Unable to normalize string {string}')

def normalize_unit(unit):
    r"""
    Return `unit` as an `astropy <https://docs.astropy.org/en/stable/units/>`_ unit.

    This method normalizes unit names, e.g., it rewrites 'uA cm-2' to 'uA / cm2' which astropy understands.

    EXAMPLES::

        >>> from svgdigitizer.electrochemistry.normalization import normalize_unit
        >>> unit = 'uA cm-2'
        >>> normalize_unit(unit)
        Unit("uA / cm2")

    """
    unit_spellings = {'uA / cm2': ['uA / cm2', 'uA / cm²', 'µA / cm²', 'uA/cm2', 'uA/cm²', 'µA/cm²', 'µA cm⁻²', 'uA cm-2'],
                    'mA / cm2': ['mA / cm2', 'mA / cm²', 'mA cm⁻²', 'mA/cm2', 'mA/cm²', 'mA cm-2'],
                    'A / cm2': ['A / cm2', 'A/cm2', 'A cm⁻²', 'A cm-2'],
                    'uA': ['uA', 'µA', 'microampere'],
                    'mA': ['mA', 'milliampere'],
                    'A': ['A', 'ampere', 'amps', 'amp'],
                    'mV': ['milliV', 'millivolt', 'milivolt', 'miliv', 'mV'],
                    'V': ['V', 'v', 'Volt', 'volt'],
                    'V / s': ['V s-1', 'V/s', 'V / s'],
                    'mV / s': ['mV / s', 'mV s-1', 'mV/s'],
                    'mol / l': ['M', 'mol l⁻¹', 'mol/l', 'mol l^-1'],
                    'mmol / l': ['mM', 'mmol l⁻¹', 'mmol/l', 'mmol l^-1'],
                    'µmol / l': ['uM', 'umol l⁻¹', 'umol/l', 'umol l^-1','µM', 'µmol l⁻¹', 'µmol/l', 'µmol l^-1'],
                    }
    return u.Unit(normalize_spelling(unit, unit_spellings))

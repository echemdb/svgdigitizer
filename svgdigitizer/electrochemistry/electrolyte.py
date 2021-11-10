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
from pHcalc.pHcalc import Acid, Neutral, System
from astropy import units as u

class Electrolyte():
    r"""
    Electrolyte
    """
    def __init__(self, electrolyte):
        self.electrolyte = electrolyte

    @property
    @cache
    def pH(self):
        r"""
        pH of the electrolyte.
        """
        try:
            return self.electrolyte['pH']
        except KeyError:           
            return self.estimate_pH()

    def estimate_pH(self):
        r"""
        Estimates the pH of aquoues electrolytes.
        """
        pKa_dict = {
            "HClO4": [-1.6], # CRC handbook of chemistry and physics 2017
            "H2SO4": [-3, 1.9], # http://www.chem.wisc.edu/areas/reich/pkatable/pKa_compilation-1-Williams.pdf
            "H3PO4": [2.16, 7.21, 12.32], # CRC handbook of chemistry and physics 2017
            "HCOOH": [3.75], # CRC handbook of chemistry and physics 2017
            "acetic acid": [4.78],
            "HCl": [-6.2], # Analytical Chemistry, 43(7), 1971, S. 969–970.
            "pyridine": [5.23], # CRC handbook of chemistry and physics 2017
            "NH3": [9.25], # CRC handbook of chemistry and physics 2017
            "H2CO3": [6.35, 10.33] # CRC handbook of chemistry and physics 2017
        }
        acid_base_dict = {
            "NaCl": [Acid(pKa=pKa_dict["HCl"],charge=0),Neutral(charge=1)],
            "HCl": [Acid(pKa=pKa_dict["HCl"],charge=0)],
            "pyridine": [Acid(pKa=pKa_dict["pyridine"],charge=1)],
            "H2SO4": [Acid(pKa=pKa_dict["H2SO4"],charge=0)],
            "H3PO4": [Acid(pKa=pKa_dict["H3SO4"],charge=0)],
            "NaOH": [Neutral(charge=1)]            
        }
        if self.electrolyte['type'] != 'aq':
            raise NotImplementedError("pH calculations are only implemented for aqueous solutions!")
        acids_bases = []
        for i in self.electrolyte['components']:
            temp = acid_base_dict[i['name']]
            for e in temp:
                
                q = i['concentration']['value'] * self.convert_concentration_unit(i['concentration']['unit'])
                e.conc = q.to("mol / l").value
            acids_bases.extend(temp)
            
        system = System(*acids_bases)
        system.pHsolve()
        
        return system.pH
   
    @classmethod
    def convert_concentration_unit(cls, unit):
        r"""
        Return `unit` as an `astropy <https://docs.astropy.org/en/stable/units/>`_ unit.
        This method normalizes unit names, e.g., it rewrites 'uA cm-2' to 'uA / cm2' which astropy understands.
        EXAMPLES::
            >>> from website.electrochemistry.cv import Electrolyte
            >>> unit = 'µmol l⁻¹'
            >>> CV.get_axis_unit(unit)
            Unit("µmol / cm2")
        """
        unit_spelling = {'mol / l': ['M', 'mol l⁻¹', 'mol/l', 'mol l^-1'],
                      'mmol / l': ['mM', 'mmol l⁻¹', 'mmol/l', 'mmol l^-1'],
                      'µmol / l': ['uM', 'umol l⁻¹', 'umol/l', 'umol l^-1','µM', 'µmol l⁻¹', 'µmol/l', 'µmol l^-1'],
                        }

        for correct_unit, typos in unit_spelling.items():
            for typo in typos:
                if unit == typo:
                    return u.Unit(correct_unit)

        raise ValueError(f'Unknown Unit {unit}')
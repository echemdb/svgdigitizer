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
from svgdigitizer.helpers import normalize_unit, normalize_chemical_name

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
            "H3PO4": [Acid(pKa=pKa_dict["H3PO4"],charge=0)],
            "NaOH": [Neutral(charge=1)]            
        }
        if self.electrolyte['type'] != 'aq':
            raise NotImplementedError("pH calculations are only implemented for aqueous solutions!")
        acids_bases = []
        for i in self.electrolyte['components']:
            if not i['type'] == 'solvent':
                temp = acid_base_dict[normalize_chemical_name(i['name'])]
                for e in temp:
                
                    q = i['concentration']['value'] * normalize_unit(i['concentration']['unit'])
                    e.conc = q.to("mol / l").value
                acids_bases.extend(temp)
            
        system = System(*acids_bases)
        system.pHsolve()
        
        return system.pH

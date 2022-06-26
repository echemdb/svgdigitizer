r"""
This module contains the :class: `Electrolyte` which represents the electrolyte
with all it's components and handles everything related to it, such as
composition, pH (aqueous only), etc. Furthermore, the dict `acid_base` contains
a database of chemicals identified by InChI with their respective pKa values.
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

import copy
import logging
import re
from functools import cache

from astropy import units as u
from pHcalc.pHcalc import Acid, Neutral, System

logger = logging.getLogger("electrolyte")

molar = u.def_unit("M", u.mol * u.dm**-3)
u.add_enabled_units([molar])

acid_base = {
    "HClO4": [Acid(pKa=[-1.6], charge=0)],  # CRC handbook of chemistry and physics 2017
    "H2SO4": [
        Acid(pKa=[-3, 1.9], charge=0)
    ],  # http://www.chem.wisc.edu/areas/reich/pkatable/pKa_compilation-1-Williams.pdf
    "H3PO4": [
        Acid(pKa=[2.16, 7.21, 12.32], charge=0)
    ],  # CRC handbook of chemistry and physics 2017
    "HCOOH": [Acid(pKa=[3.75], charge=0)],  # CRC handbook of chemistry and physics 2017
    "acetic acid": [Acid(pKa=[4.78], charge=0)],
    "HCl": [
        Acid(pKa=[-6.2], charge=0)
    ],  # Analytical Chemistry, 43(7), 1971, S. 969–970.
    "pyridine": [
        Acid(pKa=[5.23], charge=1)
    ],  # CRC handbook of chemistry and physics 2017
    "NH3": [Acid(pKa=[9.25], charge=1)],  # CRC handbook of chemistry and physics 2017
    "H2CO3": [
        Acid(pKa=[6.35, 10.33], charge=0)
    ],  # CRC handbook of chemistry and physics 2017
    "NaOH": [Neutral(charge=1)],
    "NaClO4": [Acid(pKa=[-1.6], charge=0), Neutral(charge=1)],
    "NaCl": [Acid(pKa=[-6.2], charge=0), Neutral(charge=1)],
    "Na2SO4": [Acid(pKa=[-3, 1.9], charge=0), Neutral(charge=2)],
    "Na3PO4": [Acid(pKa=[2.16, 7.21, 12.32], charge=0), Neutral(charge=3)],
    "Na2HPO4": [Acid(pKa=[2.16, 7.21, 12.32], charge=0), Neutral(charge=2)],
    "NaH2PO4": [Acid(pKa=[2.16, 7.21, 12.32], charge=0), Neutral(charge=1)],
}


class Electrolyte:
    r"""
    :class: Electrolyte models the electrolyte i.e. the solution with all it's components.
    EXAMPLES:
    >>> from svgdigitizer.electrochemistry.electrolyte import Electrolyte
    >>> electrolyte_dict = {"type": "aq", "components": [{"name": "H2SO4","type": "acid", "concentration": {"value": 0.1, "unit": "M"}}, {"name": "Na2SO4","type": "salt", "concentration": {"value": 0.1, "unit": "M"}}]}
    >>> electrolyte = Electrolyte(electrolyte_dict)
    >>> electrolyte.pH
    1.3538681030273414
    """

    def __init__(self, electrolyte):
        self.electrolyte = electrolyte

    @property
    @cache
    def pH(self):
        r"""
        pH of the electrolyte which is either taken from the electrolyte description or if not
        present estimated using the pHcalc package.
        EXAMPLES:
            >>> from svgdigitizer.electrochemistry.electrolyte import Electrolyte
            >>> electrolyte_dict = {"pH": 1.0, "type": "aq", "components": [{"name": "H2SO4","type": "acid", "concentration": {"value": 0.1, "unit": "M"}}, {"name": "Na2SO4","type": "salt", "concentration": {"value": 0.1, "unit": "M"}}]}
            >>> electrolyte = Electrolyte(electrolyte_dict)
            >>> electrolyte.pH
            1.0
            >>> electrolyte_dict = {"type": "aq", "components": [{"name": "H2SO4","type": "acid", "concentration": {"value": 0.1, "unit": "M"}}, {"name": "Na2SO4","type": "salt", "concentration": {"value": 0.1, "unit": "M"}}]}
            >>> electrolyte = Electrolyte(electrolyte_dict)
            >>> electrolyte.pH
            1.3538681030273414
        """
        if "pH" in self.electrolyte:
            return self.electrolyte["pH"]
        return self._estimate_ph()

    def _estimate_ph(self):
        r"""
        Return an estimate of the pH of this aquoues electrolytes.
        EXAMPLES:
            >>> from svgdigitizer.electrochemistry.electrolyte import Electrolyte
            >>> electrolyte_dict = {"type": "aq", "components": [{"name": "H2SO4","type": "acid", "concentration": {"value": 0.1, "unit": "M"}}, {"name": "Na2SO4","type": "salt", "concentration": {"value": 0.1, "unit": "M"}}]}
            >>> electrolyte = Electrolyte(electrolyte_dict)
            >>> electrolyte._estimate_ph()
            1.3538681030273414

            Nonexistent chemical:
            >>> from svgdigitizer.electrochemistry.electrolyte import Electrolyte
            >>> electrolyte_dict = {"type": "aq", "components": [{"name": "H3SO4","type": "acid", "concentration": {"value": 0.1, "unit": "M"}}, {"name": "Na2SO4","type": "salt", "concentration": {"value": 0.1, "unit": "M"}}]}
            >>> electrolyte = Electrolyte(electrolyte_dict)
            >>> electrolyte._estimate_ph()

            Chemical not in database:
            >>> from svgdigitizer.electrochemistry.electrolyte import Electrolyte
            >>> electrolyte_dict = {"type": "aq", "components": [{"name": "H3SO4","type": "acid", "concentration": {"value": 0.1, "unit": "M"}}, {"name": "Na2SO4","type": "salt", "concentration": {"value": 0.1, "unit": "M"}}]}
            >>> electrolyte = Electrolyte(electrolyte_dict)
            >>> electrolyte._estimate_ph()

        """
        if self.electrolyte["type"] != "aq":
            logger.warning(
                "pH calculations are only implemented for aqueous solutions."
            )
            return None

        acids_bases = []
        for component in self.electrolyte["components"]:
            if component["type"] != "solvent":
                # check if chemical is in database
                if component["name"] in acid_base:
                    molecular_components = copy.deepcopy(acid_base[component["name"]])
                    for molecular_component in molecular_components:
                        quantity = component["concentration"]["value"] * u.Unit(
                            component["concentration"]["unit"]
                        )
                        molecular_component.conc = quantity.to("mol / l").value
                    acids_bases.extend(molecular_components)
                else:
                    acids_bases.append(None)
                    logger.warning(
                        f"Component {component['name']} not found in acid base database. Consider adding it."
                    )

        # skip calculation if at least one component is not known
        if None in acids_bases:
            return None

        system = System(*acids_bases)
        system.pHsolve()
        return system.pH
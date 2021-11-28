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
import re
import xml.etree.ElementTree as ET
from functools import cache

import pubchempy as pcp
import requests
from astropy import units as u
from pHcalc.pHcalc import Acid, Neutral, System

from svgdigitizer.electrochemistry.normalization import normalize_unit

acid_base = {
    "InChI=1S/ClHO4/c2-1(3,4)5/h(H,2,3,4,5)": {
        "name": "HClO4",
        "components": [Acid(pKa=[-1.6], charge=0)],
    },  # CRC handbook of chemistry and physics 2017
    "InChI=1S/H2O4S/c1-5(2,3)4/h(H2,1,2,3,4)": {
        "name": "H2SO4",
        "components": [Acid(pKa=[-3, 1.9], charge=0)],
    },  # http://www.chem.wisc.edu/areas/reich/pkatable/pKa_compilation-1-Williams.pdf
    "InChI=1S/H3O4P/c1-5(2,3)4/h(H3,1,2,3,4)": {
        "name": "H3PO4",
        "components": [Acid(pKa=[2.16, 7.21, 12.32], charge=0)],
    },  # CRC handbook of chemistry and physics 2017
    "InChI=1S/CH2O2/c2-1-3/h1H,(H,2,3)": {
        "name": "HCOOH",
        "components": [Acid(pKa=[3.75], charge=0)],
    },  # CRC handbook of chemistry and physics 2017
    "InChI=1S/C2H4O2/c1-2(3)4/h1H3,(H,3,4)": {
        "name": "acetic acid",
        "components": [Acid(pKa=[4.78], charge=0)],
    },
    "InChI=1S/ClH/h1H": {
        "name": "HCl",
        "components": [Acid(pKa=[-6.2], charge=0)],
    },  # Analytical Chemistry, 43(7), 1971, S. 969–970.
    "InChI=1S/C5H5N/c1-2-4-6-5-3-1/h1-5H": {
        "name": "pyridine",
        "components": [Acid(pKa=[5.23], charge=1)],
    },  # CRC handbook of chemistry and physics 2017
    "InChI=1S/H3N/h1H3": {
        "name": "NH3",
        "components": [Acid(pKa=[9.25], charge=1)],
    },  # CRC handbook of chemistry and physics 2017
    "InChI=1S/CH2O3/c2-1(3)4/h(H2,2,3,4)": {
        "name": "H2CO3",
        "components": [Acid(pKa=[6.35, 10.33], charge=0)],
    },  # CRC handbook of chemistry and physics 2017
    "InChI=1S/Na.H2O/h;1H2/q+1;/p-1": {
        "name": "NaOH",
        "components": [Neutral(charge=1)],
        },
    "InChI=1S/ClH.Na/h1H;/q;+1/p-1": {
        "name": "NaCl",
        "components": [Acid(pKa=[-6.2], charge=0), Neutral(charge=1)],
    },
    "InChI=1S/2Na.H2O4S/c;;1-5(2,3)4/h;;(H2,1,2,3,4)/q2*+1;/p-2": {
        "name": "Na2SO4",
        "components": [Acid(pKa=[-3, 1.9], charge=0), Neutral(charge=2)],
    },
    "InChI=1S/3Na.H3O4P/c;;;1-5(2,3)4/h;;;(H3,1,2,3,4)/q3*+1;/p-3": {
        "name": "Na3PO4",
        "components": [Acid(pKa=[2.16, 7.21, 12.32], charge=0), Neutral(charge=3)],
    },
    "InChI=1S/2Na.H3O4P/c;;1-5(2,3)4/h;;(H3,1,2,3,4)/q2*+1;/p-2": {
        "name": "Na2HPO4",
        "components": [Acid(pKa=[2.16, 7.21, 12.32], charge=0), Neutral(charge=2)],
    },
    "InChI=1S/Na.H3O4P/c;1-5(2,3)4/h;(H3,1,2,3,4)/q+1;/p-1": {
        "name": "NaH2PO4",
        "components": [Acid(pKa=[2.16, 7.21, 12.32], charge=0), Neutral(charge=1)],
    },
}


class Electrolyte:
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
            return self.electrolyte["pH"]
        except KeyError:
            return self.estimate_pH()

    def estimate_pH(self):
        r"""
        Estimates the pH of aquoues electrolytes.

        EXAMPLES::

            CID can be retrieved with InChIKey::
            >>> from svgdigitizer.electrochemistry.electrolyte import Electrolyte
            >>> electrolyte_dict = {"type": "aq", "components": [{"name": "H2SO4","type": "acid", "concentration": {"value": 0.1, "unit": "M"}}, {"name": "Na2SO4","type": "salt", "concentration": {"value": 0.1, "unit": "M"}}]}
            >>> electrolyte = Electrolyte(electrolyte_dict)
            >>> electrolyte.pH
            1.3538681030273414
        """

        if self.electrolyte["type"] != "aq":
            raise NotImplementedError(
                "pH calculations are only implemented for aqueous solutions!"
            )
        acids_bases = []
        for i in self.electrolyte["components"]:
            if not i["type"] == "solvent":
                InChI = self.lookup_chemical_ids_from_name(i["name"])["InChI"]
                temp = self.get_pKa(InChI)
                for e in temp:
                    q = i["concentration"]["value"] * normalize_unit(
                        i["concentration"]["unit"]
                    )
                    e.conc = q.to("mol / l").value
                acids_bases.extend(temp)

        system = System(*acids_bases)
        system.pHsolve()

        return system.pH

    @classmethod
    def lookup_CID_from_InChI(cls, InChI):
        r"""
        Lookup Pubchem CID from InChI.

        EXAMPLES::

            CID can be retrieved with InChI::
            >>> Electrolyte.lookup_CID_from_InChI(InChI='InChI=1S/H3O4P/c1-5(2,3)4/h(H3,1,2,3,4)') # phosphoric acid
            1004

        """
        return pcp.get_cids(InChI, "inchi")[0]

    @classmethod
    def lookup_chemical_ids_from_name(cls, chemical_name):
        r"""
        Lookup CID, InChI, and InChIKey from chemical name.

        EXAMPLES::

            CID can be retrieved with InChIKey::
            >>> from svgdigitizer.electrochemistry.electrolyte import Electrolyte
            >>> Electrolyte.lookup_chemical_ids_from_name('phosphoric acid')
            {'CID': 1004, 'InChI': 'InChI=1S/H3O4P/c1-5(2,3)4/h(H3,1,2,3,4)', 'InChIKey': 'NBIIXXVUZAFLBC-UHFFFAOYSA-N'}

        """
        results = pcp.get_cids(chemical_name, "name")
        len_results = len(results)
        if len_results > 1:
            raise RuntimeError(
                "Ambiguous chemical name! More than one chemical id return by pubchem. Use another chemical name"
            )
        elif len_results == 0:
            raise RuntimeError(
                f"Name of chemical {chemical_name} not found in pubchem! Check spelling."
            )
        else:
            return pcp.get_properties(("InChI", "InChIKey"), results[0])[0]

    def get_pKa(self, InChI):
        r"""
        Get pKa
        Pubchem lookup only works for neutral acids!

        """
        pattern = re.compile(r".*(?P<pKa>\d+\.\d*).*")
        try:
            return acid_base[InChI]["components"]
        except KeyError:
            cid = self.lookup_CID_from_InChI(InChI=InChI)
            pKa_result = self.lookup_pKa(cid)["pKa"]
            # TODO support salts etc.
            return [
                Acid(
                    pKa=[pattern.match(i).group("pKa") for i in pKa_result.split(";")],
                    charge=0,
                )
            ]

    def lookup_pKa(self, cid):
        r"""
        get url from Pubchem to get pka lookup result
        'XML' can be replaced with 'JSON' but it is harder to parse later on
        for more info about Pubchem output types: https://pubchemdocs.ncbi.nlm.nih.gov/pug-rest$_Toc494865558
        stolen from https://github.com/khoivan88/pka_lookup/blob/master/src/pka_lookup_pubchem.py
        """
        pka_lookup_result_xml = f"https://pubchem.ncbi.nlm.nih.gov/rest/pug_view/data/compound/{cid}/XML?heading=Dissociation+Constants"
        headers = {
            "user-agent": "Mozilla/5.0 (X11; CentOS; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.75 Safari/537.36"
        }

        # Get the html request info using CID number from pubchem
        r = requests.get(pka_lookup_result_xml, headers=headers, timeout=15)
        # Check to see if give OK status (200) and not redirect
        if r.status_code == 200 and len(r.history) == 0:
            # print(r.text)
            # Use python XML to parse the return result
            tree = ET.fromstring(r.text)

            # Get the XML tree of <Information> only
            info_node = tree.find(
                ".//*{http://pubchem.ncbi.nlm.nih.gov/pug_view}Information"
            )

            # Get the pKa reference:
            original_source = info_node.find(
                "{http://pubchem.ncbi.nlm.nih.gov/pug_view}Reference"
            ).text
            # Get the pKa result:
            pka_result = info_node.find(
                ".//*{http://pubchem.ncbi.nlm.nih.gov/pug_view}String"
            ).text
            pka_result = re.sub(
                r"^pKa = ", "", pka_result
            )  # remove 'pka = ' part out of the string answer

            result = {
                "pKa": pka_result,
                "reference": original_source,
            }

            return result

        else:
            raise RuntimeError("pKa not found in Pubchem.")

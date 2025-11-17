r"""
Module for handling operations related to PDF files.
"""

import logging

# ********************************************************************
#  This file is part of svgdigitizer.
#
#        Copyright (C) 2025 Johannes Hermann
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
import os
from functools import cached_property

logger = logging.getLogger("svgdigitizer.pdf")

# taken from https://github.com/retorquere/zotero-better-bibtex/blob/2be35ea03431b703bf6d2ebbf6b07d12dd352a0f/content/Preferences/preferences.yaml#L353
default_skip_words = (
    "a",
    "ab",
    "aboard",
    "about",
    "above",
    "across",
    "after",
    "against",
    "al",
    "along",
    "amid",
    "among",
    "an",
    "and",
    "anti",
    "around",
    "as",
    "at",
    "before",
    "behind",
    "below",
    "beneath",
    "beside",
    "besides",
    "between",
    "beyond",
    "but",
    "by",
    "d",
    "da",
    "das",
    "de",
    "del",
    "dell",
    "dello",
    "dei",
    "degli",
    "della",
    "dell",
    "delle",
    "dem",
    "den",
    "der",
    "des",
    "despite",
    "die",
    "do",
    "down",
    "du",
    "during",
    "ein",
    "eine",
    "einem",
    "einen",
    "einer",
    "eines",
    "el",
    "en",
    "et",
    "except",
    "for",
    "from",
    "gli",
    "i",
    "il",
    "in",
    "inside",
    "into",
    "is",
    "l",
    "la",
    "las",
    "le",
    "les",
    "like",
    "lo",
    "los",
    "near",
    "nor",
    "of",
    "off",
    "on",
    "onto",
    "or",
    "over",
    "past",
    "per",
    "plus",
    "round",
    "save",
    "since",
    "so",
    "some",
    "sur",
    "than",
    "the",
    "through",
    "to",
    "toward",
    "towards",
    "un",
    "una",
    "unas",
    "under",
    "underneath",
    "une",
    "unlike",
    "uno",
    "unos",
    "until",
    "up",
    "upon",
    "versus",
    "via",
    "von",
    "while",
    "with",
    "within",
    "without",
    "yet",
    "zu",
    "zum",
)


class Pdf:
    "Handles all interactions with the PDF file."

    def __init__(self, pdf_filepath, doi=None):
        "Takes the path of a PDF file."
        self.filepath = pdf_filepath
        self._doi = doi

    @cached_property
    def doc(self):
        "Holds the opened PDF file."
        import pymupdf

        return pymupdf.open(self.filepath)

    def _rename(self, new_name):
        "Rename the PDF and update its file path."
        os.rename(self.filepath, new_name)
        self.filepath = new_name

    @cached_property
    def doi(self):
        """
        Extract the DOI from the provided PDF or the provided string. Since in some cases additional pages are prepended to the PDF, the DOI is extracted from either the first or second page.
        """
        import re

        pattern = r"10\.\d{4,9}\/[-._;()/:a-zA-Z0-9]+"

        if self._doi:
            match = re.match(pattern, self._doi)
            if match:
                return self._doi
            else:
                raise ValueError("The provided DOI is not a valid.")

        doc = self.doc

        for page_num in range(
            min(doc.page_count, 2)
        ):  # inspect the first (two) page(s)
            text = doc.get_page_text(page_num)
            matches = re.findall(pattern, text)
            if len(matches) == 0:
                logger.info(f"No DOI found on page {page_num + 1}. Trying next page.")
            elif len(matches) > 1:
                raise ValueError(
                    f"{len(matches)} DOIs found. Candidates are {matches}. Extraction of DOI failed."
                )
            else:
                logger.info(f"DOI found on page {page_num + 1}.")
                return matches[0]

        raise ValueError("No DOI found. Extraction of DOI failed.")

    @staticmethod
    def _download_citation(doi):
        "Download citation using DOI"
        import requests

        resp = requests.get(
            "https://doi.org/" + doi,
            headers={"Accept": "application/x-bibtex; charset=utf-8"},
            timeout=5,
        )
        if resp.ok:
            return resp.text
        return None

    @cached_property
    def bibliographic_entry(self):
        r"""
        Get the citation from the DOI provided PDF file. Returns a bibtex string.

        EXAMPLES::

            >>> from svgdigitizer.pdf import Pdf
            >>> from svgdigitizer.test.cli import TemporaryData
            >>> with TemporaryData("**/Hermann_2018_J._Electrochem._Soc._165_J3192.pdf") as directory:
            ...     # do not assign instance to variable which keeps the file open and fails for windows
            ...     Pdf(os.path.join(directory, "Hermann_2018_J._Electrochem._Soc._165_J3192.pdf")).bibliographic_entry
            '@article{Hermann_2018, title={Enhanced Electrocatalytic Oxidation ... year={2018}, pages={J3192–J3198} }'

        """
        doi = self.doi
        citation = self._download_citation(doi).strip()

        if not citation:
            raise KeyError(f"Failed to get citation from DOI {doi}.")
        return citation

    @cached_property
    def num_pages(self):
        "Number of pages of the PDF file."
        return self.doc.page_count

    def export_png(self, page_idx, dpi):
        "Returns the requested PDF page as PNG with specified DPI."
        return self.doc.load_page(page_idx).get_pixmap(dpi=dpi)

    def rename_by_key(self):
        r"""
        Rename the provided PDF file by the key derived from citation.

        """
        from pybtex.database import parse_string

        bibliography_data = parse_string(self.bibliographic_entry, bib_format="bibtex")
        identifier = self.build_identifier(bibliography_data)
        self._rename(identifier + ".pdf")

    @staticmethod
    def build_identifier(citation, skip_words=default_skip_words):
        """
        Build the entry identifier based on a bibtex citation provided as `BibliographyData` (pybtex).
        Some common title words are omitted from the identifier by default (see `skip_words`).
        To change the omitted words it is possible to provide a custom word list.

        TESTS::

            >>> from svgdigitizer.pdf import Pdf
            >>> from pybtex.database import parse_string
            >>> bibtex_string = '@article{Mart_nez_Hincapi__2021, title={Surface charge and interfacial acid-base properties: pKa,2 of carbon dioxide at Pt(110)/perchloric acid solution interfaces.}, volume={388}, ISSN={0013-4686}, url={http://dx.doi.org/10.1016/j.electacta.2021.138639}, DOI={10.1016/j.electacta.2021.138639}, journal={Electrochimica Acta}, publisher={Elsevier BV}, author={Martínez-Hincapié, R. and Rodes, A. and Climent, V. and Feliu, J.M.}, year={2021}, month=aug, pages={138639} }' #pylint: disable=line-too-long
            >>> bibliography_data = parse_string(bibtex_string, bib_format="bibtex")
            >>> Pdf.build_identifier(bibliography_data)
            'martinez-hincapie_2021_surface_138639'

            >>> bibtex_string = '@article{hermannEffectPHAnion2021, title = {The {{Effect}} of {{pH}} and {{Anion Adsorption}} on {{Formic Acid Oxidation}} on {{Au}}(111) {{Electrodes}}}, author = {Hermann, Johannes M. and Abdelrahman, Areeg and Jacob, Timo and Kibler, Ludwig A.}, year = 2021, month = jul, journal = {Electrochim. Acta}, volume = {385}, pages = {138279}, issn = {0013-4686}, doi = {10.1016/j.electacta.2021.138279} }' #pylint: disable=line-too-long
            >>> bibliography_data = parse_string(bibtex_string, bib_format="bibtex")
            >>> Pdf.build_identifier(bibliography_data)
            'hermann_2021_effect_138279'

        """
        from slugify import slugify

        entry = list(citation.entries.values())[0]
        first_author = entry.persons["author"][0].last_names[0]
        title_words = entry.fields["title"].split(" ")
        first_word = slugify(title_words[0])
        if first_word in skip_words:
            first_word = title_words[1]
        year = entry.fields["year"]
        first_page = (
            entry.fields["pages"].split("–")[0].split("-")[0]
        )  # split unicode "–" and normal hypen "-"
        slugified_strs = [
            slugify(item) for item in [first_author, year, first_word, first_page]
        ]
        identifier = "_".join(slugified_strs)
        return identifier

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
from typing import BinaryIO

logger = logging.getLogger("svgdigitizer.pdf")


class Pdf:
    "Handles all interactions with the PDF file."

    def __init__(self, pdf_file: BinaryIO):
        "Takes a file-like object."
        self._pdf = pdf_file

    @property
    def pdf(self):
        "Holds the PDF file."
        return self._pdf

    @cached_property
    def doc(self):
        "Holds the opened PDF file."
        import pymupdf

        return pymupdf.open(self._pdf)

    def _rename(self, new_name):
        os.rename(self._pdf, new_name)
        self._pdf.name = new_name

    @cached_property
    def doi(self):
        """
        Extract the DOI from the provided PDF. Since in some cases additional pages are prepended to the PDF, the DOI is extracted from either the first or second page.
        """
        import re

        doc = self.doc

        for page_num in range(
            min(doc.page_count, 2)
        ):  # inspect the first (two) page(s)
            text = doc.get_page_text(page_num)
            matches = re.findall(r"10\.\d{4,9}\/[-._;()/:a-zA-Z0-9]+", text)
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
        "Download citation for DOI"
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
        Get the citation from the DOI provided PDF file.

        EXAMPLES::

            >>> from svgdigitizer.pdf import Pdf
            >>> from svgdigitizer.test.cli import TemporaryData
            >>> with TemporaryData("**/Hermann_2018_J._Electrochem._Soc._165_J3192.pdf") as directory:
            ...     pdf = Pdf(os.path.join(directory, "Hermann_2018_J._Electrochem._Soc._165_J3192.pdf"))
            ...     pdf.bibliographic_entry
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

        bibliography = parse_string(self.bibliographic_entry, bib_format="bibtex")
        identifier = self._build_identifier(bibliography)
        self._rename(identifier + ".pdf")

    @staticmethod
    def _build_identifier(citation):
        """
        Build the entry identifier based on bibtex citation.

        TESTS::

            >>> from svgdigitizer.pdf import Pdf
            >>> from pybtex.database import parse_string
            >>> bibtex_string = ' @article{Mart_nez_Hincapi__2021, title={Surface charge and interfacial acid-base properties: pKa,2 of carbon dioxide at Pt(110)/perchloric acid solution interfaces.}, volume={388}, ISSN={0013-4686}, url={http://dx.doi.org/10.1016/j.electacta.2021.138639}, DOI={10.1016/j.electacta.2021.138639}, journal={Electrochimica Acta}, publisher={Elsevier BV}, author={Martínez-Hincapié, R. and Rodes, A. and Climent, V. and Feliu, J.M.}, year={2021}, month=aug, pages={138639} }' #pylint: disable=line-too-long
            >>> bibliography = parse_string(bibtex_string, bib_format="bibtex")
            >>> Pdf._build_identifier(bibliography)
            'martinez-hincapie_2021_surface_138639'

        """
        from slugify import slugify

        entry = list(citation.entries.values())[0]
        first_author = entry.persons["author"][0].last_names[0]
        title_words = entry.fields["title"].split(" ")
        first_word = title_words[0]
        if "the" == first_word:  # maybe add more words?
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

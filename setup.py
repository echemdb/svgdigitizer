# *********************************************************************
#  This file is part of svgdigitizer.
#
#        Copyright (C)      2021 Albert Engstfeld
#        Copyright (C)      2021 Johannes Hermann
#        Copyright (C) 2021-2022 Julian Rüth
#        Copyright (C)      2021 Nicolas Hörmann
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
# *********************************************************************
import setuptools
from distutils.core import setup

setup(
    name="svgdigitizer",
    version="0.6.0",
    packages=["svgdigitizer", "svgdigitizer.electrochemistry", "svgdigitizer.test"],
    license="GPL 3.0+",
    description="svgdigitizer is a Python library and command line tool to recover the measured data underlying plots in scientific publications.",
    long_description=open("README.md", encoding="UTF-8").read(),
    long_description_content_type="text/markdown",
    include_package_data=True,
    install_requires=[
        "astropy>=5,<6",
        "click>=8,<9",
        "frictionless>=4.28.2,<5",
        "matplotlib>=3.5,<4",
        "mergedeep>=1.3.4,<2",
        "pandas>=1.3,<2",
        "pdf2image>=1.16,<2",
        "pillow>=9,<10",
        "pyyaml>=6,<7",
        "scipy>=1.7,<2",
        "svg.path>=4.1,<5",
        "svgpathtools>=1.4,<2",
        "svgwrite>=1.4,<2",
    ],
    entry_points={
        "console_scripts": ["svgdigitizer=svgdigitizer.__main__:cli"],
    },
    python_requires=">=3.9",
)

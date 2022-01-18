#*********************************************************************
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
#*********************************************************************
import os
from distutils.core import setup

setup(
    name = 'svgdigitizer',
    version = '0.1.0',
    packages = ['svgdigitizer', 'svgdigitizer.electrochemistry', 'svgdigitizer.test'],
    license = 'GPL 3.0+',
    long_description = open('README.md').read(),
    include_package_data=True,
    install_requires = [
        'astropy>=5,<6',
        'click>=8,<9',
        'matplotlib>=3.5,<4',
        'pandas>=1.3,<2',
        'pdf2image>=1.16,<2',
        'pillow>=8.4,<9',
        'pyyaml>=6,<7',
        'scipy>=1.7,<2',
        'svg.path>=4.1,<5',
        'svgpathtools>=1.4,<2',
        'svgwrite>=1.4,<2',
    ],
    entry_points = {
        'console_scripts': [
            'svgdigitizer=svgdigitizer.__main__:cli'
        ],
    },
)

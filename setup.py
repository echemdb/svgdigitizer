import os
from distutils.core import setup

setup(
    name = 'svgdigitizer',
    version = '0.1.0',
    packages = ['svgdigitizer',],
    license = 'GPL 3.0+',
    long_description = open('README.md').read(),
    include_package_data=True,
    entry_points = {
        'console_scripts': [
            'svgdigitizer=svgdigitizer.__main__:cli'
        ],
    },
)

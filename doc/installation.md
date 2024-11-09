Installation
============

The recommended way to install the svgdigitizer is to use your package manager,
(e.g., `apt-get` on Debian or Ubuntu, `pacman` on Arch Linux, `brew` on macOS.)

You can consult [repology](https://repology.org/project/python:svgdigitizer/packages)
to see if the svgdigitizer is available for your package manager.

Alternatively, the svgdigitizer can be installed by one of the following
methods.

Install with pip from PyPI
--------------------------

The latest stable version of the svgdigitizer is available on
[PyPI](https://pypi.org/project/svgdigitizer/) for all platforms and can be
installed if you have Python and pip installed already:

```sh
pip install svgdigitizer
```

This command downloads and installs the svgdigitizer and its dependencies into
your local Python installation.

If the above command fails because you do not have permission to modify your
Python installation, you can install the svgdigitizer into your user account:

```sh
pip install --user svgdigitizer
```

You can instead also install the latest unreleased version of the svgdigitizer
from our [GitHub Repository](https://github.com/echemdb/svgdigitizer) with

```sh
pip install git+https://github.com/echemdb/svgdigitizer@master
```

Install with conda from conda-forge
-----------------------------------

The svgdigitizer is [available on
conda-forge](https://github.com/conda-forge/svgdigitizer-feedstock) for all
platforms.

If you don't have conda yet, we recommend to install
[Miniforge](https://github.com/conda-forge/miniforge#miniforge3).

Miniforge is already pre-configured for conda-forge. If you already had another
release of conda installed, make sure the conda-forge channel is
[configured correctly](https://conda-forge.org/docs/user/introduction.html#how-can-i-install-packages-from-conda-forge)

Once your conda setup is ready, create a new `svgdigitizer` environment with
the latest stable version of the svgdigitizer:

```sh
conda create -n svgdigitizer svgdigitizer
```

To use the svgdigitizer, activate the `svgdigitizer` environment:

```sh
conda activate svgdigitizer
svgdigitizer --help
```

To install the svgdigitizer into an existing environment, activate that environment and then

```sh
conda install svgdigitizer
```

In case you use mamba instead of conda, replace `conda` with mamba in the examples above.

Install with pip for development
--------------------------------

If you want to work on the svgdigitizer itself, install [pixi](https://pixi.sh)
and get a copy of the latest unreleased version of the svgdigitizer:

```sh
git clone https://github.com/echemdb/svgdigitizer.git
cd svgdigitizer
```

To launch the svgdigitizer, run

```sh
pixi run svgdigitizer
```

Any changes you make to the files in your local copy of the svgdigitizer should
now be available in your next Python session.

To build the documentation locally, run

```sh
pixi run doc
```

and to run all doctests, run

```sh
pixi run doctest
```

We would love to see your contribution to the svgdigitizer.

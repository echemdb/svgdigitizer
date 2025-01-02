# SVGDigitizer — Extract (x,y) Data Points from SVG files

![Logo](https://raw.githubusercontent.com/echemdb/svgdigitizer/master/doc/files/logo/logo.png)

The `svgdigitizer` allows recovering data from a curve in a figure, plotted in a 2D coordinate system, which is usually found in scientific publications.
The data is accessible either with a command line interface or the API from a specifically prepared scaled vector graphics (SVG) file. The data can be stored as a [frictionless datapackage](https://frictionlessdata.io/) (CSV and JSON) which can be used with [unitpackage](https://echemdb.github.io/unitpackage/) to access the plots metadata or create a database of such datapackages.

# Features

The `svgdigitizer` has additional features compared to other plot digitizers, such as:

* supports **multiple y (x) values per x (y) value**
* usage of splines allows for very **precise retracing** of distinct features
* splines can be digitized with specific **sampling intervals**
* supports plots with distorted/**skewed axis**
* **extracts units** from axis labels
* **reconstruct time series** with a given scan rate
* supports **scale bars**
* supports **scaling factors**
* **extracts metadata** associated with the plot in the SVG
* **saves data as [frictionless datapackage](https://frictionlessdata.io/)** (CSV + JSON) allowing for [FAIR](https://en.wikipedia.org/wiki/FAIR_data) data usage
* **inclusion of metadata** in the datapackage
* **Python API** to interact with the retraced data

Refer to our [documentation](https://echemdb.github.io/svgdigitizer/) for more details.

## Installation

This package is available on [PyPI](https://pypi.org/project/svgdigitizer/) and can be installed with pip:

```sh .noeval
pip install svgdigitizer
```

The package is also available on [conda-forge](https://github.com/conda-forge/svgdigitizer-feedstock) and can be installed with conda

```sh .noeval
conda install -c conda-forge svgdigitizer
```

or mamba

```sh .noeval
mamba install -c conda-forge svgdigitizer
```

Please consult our [documentation](https://echemdb.github.io/svgdigitizer/) for
more detailed [installation instructions](https://echemdb.github.io/svgdigitizer/installation.html).

## Command Line Interface

The CLI allows creating SVG files from PDFs and allows digitizing the processed SVG files. Certain plot types have specific commands to recover different kinds of metadata. Refer to the [CLI documentation](https://echemdb.github.io/svgdigitizer/cli) for more information.

```sh
$ svgdigitizer
Usage: svgdigitizer [OPTIONS] COMMAND [ARGS]...

  The svgdigitizer suite.

Options:
  --help  Show this message and exit.

Commands:
  cv        Digitize a cylic voltammogram and create a frictionless datapackage.
  digitize  Digitize a 2D plot.
  figure    Digitize a figure with units on the axis and create a frictionless datapackage.
  paginate  Render PDF pages as individual SVG files with linked PNG images.
  plot      Display a plot of the data traced in an SVG.

$ svgdigitizer figure doc/files/others/looping_scan_rate.svg --sampling-interval 0.01
```

## API

You can also use the `svgdigitizer` package directly from Python, to access properties of the SVG or additional properties associated with the figure.

```python
>>> from svgdigitizer.svg import SVG
>>> from svgdigitizer.svgplot import SVGPlot
>>> from svgdigitizer.svgfigure import SVGFigure


>>> figure = SVGFigure(SVGPlot(SVG(open('doc/files/others/looping.svg', 'rb')), sampling_interval=0.01))
```

Examples:
`figure.df` provides a dataframe of the digitized curve.
`figure.plot()` shows a plot of the digitized curve.
`figure.metadadata` provides a dict with metadata of the original plot, such as original units of the axis.

The `svgdigitizer` can be enhanced with submodules, which are designed to digitize specific plot types, such as the submodule `electrochemistry.cv`.

This submodule allows digitizing cyclic voltammograms
commonly found in the field of electrochemistry.

```python
>>> from svgdigitizer.svg import SVG
>>> from svgdigitizer.svgplot import SVGPlot
>>> from svgdigitizer.electrochemistry.cv import CV

>>> cv_svg = 'doc/files/mustermann_2021_svgdigitizer_1/mustermann_2021_svgdigitizer_1_f2a_blue.svg'
>>> cv = CV(SVGPlot(SVG(open(cv_svg, 'rb')), sampling_interval=0.01))
```

The resulting `cv` object has the same properties as the `figure` object above.

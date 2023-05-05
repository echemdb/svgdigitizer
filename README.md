# SVGDigitizer — (x,y) Data Points from SVG files

![Logo](./doc/files/logo/logo.png)

The `svgdigitizer` allows recovering data from a curve in a figure, plotted in a 2D coordinate system, which is usually found in scientific publications.
The data is accessible either with a command line interface or the `svgdigitizer` API from a specifically prepared scaled vector graphics (SVG) file. The data can be stored as a [frictionless datapackage](https://frictionlessdata.io/) (CSV and JSON) which can be used with [unitpackage](https://echemdb.github.io/echemdb/) to access the plots metadata or create a database of such datapackages.

# Advantages

The `svgdigitizer` has the following advantages compared to other plot digitizers, such as:

* usage of splines allows for very **precise retracing** distinct features
* supports **multiple y (x) values per x (y) value**
* supports **scale bars**
* supports **scaling factors**
* supports plots with distorted/**skewed axis**
* splines can be digitized with specific **sampling intervals**
* **extracts units** from axis labels
* **extracts metadata** associated with the plot in the SVG
* **reconstruct time series** with a given scan rate
* **saves data as [frictionless datapackage](https://frictionlessdata.io/)** (CSV + JSON) allowing for [FAIR](https://en.wikipedia.org/wiki/FAIR_data) data usage
* **inclusion of metadata** in the datapackage
* **Python API** to interact with the retraced data

Refer to our [documentation](https://echemdb.github.io/svgdigitizer/) for more details.

## Installation

Install the latest stable version of `svgdigitizer` from PyPI

```sh
pip install echemdb
```

or conda

```sh
conda install -c conda-forge echemdb
```

Please consult our [documentation](https://echemdb.github.io/svgdigitizer/) for
more detailed [installation instructions](https://echemdb.github.io/svgdigitizer/installation.html).

## Command Line Interface

The CLI allows creating SVG files from PDFs and allows digitizing the processed SVG files. Certain plot types have specific commands to recover different kinds of metadata. Refer to the [CLI documentation](https://echemdb.github.io/svgdigitizer/cli) for more information.

```sh
$ svgdigitizer  # byexample: +term as-is +geometry 80x240
Usage: svgdigitizer [OPTIONS] COMMAND [ARGS]...
  The svgdigitizer suite.
Options:
  --help  Show this message and exit.
Commands:
  cv        Digitize a cylic voltammogram and create a frictionless datapackage.
  digitize  Digitize a plot.
  figure    Digitize a figure with units on the axis and create a frictionless datapackage.
  paginate  Render PDF pages as individual SVG files with linked PNG images.
  plot      Display a plot of the data traced in an SVG.

$ svgdigitizer cv doc/files/mustermann_2021_svgdigitizer_1/mustermann_2021_svgdigitizer_1_f2a_blue.svg --sampling-interval 0.01
```

## API

You can also use the `svgdigitizer` package directly from Python.

The examples are based on the documentation files provided with `svgdigitizer` in the folder `doc/files/others`.

```python
>>> from svgdigitizer.svg import SVG
>>> from svgdigitizer.svgplot import SVGPlot
>>> from svgdigitizer.svgfigure import SVGFigure


>>> plot = SVGFigure(SVGPlot(SVG(open('doc/files/others/looping.svg', 'rb'))))
```

`plot.df` provides a dataframe of the digitized curve.
`plot.plot()` shows a plot of the digitized curve.


## Submodule CV

The submodule `electrochemistry.cv` is specifically designed to digitize cyclic voltammograms
commonly found in the field of electrochemistry.

```python
>>> from svgdigitizer.svgplot import SVGPlot
>>> from svgdigitizer.svg import SVG
>>> from svgdigitizer.electrochemistry.cv import CV

>>> cv = CV(SVGPlot(SVG(open('test/data/xy_rate.svg', 'rb'))))
```

`cv.df` provides a dataframe with a time, voltage and current axis (in SI units). Depending on the type of data the current is expressed as current `I` in `A` or a current density `j` in `A / m2`.

The dataframe can for example be saved as `csv` via:

```python
from pathlib import Path
cv.df.to_csv(Path(svgfile).with_suffix('.csv'), index=False)
```

`cv.plot()` shows a plot of the digitizd data with appropriate axis labels.
`cv.metadadata` provides a dict with metadata of the original plot, such as original units of the axis.


`CV` also accepts a dict with metadata, which is updated with keywords related to the original figure (`figure descripton`), i.e., original axis units.

```python
>>> import yaml
>>> from svgdigitizer.svgplot import SVGPlot
>>> from svgdigitizer.svg import SVG
>>> from svgdigitizer.electrochemistry.cv import CV

>>> with open('test/data/xy_rate.yaml') as f:
...    metadata = yaml.load(f, Loader=yaml.SafeLoader)

>>> cv = CV(SVGPlot(SVG(open('test/data/xy_rate.svg', 'rb'))), metadata=metadata)
```

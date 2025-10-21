---
jupytext:
  formats: ipynb,md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.14.5
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
---

```{raw-cell}
<!--
The original figure in this documentation were produced with Xournal++ (./files/others/example_plot.xopp). The content of the XOPP was exported as pdf (./files/others/example_plot.pdf). With the paginate function of svgdigitizer the page was exported as PNG and SVG.
* (./files/others/example_plot.png)
* (./files/others/example_plot.svg)

The latter was renamed and to ./files/others/example_plot_demo.svg and the curve was digitized. The digitized plot was exported as ./files/others/example_plot_demo.png
-->
```

Welcome to svgdigitizer's documentation!
========================================

The `svgdigitizer` allows recovering data from a curve in a figure,
plotted in a 2D coordinate system. The data can be recovered from an SVG with a Python API or a command line interface to create figures or [frictionless datapackages](https://frictionlessdata.io/) (CSV and JSON). The `svgdigitizer` supports units, scalebars, scaling factors, and more.

![files/logo/logo.png](files/logo/logo.png)

Features
============

The `svgdigitizer` has additional features compared to other plot digitizers:

* usage of splines allows for very **precise retracing** of distinct features
* supports **multiple y (x) values per x (y) value**
* supports **scale bars**
* supports **scaling factors**
* supports plots with a **skewed axis**
* splines can be digitized with specific **sampling intervals**
* **extracts units** from axis labels
* **extracts metadata** associated with the plot in the SVG
* **reconstruct time series** with a given scan rate
* **saves data as [frictionless datapackage](https://frictionlessdata.io/)** (CSV + JSON) allowing for [FAIR](https://en.wikipedia.org/wiki/FAIR_data) data usage
* **inclusion of metadata** in the datapackage
* **Python API** to interact with the retraced data

## Example Plot

Such plots are often found in scientific publications, where
in many cases, especially for old publications, the source data
is not accessible anymore.
In some cases, the axes of the plot can be skewed, e.g., in scanned
documents. An extreme case for such a plot is depicted in the following figure.

![files/images/example_plot_p0.png](files/images/example_plot_p0.png)

In order to recover the source data, first the plot is imported in a
vector graphics program, such as [Inkscape](https://inkscape.org/) to create an SVG file.
The curve is traced with a *regular bezier path* and is grouped with a text label containing a unique label.
The coordinate system is defined by groups of two points and text labels for each axis.
A scan rate can be given as text label, where the units of the rate must be equivalent to the unit on the x-axis divided by time, such as `50 mV / s`. This allows reconstructing a time axis for inclusion in the CSV file.
Additional labels describing the data
can be provided anywhere in the SVG file. For the above figure the SVG looks as follows.

![files/images/example_plot_p0_demo.png](files/images/example_plot_p0_demo.png)

+++

## [Command line interface](cli.md)

This SVG can be digitized from the [command line interface](cli.md), which creates a [frictionless datapacke](https://frictionlessdata.io/) including a
{download}`CSV <./files/others/example_plot_p0_demo.csv>` of the x and y data (here U and v) and a {download}`JSON <./files/others/example_plot_p0_demo.json>` file with metadata.
The sampling of the *bezier paths* can be set by `--sampling-interval` which specifies the sampling interval in x units.
In this specific case also indicate that the axes are `--skewed`.

```sh .noeval
svgdigitizer figure example_plot_p0_demo.svg --sampling-interval 0.01 --skewed
```

+++

## [API](api.md)

With the Python [API](api.md), the SVG can also be used to create an [SVGPlot instance](api/svgplot.md) to extract basic information.

```{code-cell} ipython3
from svgdigitizer.svg import SVG
from svgdigitizer.svgplot import SVGPlot

plot = SVGPlot(SVG(open('./files/others/example_plot_p0_demo.svg', 'rb')), sampling_interval=0.01, algorithm='mark-aligned')
```

Now axis labels or any other text label in the SVG can be queried.

```{code-cell} ipython3
plot.axis_labels
```

```{code-cell} ipython3
plot.svg.get_texts()
```

The sampled data can be extracted as a [pandas](https://pandas.pydata.org/) dataframe, where the values are given the original plots units:

```{code-cell} ipython3
plot.df.head()
```

The [SVGPlot instance](api/svgplot.md) can be used be used to create an [SVGFigure instance](api/svgfigure.md), which, for example, reconstructs the time axis based on the scan rate.

```{code-cell} ipython3
from svgdigitizer.svgfigure import SVGFigure

figure = SVGFigure(plot)
figure.scan_rate # Returns an astropy quantity
```

And the corresponding data:

```{code-cell} ipython3
figure.df.head()
```

A plot can be created via

```{code-cell} ipython3
figure.plot() # Or plot.plot() for an svgplot instance.
```

+++

Installation
============

This package is available on [PiPY](https://pypi.org/project/svgdigitizer/) and can be installed with pip:

```sh .noeval
pip install svgdigitizer
```

The package is also available on [conda-forge](https://github.com/conda-forge/svgdigitizer-feedstock) an can be installed with conda

```sh .noeval
conda install -c conda-forge svgdigitizer
```

or mamba

```sh .noeval
mamba install -c conda-forge svgdigitizer
```

See the [installation instructions](installation.md) for further details.

Further information
===================

The svgdigitizer can be enhanced with other modules for specific datasets.

Currently the following datasets are supported:

* [cyclic voltammograms](api/cv.md) (*I* vs. *E* — current vs. potential curves or *j* vs. *E* — current density vs. potential curves) commonly found in electrochemistry. For further details and requirements refer to the specific instructions of the [cv module](api/cv.md) itself or the detailed description on how to [digitize cyclic voltammograms](workflow.md) for the [echemdb](https://www.echemdb.org/).

If you have used this project in the preparation of a publication, please cite it as described [on our zenodo page](https://zenodo.org/records/5881475).

## Datapackage interaction

Datapackges created with `svgplot` (or modules inheriting from `svgplot` such as `cv`) can be loaded with the ['unitpackage' module](https://echemdb.github.io/unitpackage/) to create a database of the digitized data. In case your own data has the same datapackage structure, the digitized data can easily be compared with your own data.

```{toctree}
:maxdepth: 2
:caption: "Contents:"
:hidden:
installation.md
usage.md
cli.md
api.md
workflow.md
```

Welcome to svgdigitizer's documentation!
========================================

<!--
```{todo}
* what is svgdigitizer and what is our aim.
* then refer to installation, cli, api and cv.
```
-->

Svgdigitizer allows recovering data from a curve, plotted in a 2D coordinate 
system with defined axes.
Such plots are often found in scientific publications, where
in many cases, especially for old pulications, the underlying data 
is not accessible anymore. 
In some cases, the axis of the plot can be a bit skewed, caused from scanning 
printed documents. An extreme case for such a plot is depicted in the following figure.

![files/images/example_plot_p0.png](files/images/example_plot_p0.png) 

In order to recover the underlying data, first the plot is imported in a 
vector graphics program, such as [Inkscape](https://inkscape.org/).
The curve is traced with *regular bezier paths* and two points and text labels
are created and grouped for each axis to define the coordinate system.
The curve should be assigned a text label. Additional labels describing the data 
can be provided anywhere in the SVG file. The resulting file looks as follows.

![files/images/example_plot_p0_demo.png](files/images/example_plot_p0_demo.png) 

## [Command line interface](cli.md)
This SVG can be digitized from the [command line interface](cli.md), which creates a CSV file of the x and y data. 
The resolution can be specified by `--sampling-interval`.

```sh
svgdigitizer digitize example_plot_p0_demo.svg --sampling-interval 0.01
```

## [API](api.md)
With the [API](api.md), the file can also be used to create an actual [SVGplot class](api/svgplot.md).

```python
>>> from svgdigitizer.svg import SVG
>>> from svgdigitizer.svgplot import SVGPlot

>>> plot = SVGPlot(SVG(open('./svgdigitizer/doc/files/others/example_plot_p0_demo.svg', 'rb')), sampling_interval=0.01, algorithm='mark-aligned')
```

Now one can query things such as the axis labels or any other text label in the SVG file.
```python
>>> plot.axis_labels
{'x': 'V', 'y': 'm / s'}

>>> plot.svg.get_texts()
[<text>curve: blue</text>,
 <text>x2: 80 V</text>,
 <text>x1: 10 V</text>,
 <text>y1: 10 m / s</text>,
 <text>y2: 60 m / s</text>,
 <text>comment: random data</text>,
 <text>operator: Mr. X</text>]
```

The sampled data can be extracted as a [pandas](https://pandas.pydata.org/) dataframe:
```python
>>> plot.df
	        x	        y
0	11.660079	13.681307
1	11.670079	13.681548
2	11.680079	13.681934
3	11.690079	13.682416
4	11.700079	13.682976
...	      ...	      ...
```

A plot can be created via
```python
>>> plot.plot()
```
![files/images/example_plot_p0_demo_digitized.png](files/images/example_plot_p0_demo_digitized.png) 

Installation
============

The package is hosted on [PiPY](https://pypi.org/project/svgdigitizer/) and can be installed via

```sh
pip install svgdigitizer
```

Read the [installation instructions](installation.md) on further details if you want to contribute to the project.

Further information
===================

The svgdigitizer can be enhanced with other modules for specific datasets.

Currently the following datasets are supported:
* [cyclic voltammograms](api/cv.md) (I vs. E - current vs. potential curves or j vs. E - current density vs. potential curves) commonly found in electrochemistry. For further details and requirements refer to the specific instructions of the [cv module](api/cv.md) itself or the detailed description on how to [digitize cyclic voltamograms](workflow.md) for the [echemdb](https://echemdb.github.io/website/).

We would be delighted if you would [cite](https://zenodo.org/record/5881475) our project when you use the svgdigitizer in your project.

```{toctree}
:maxdepth: 2
:caption: "Contents:"
:hidden:
installation.md
cli.md
api.md
api/cv.md
workflow.md
```

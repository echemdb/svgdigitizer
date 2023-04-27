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

Command Line Interface
======================

The command line interface (CLI) allows creating SVG files from PDFs and allows digitizing the [processed SVG files](usage.md). Certain plot types have specific commands to recover different kinds of metadata. All options are revealed

```{note}
The preceding `!` in the following examples is used to evaluate bash commands in [jupyter notebooks](https://jupyter-tutorial.readthedocs.io/en/stable/workspace/ipython/shell.html). Remove the `!` to evaluate the command in the shell.
```

```{code-cell} ipython3
!svgdigitizer
```

## `paginate`

```{code-cell} ipython3
!svgdigitizer paginate --help
```

### Examples

There are several {download}`example PDFs <./files/others/example_plot_paginate.pdf>` available in the `svgdigitizer`documentation which can be used for testing.

```{code-cell} ipython3
!svgdigitizer paginate ./files/others/example_plot_paginate.pdf
```

Download the resulting {download}`SVG (example_plot_paginate_p0.svg)<./files/others/example_plot_paginate_p0.svg>`.

(digitize)=
## `digitize`

```{code-cell} ipython3
!svgdigitizer digitize --help
```

### Examples

Consider the following skewed plot.

```{image} /files/others/example_plot_p0.png
:class: bg-primary mb-1
:width: 500px
:align: center
```

We can create an unskewed digitized CSV data of the plot with

```{code-cell} ipython3
!svgdigitizer digitize ./files/others/example_plot_p0_demo_digitize.svg --skewed
```

The CSV can, for example, be imported as a pandas dataframe to create a plot.

```{code-cell} ipython3
:align: center
:class: bg-primary mb-1
:width: 500px

import pandas as pd

df = pd.read_csv('./files/others/example_plot_p0_demo_digitize.csv')
df.plot(x='U', y='v', ylabel='v')
```

The resulting plot indicates that only the nodes of the spline were connected. To improve the tracing use the `--sampling-interval` option.

```{code-cell} ipython3
!svgdigitizer digitize ./files/others/example_plot_p0_demo_digitize.svg --skewed --sampling-interval 0.01
```

The result looks as follows

```{code-cell} ipython3
:align: center
:class: bg-primary mb-1
:tags: [hide-input]
:width: 500px

import pandas as pd

df = pd.read_csv('./files/others/example_plot_p0_demo_digitize.csv')
df.plot(x='U', y='v', ylabel='v')
```

```{note}
The use of [`svgdigitizer digitize`](digitize) is discouraged when your axis labels contain units, since the output CSV does not contain this information. Use [`svgdigitizer figure`](figure) instead, which creates a frictionless datapackage (CSV + JSON).
```

## `plot`

```{code-cell} ipython3
!svgdigitizer plot --help
```

```{note}
The plot will only be displayed, when your shell is configure accordingly.
```

### Examples

```{code-cell} ipython3
!svgdigitizer plot ./files/others/example_plot_p0_demo_digitize.svg --skewed --sampling-interval 0.01
```

(figure)=
## `figure`

```{code-cell} ipython3
!svgdigitizer figure --help
```

Flags `--metadata` and `--bibliography` are described in the [advanced section](advanced-flags) below.

### Examples

Consider the following figure where the annotated {download}`SVG (looping_scan_rate.svg)<./files/others/looping_scan_rate.svg>` contains a scan rate.

```{image} ./files/others/looping_scan_rate_annotated.png
:width: 400px
```

Digitize the figure with

```{code-cell} ipython3
!svgdigitizer figure ./files/others/looping_scan_rate.svg --sampling-interval 0.01
```

Resulting in

```{code-cell} ipython3
:tags: [hide-input]

import pandas as pd

df = pd.read_csv('./files/others/looping_scan_rate.csv')
df.plot(x='d', y='height', xlabel='distance [m]', ylabel='height [m]', legend=False)
```

## `cv`

The `cv` option is designed specifically to digitze cyclic voltammograms (CVs). Overall it has the same functionality as the [`figure`](figure) option. The differences are as follows.

* Certain keys in the output metadata are directly related to cyclic voltammetry measurements.
* The units on the x-axis must be equivalent to volt `U` in `V` and those on the y-axis equivalent to current `I` in `A` or current density `j` in `A / m2`.
* The voltage unit can be referred to a reference, such as `V vs. RHE`. In that case the dimension should be `E` instead of `U`.
* The `--sampling-interval` is in units of mV.

These standardized cv data are, for example, used in the [echemdb](https://www.echemdb.org) database.

```{code-cell} ipython3
!svgdigitizer cv --help
```

### Examples

An annotated example {download}`SVG<./files/mustermann_2021_svgdigitizer_1/mustermann_2021_svgdigitizer_1_f2a_blue.svg>` is shown in the following figure.

```{image} ./files/mustermann_2021_svgdigitizer_1/mustermann_2021_svgdigitizer_1_f2a_blue.png
:width: 400px
```

```{code-cell} ipython3
!svgdigitizer cv ./files/mustermann_2021_svgdigitizer_1/mustermann_2021_svgdigitizer_1_f2a_blue.svg --sampling-interval 0.01
```

(advanced-flags)=
## Advanced flags

### `--metadata`

The flag `--metadata` allows adding metadata to the resource of the datapackage from a yaml file. An example of such a yaml file for electrochemical data can be found [here](https://github.com/echemdb/metadata-schema/blob/main/examples/file_schemas/svgdigitizer.yaml).

<!--
Return a bibtex string built from a BIB file and a key provided in `metadata['source']['citation key']`,
    when both requirements are met. Otherwise an empty string is returned.
    -->

```{code-cell} ipython3
!svgdigitizer figure --metadata --help
```

```{todo}
Add example
```

### `--bibliography`

```{code-cell} ipython3
!svgdigitizer figure --bibliography --help
```

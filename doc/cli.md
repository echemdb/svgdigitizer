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

The command line interface (CLI) allows creating SVG files from PDFs, which in turn allows digitizing the [processed SVG files](usage.md). Certain plot types have specific commands to recover different kinds of plots with different metadata. All commands and options are revealed with

```{note}
The preceding `!` in the following examples is used to evaluate bash commands in [jupyter notebooks](https://jupyter-tutorial.readthedocs.io/en/latest/notebook/example.html). Remove the `!` to evaluate the command in the shell.
```

```{code-cell} ipython3
!svgdigitizer
```

```{note}
[Example files](https://github.com/echemdb/svgdigitizer/tree/master/doc/files/others) for the use with the `svgdigitizer` can be found in the repository.
```

## `paginate`

Create SVG and PNG files from a PDF with

```{code-cell} ipython3
!svgdigitizer paginate --help
```

{download}`Example PDFs <./files/others/example_plot_paginate.pdf>` for testing purposes are available in the `svgdigitizer` repository.

### Examples

Create an SVG with a linked PNG for each page in a PDF.

```{code-cell} ipython3
!svgdigitizer paginate ./files/others/example_plot_paginate.pdf
```

Download the resulting {download}`SVG (example_plot_paginate_p0.svg)<./files/others/example_plot_paginate_p0.svg>`.


## `create-svg`

Create an SVG with a linked PNG or JPEG from such a file.

```{code-cell} ipython3
!svgdigitizer create-svg --help
```

A {download}`Example PNG <./files/others/example_plot_p0.png>` for testing purposes is available in the `svgdigitizer` repository.

In addition to the linked image, elements for annotating a curve in a figure
can be embedded in the SVG from builtin templates with the `--template` option.

```{code-cell} ipython3
!svgdigitizer paginate ./files/others/example_plot_paginate.pdf --template basic
```

Custom templates can be included by providing to the `--template-file` argument a custom SVG  `<file path>`.
Only elements of the template SVG residing inside a group/layer with the `id` attribute `digitization-layer` are imported.

```{code-cell} ipython3
!svgdigitizer paginate ./files/others/example_plot_paginate.pdf --template-file ./files/others/custom_template.svg
```


(digitize)=
## `digitize`

Produces a CSV from the curve traced in the SVG.

```{code-cell} ipython3
!svgdigitizer digitize --help
```

### Examples

Consider the following skewed plot.

```{image} ./files/others/example_plot_p0.png
:width: 500px
:align: center
```

An unskewed digitized CSV can be created with

```{code-cell} ipython3
!svgdigitizer digitize ./files/others/example_plot_p0_demo_digitize.svg --skewed
```

The CSV can, for example, be imported as a pandas dataframe to create a plot.

```{code-cell} ipython3
:align: center
:class: bg-primary mb-1
:tags: [remove-stdout, remove-stderr]
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
:tags: [hide-input, remove-stdout, remove-stderr]
:width: 500px

import pandas as pd

df = pd.read_csv('./files/others/example_plot_p0_demo_digitize.csv')
df.plot(x='U', y='v', ylabel='v')
```

```{note}
The use of [`svgdigitizer digitize`](digitize) is discouraged when your axis labels contain units, because the output CSV does not contain this information. Use [`svgdigitizer figure`](figure) instead, which creates a frictionless datapackage (CSV + JSON).
```

## `plot`

Display a plot of the data traced in an SVG

```{code-cell} ipython3
!svgdigitizer plot --help
```

```{note}
The plot will only be displayed, when your shell is configure accordingly.
```

### Examples

The plot of an annotated example SVG (with skewed axis) with a specific sampling interval can be created with

```{code-cell} ipython3
!svgdigitizer plot ./files/others/example_plot_p0_demo_digitize.svg --skewed --sampling-interval 0.01
```

(figure)=
## `figure`

The figure command produces a CSV and an JSON with additional metadata, which contains, for example, information on the axis units. In addition it will reconstruct a time axis, when the rate at which the data on the x-axis is given in a text label in the SVG such as `scan rate: 30 m/s`. Here the unit must be equivalent to that on the x-axis divided by a time.

```{code-cell} ipython3
!svgdigitizer figure --help
```

```{note}
Flags `--bibliography`, `--metadata` and `si-units` are covered in the [advanced section](advanced-flags) section below.
```

### Examples

Consider the following figure where the annotated {download}`SVG (looping_scan_rate.svg)<./files/others/looping_scan_rate.svg>` contains a scan rate.

```{image} ./files/others/looping_scan_rate_annotated.png
:width: 400px
```

Digitize the figure with

```{code-cell} ipython3
:tags: [remove-stderr]

!svgdigitizer figure ./files/others/looping_scan_rate.svg --sampling-interval 0.01
```

Resulting in

```{code-cell} ipython3
:tags: [hide-input, remove-stderr]

import pandas as pd

df = pd.read_csv('./files/others/looping_scan_rate.csv')
df.plot(x='d', y='height', xlabel='distance [m]', ylabel='height [m]', legend=False)
```

## `cv`

The `cv` option is designed specifically to digitze [cyclic voltammograms (CVs)](https://en.wikipedia.org/wiki/Cyclic_voltammetry). Overall the command `cv` has the same functionality as the [`figure`](figure) command. The differences are as follows.

* Certain keys in the output metadata are directly related to cyclic voltammetry measurements.
* The units on the x-axis must be equivalent to volt `U` given in units of `V` and those on the y-axis equivalent to current `I` in units of `A` or current density `j` in units of `A / m2`.
* The voltage unit can be given vs. a reference, such as `V vs. RHE`. In that case, the dimension should be `E` instead of `U`.
* The `--sampling-interval` should be provided in units of `mV`.

These standardized CV data are, for example, used in the [echemdb](https://www.echemdb.org/cv) database.

```{code-cell} ipython3
!svgdigitizer cv --help
```

```{note}
Flags `--bibliography`, `--metadata` and `si-units` are covered in the [advanced section](advanced-flags) section below.
```

### Examples

An annotated example {download}`SVG<./files/mustermann_2021_svgdigitizer_1/mustermann_2021_svgdigitizer_1_f2a_blue.svg>` is shown in the following figure.

```{image} ./files/mustermann_2021_svgdigitizer_1/mustermann_2021_svgdigitizer_1_f2a_blue.png
:width: 400px
```

which can be digitzed via

```{code-cell} ipython3
:tags: [remove-stderr]

!svgdigitizer cv ./files/mustermann_2021_svgdigitizer_1/mustermann_2021_svgdigitizer_1_f2a_blue.svg --sampling-interval 0.01
```

(advanced-flags)=
## Advanced flags

### `--si-units`

The flag `--si-unit` is used by the [`figure`](figure) command and commands that inherit from `figure`, such as the `cv` command. The units are converted to SI units, if they are compatible with the [astropy](https://www.astropy.org/) unit package. The values in the CSV are scaled respectively and the new units are provided in the output JSON files.

```{warning}
In some cases conversion to SI units might not result in the desired output. For example, even though `V` is considered as an SI unit, astropy might convert the unit to `W / A` or `A Ohm`.
```

### `--metadata`

The flag `--metadata` allows adding metadata to the resource of the datapackage from a yaml file. It is used by the [`figure`](figure) command and commands that inherit from `figure`, such as the `cv` command.

Consider the following figure where the annotated {download}`SVG (looping_scan_rate.svg)<./files/others/looping_scan_rate.svg>`.

```{image} ./files/others/looping_scan_rate_annotated.png
:width: 400px
```

We collect additional metadata in a {download}`YAML file (looping_scan_rate_yaml.yaml)<./files/others/looping_scan_rate_yaml.yaml>` describing the underlying "experiment".

```{code-cell} ipython3
:tags: [remove-stderr]

!svgdigitizer figure ./files/others/looping_scan_rate_yaml.svg --metadata ./files/others/looping_scan_rate_yaml.yaml --sampling-interval 0.01
```

The metadata from the YAML is included in the JSON of the resulting datapackage and is accessible with a JSON loader

```{code-cell} ipython3
:tags: [output_scroll]

import json
with open('./files/others/looping_scan_rate_yaml.json', 'r') as f:
    metadata = json.load(f)
metadata
```

or directly with the frictionless interface

```{code-cell} ipython3
:tags: [output_scroll]

from frictionless import Package
package = Package('./files/others/looping_scan_rate_yaml.json')
package
```

For electrochemical data an example YAML can be found [here](https://github.com/echemdb/metadata-schema/blob/main/examples/file_schemas/svgdigitizer.yaml).

### `--bibliography`

The flag `--bibliography` adds a bibtex bibliography entry to the JSON of the produced datapackage. It is used by the [`figure`](figure) command and commands that inherit from `figure` such as the `cv` command.

Requirements:

* a file in the {download}`BibTex<./files/others/cyclist2023.bib>` format should exist in the same folder than the SVG (otherwise an empty string is returned)
* a YAML file must exist which is invoked with the `--metadata` option.
* the {download}`YAML file<./files/others/looping_scan_rate_bib.yaml>` file must contain a reference to the bib file such as

```yaml
source:
  citationKey: BIB_FILENAME  # without file extension
```

```{code-cell} ipython3
:tags: [remove-stderr]

!svgdigitizer figure ./files/others/looping_scan_rate_bib.svg --bibliography --metadata ./files/others/looping_scan_rate_bib.yaml --sampling-interval 0.01
```

The bib file content is included in the resulting JSON of the datapackge

```{code-cell} ipython3
:tags: [output_scroll]

from frictionless import Package
package = Package('./files/others/looping_scan_rate_bib.json')
package
```

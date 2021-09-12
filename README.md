# SVGDigitizer — (x,y) Data Points from SVG files

![Logo](./logo.svg)

The purpose of this project is to digitize plots in scientific publications, recovering the measured data visualized in such a plot.

## Installation

```
pip install -e .
```

## Command Line Interface

There's a simple command line interface.

```
$ svgdigitizer
Usage: python -m svgdigitizer [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  digitize
  paginate
  plot
$ svgdigitizer plot test/data/Ni111_NaOH_Beden1985_Fig2c.svg
[displays a plot]
$ svgdigitizer digitize test/data/Ni111_NaOH_Beden1985_Fig2c.svg
[creates test/data/Ni111_NaOH_Beden1985_Fig2c.csv]
$ svgdigitizer digitize test/data/Ni111_NaOH_Beden1985_Fig2c.svg
[creates test/data/Ni111_NaOH_Beden1985_Fig2c.csv]
$ svgdigitizer paginate <pdf file>
[paginates the pdf file]
```

## API

You can also use the `svgdigitizer` package directly from Python.

The examples are based on the test files provided with `svgdigitizer` in the folder `test/data`.
 
```python
from svgdigitizer.svgplot import SVGPlot
from svgdigitizer.svg import SVG

svgfile = f'svgdigitizer/test/data/xy_rate.svg'
    
svgplot = SVGPlot(SVG(open(svgfile, 'rb')))
```

`svgplot.df` provides a dataframe of the digitized curve.  
`svgplot.plot()` shows a plot of the digitized curve.


## Submodule CV

The submodule `electrochemistry.cv` is specifically designed to digitize cyclic voltamograms
commonly found in the field of electrochemistry.

```python
from svgdigitizer.svgplot import SVGPlot
from svgdigitizer.svg import SVG
from svgdigitizer.electrochemistry.cv import CV

svgfile = f'svgdigitizer/test/data/xy_rate.svg'
    
cv = CV(SVGPlot(SVG(open(svgfile, 'rb'))))
```

`cv.df` provides a dataframe with a time, voltage and current axis (in SI units). Depending on the type of data the current is expressed as current `I` in `A` or a current density `j` in `A / m2`.

The dataframe can for example be saved as `csv` via:

```python
from pathlib import Path
cv.df.to_csv(Path(svgfile).with_suffix('.csv'), index=False)
``` 

`cv.plot` shows a plot of the digitizd data with appropriate axis labels.  
`cv.metadadata` provides a dict with metadata of the original plot, i.e., original units of the axis.


`CV` also accepts a dict with metadata, which is updated with keywords related to the original figure (`figure descripton`), i.e., original axis units.

```python
import yaml
from svgdigitizer.svgplot import SVGPlot
from svgdigitizer.svg import SVG
from svgdigitizer.electrochemistry.cv import CV

svgfile = f'svgdigitizer/test/data/xy_rate.svg'
yamlfile = f'svgdigitizer/test/data/xy_rate.yaml'

with open(yamlfile) as f:
    metadata = yaml.load(f, Loader=yaml.FullLoader)

cv = CV(SVGPlot(SVG(open(svgfile, 'rb'))), metadata=metadata)
```
**Added:**

* Added module `svgdigitizer.svgfigure.SVGFigure` to digitize custom figures (which are not CVs.)
* Added assertions to `svgdigitizer.electrochemistry.cv.CV`, such that only E or U (I or j) labels are allowed on the x-axis (y-axis).
* Added `scan_rate_labels` to `svgdigitizer.svgfigure`, returning the labels in the SVG with a scan rate.
* Added possibility to reconstruct a time axis, when a scan rate is provided in the plot, who's units match those of the x-axis.
* Added keyword `measurement_type` to `svgdigitizer.svgfigure.SVGFigure`, which will be added to the metadata.
* Added keyword `force_si_units` to `svgdigitizer.svgfigure.SVGFigure`, which allows transformation of a figure with units into SI units.
* Added flag `--si-units` to the `cv` command in the command line interface.

**Changed:**

* Changed `svgdigitizer.svgplot.SVGplot.schema` to `svgdigitizer.svgplot.SVGplot.figure_schema`.

**Removed:**

* Removed the following methods and properties from `svgdigitizer.electrochemistry.cv.CV` which were also not transferred to `svgdigitizer.svgfigure.SVGFigure`: `voltage_dimension`, `current_dimension`, `_add_voltage_axis`, and `_add_current_axis`.

**Fixed:**

* Fixed detection of `simultaneous measurement` in `electrochemistry.cv.CV`.

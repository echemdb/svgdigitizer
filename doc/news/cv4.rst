**Added:**

* Added an axis `schema` to `electrochemistry.cv.CV` and `svgplot.SVGPlot`, describing the data extracted from the plot.
* Added `voltage_dimension` and `current_dimension` to `electrochemistry.cv.CV`, providing the dimension of the voltage and the current.

**Changed:**

* Changed `electrochemistry.cv.CV` such that it only accepts SVGs where the labels on one axis are either `U` or `E` (V, mV, ...) and another axis are `I` (A, mA, ...) or `j` (A / cm2, uA / m2, ...).  
* Changed `rate`` to `scan_rate`` in `electrochemistry.cv.CV`

**Removed:**

* Removed `axis_properties` and `x_label` from `electrochemistry.cv.CV`.

**Added:**

* Added the property `simultaneous_measurement` and `comment` to `svgdigitizer.electrochemistry.cv`, which read these properties from a text field in the SVG file.

**Changed:**

* Changed the output of the property `metadata` in `svgdigitizer.electrochemistry.cv`. It includes 'data_description', which contains the units to the values in the dataframe (df).
* Changed the dimension on the x-axis from `U` to `E` (potential).

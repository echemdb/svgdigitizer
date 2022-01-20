**Added:**

* Added the property `svgdigitizer.electrochemistry.cv.CV.simultaneous_measurement` which is read from a text field in the SVG file.

**Changed:**

* Changed the property `svgdigitizer.electrochemistry.cv.CV.metadata`. It now includes 'data description' which contains the units to the values in the dataframe.
* Changed the dimension on the x-axis of CVs from `U` to `E` (potential).

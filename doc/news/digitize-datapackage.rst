**Added:**

* Added the ``--metadata``, ``--si-units``, ``--bibliography``, and ``--citation-key`` options to the ``digitize`` CLI command.

**Changed:**

* Changed the ``digitize`` CLI command to create a frictionless datapackage (CSV + JSON) instead of only a CSV, so that the units and the version of svgdigitizer are recorded with the data (see `#247 <https://github.com/echemdb/svgdigitizer/issues/247>`_). When the SVG contains a scan rate, the CSV also contains a time axis.

**Deprecated:**

* Deprecated the ``figure`` CLI command, which is now an alias of the ``digitize`` command.

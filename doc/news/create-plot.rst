**Added:**

* Added a ``--plot`` flag to the ``digitize``, ``figure``, and ``cv`` CLI commands which writes a PNG of the digitized curve with labeled axes (including units) and the same scale as in the original figure.

**Changed:**

* Changed the ``plot()`` methods of ``SVGPlot``, ``SVGFigure``, and ``CV`` to return the matplotlib ``Axes`` and to use the same scale as in the original figure.

**Removed:**

* Removed the ``plot`` CLI command which is superseded by the ``--plot`` flag of the digitization commands.

**Fixed:**

* Fixed ``figure`` and ``cv`` failing to create a data package when ``--outdir`` was an absolute path with forward slashes.
* Fixed several issues in the documentation.

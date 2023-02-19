**Fixed:**

* Fixed doctesting of the command line interface, by moving the content from `__main__.py` to `entrypoint.py`.

**Removed:**

* Removed `__main__.py` as the entrypoint. As a result, `python -m svgdigitizer` does not invoke the digitizer anymore. The digitizer can still be invoked with `svgdigitizer` once installed.

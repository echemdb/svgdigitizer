**Fixed:**

* Fixed `Pdf.build_identifier` crashing with a `UnicodeEncodeError` when the bibtex entry contains plain UTF-8 characters outside latin-1 (e.g., `ć`, `ž`, or an em dash `—`). Such values are now used as-is instead of being passed through the LaTeX-to-unicode round-trip.

**Added:**

* Added retries to the download of citations from doi.org, since the services behind it occasionally fail with server errors.

**Fixed:**

* Fixed `Pdf.build_identifier` crashing with a `UnicodeEncodeError` when the bibtex entry contains plain UTF-8 characters outside latin-1 (e.g., `ć`, `ž`, or an em dash `—`). LaTeX escape sequences are now decoded with the `latex+utf8` codec, which also handles entries mixing LaTeX escapes and such characters.
* Fixed `Pdf.bibliographic_entry` failing with an unrelated `AttributeError` when the citation could not be downloaded. A `ConnectionError` describing the network error or HTTP status is now raised instead.

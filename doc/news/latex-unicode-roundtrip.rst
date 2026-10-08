**Fixed:**

* Fixed `Pdf.build_identifier` crashing with a `UnicodeEncodeError` when the bibtex entry contains plain UTF-8 characters outside latin-1 (e.g., `ć`, `ž`, or an em dash `—`). LaTeX escape sequences are now decoded with the `latex+utf8` codec, which also handles entries mixing LaTeX escapes and such characters.

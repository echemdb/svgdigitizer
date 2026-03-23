# svgdigitizer Codebase Report

Generated: 2026-03-18

---

## Overview

**svgdigitizer** is a Python library and CLI tool for recovering measured data from scientific
publication plots by digitizing manually annotated SVG files. The primary output is FAIR-compliant
frictionless datapackages (CSV + JSON metadata). It has a specialized electrochemistry submodule
targeting cyclic voltammograms for the echemdb.org project.

---

## Architecture

The code is organized in a clean layered hierarchy:

```
SVG (parsing)
  └── SVGPlot (coordinate transformation + path sampling)
        └── SVGFigure (units, metadata, datapackage creation)
              └── CV (electrochemistry-specific specialization)
```

### Key Modules

| File | Lines | Role |
|------|-------|------|
| `svgdigitizer/svgplot.py` | 2193 | Core digitization engine — coordinate transforms, Bézier sampling |
| `svgdigitizer/svgfigure.py` | 1834 | High-level figure processing — units, metadata, datapackages |
| `svgdigitizer/entrypoint.py` | 877 | Click-based CLI with 8 commands |
| `svgdigitizer/svg.py` | 647 | Low-level SVG DOM parsing via minidom |
| `svgdigitizer/pdf.py` | 328 | PDF-to-SVG pipeline, DOI extraction, citation fetching |
| `svgdigitizer/electrochemistry/cv.py` | ~300 | Cyclic voltammogram specialization |

---

## Core Algorithms

### 1. Coordinate Transformation

Extracts axis reference points (labeled `x1:`, `x2:`, `y1:`, `y2:`) from SVG annotations and
builds an affine transformation matrix mapping SVG pixel space → plot data space. Two modes:

- **axis-aligned** (default): assumes horizontal/vertical axes in SVG space
- **mark-aligned**: for skewed or scanned images where axes are not orthogonal

### 2. Path Sampling

Decomposes SVG paths into segments (Lines, Cubic Béziers), then solves polynomial root-finding
problems to sample at equidistant x (or y) intervals. The `_sample_segment` and `_min_real_root`
functions in `svgplot.py` handle the non-trivial Bézier mathematics.

### 3. Unit Handling

Parses axis labels with regex (e.g., `"E2: 1 mV vs. RHE"`), converts via `astropy.units`, and
optionally reconstructs a time axis from scan rates via dimensional analysis.

---

## CLI Commands

```
svgdigitizer digitize     # SVG → CSV (bare coordinates)
svgdigitizer figure       # SVG → frictionless datapackage with units
svgdigitizer cv           # SVG → electrochemistry datapackage
svgdigitizer plot         # Render SVG plot with matplotlib
svgdigitizer paginate     # PDF pages → SVG + PNG
svgdigitizer create-svg   # Image → SVG annotation template
svgdigitizer get-doi      # Extract DOI from PDF
svgdigitizer get-citation # Fetch BibTeX from DOI
```

---

## Dependencies

| Library | Purpose |
|---------|---------|
| `pandas` | DataFrames as primary output structure |
| `astropy` | Scientific unit parsing and conversion |
| `scipy` | Root-finding for Bézier sampling |
| `svgpathtools` / `svg.path` | SVG path parsing and manipulation |
| `frictionless` | FAIR datapackage standard |
| `pymupdf` | PDF rendering and text extraction |
| `click` | CLI framework |
| `pybtex` | BibTeX parsing |
| `pyyaml` | YAML metadata parsing |
| `requests` | HTTP calls to DOI API |
| `mergedeep` | Deep dict merging for metadata |
| `pillow` | Image processing for PNG export |

Requires Python >= 3.10.

---

## Testing

- **Doctests**: Every class and function has `EXAMPLES:` sections that double as runnable doctests
  (`pixi run doctest`). ~50+ examples embedded in source.
- **Regression tests**: 31 `.csv.expected` / `.json.expected` files in `test/data/` compared
  against CLI output.
- **Unit tests**: `svgdigitizer/test/cli.py` with `invoke()` helper and `TemporaryData` context
  manager; run in parallel via `pytest-xdist`.
- **Validation**: JSON schema validation of output metadata against echemdb schema
  (`pixi run validate`).

---

## Code Quality

### Strengths

- Consistent use of `@cached_property` for lazy evaluation throughout all major classes.
- Every class/method has thorough docstrings — the project treats documentation as a first-class
  deliverable.
- Modern packaging: `pyproject.toml` only, pixi for reproducible environments, no `setup.py`.
- Clean separation of concerns across the module hierarchy.
- Informative custom exception (`SVGAnnotationError`) with context-rich error messages.

### Observations / Weak Points

- **Large modules**: `svgplot.py` (2193 lines) and `svgfigure.py` (1834 lines) are large. Both
  could benefit from splitting into smaller focused modules, though the current structure is
  navigable due to clear property naming.
- **PDF DOI extraction** (`pdf.py`) is regex-based and scans only the first 2 pages — fragile for
  unusual PDF layouts.
- **Hardcoded skip-word list** in `pdf.py` (150+ entries for file naming from citations) — could
  be externalized to configuration.
- **Circular import** between `cv.py` and `svgfigure.py` is worked around with late imports and
  `# pylint: disable=cyclic-import` comments rather than a structural fix.

---

## Summary

svgdigitizer is a well-engineered, domain-focused scientific tool. The architecture is clean and
intentional, the documentation is exemplary, and the testing strategy (doctests + regression files)
is appropriate for a data-extraction tool where output correctness is paramount.

The main growth areas would be:

1. Breaking up the two largest modules (`svgplot.py`, `svgfigure.py`) into smaller units.
2. Hardening the PDF text extraction pipeline beyond regex-on-first-two-pages.
3. Resolving the circular import between `cv.py` and `svgfigure.py` structurally.

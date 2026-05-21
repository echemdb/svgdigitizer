---
title: 'svgdigitizer: A Python package for recovering data from plots of scientific publications'
tags:
  - Python
  - data digitization
  - FAIR data
  - scientific data recovery
  - electrochemistry
authors:
  - name: Johannes M. Hermann
    orcid: 0000-0001-7119-1295
    corresponding: true
    affiliation: 1
  - name: Nicolas G. Hörmann
    orcid: 0000-0001-6944-5575
    affiliation: 2
  - name: Albert K. Engstfeld
    orcid: 0000-0002-9686-3948
    corresponding: true
    affiliation: 1
  - name: Julian Rüth
    orcid: 0000-0002-3930-9107
    affiliation: 3
affiliations:
  - name: Institute of Electrochemistry, Ulm University, D-89069 Ulm, Germany
    index: 1
    ror: 032000t02
  - name: Fritz-Haber-Institut der Max-Planck-Gesellschaft, Faradayweg 4-6, 14195 Berlin, Germany
    index: 2
    ror: 03k9qs827
  - name: Julian Rüth GmbH, Weinbergstr. 48, D-97261 Güntersleben, Germany
    index: 3
date: 23 March 2026
bibliography: paper.bib
---

# Summary

Scientific knowledge is communicated primarily through publications, where quantitative data is
most often presented as two-dimensional figures rather than as machine-readable tables. Once a
study is published, the underlying numerical data frequently becomes inaccessible — particularly
for older literature where digital data was never archived. `svgdigitizer` is a Python library
and command-line tool that recovers quantitative data from such figures by digitizing curves
manually traced in Scalable Vector Graphics (SVG) files. The user imports a figure image into a
vector graphics editor (e.g., Inkscape [@inkscape_2025]), traces the curve of interest with Bézier
paths, and annotates the coordinate system with text labels. `svgdigitizer` then applies an
affine coordinate transformation to map SVG pixel coordinates to plot data coordinates and
samples the Bézier paths at configurable intervals to produce a tabular dataset. Physical unit
information encoded in axis labels is parsed via `astropy.units` [@astropy_2022_astropy_167] and propagated to
the output. The digitized data is exported as a *frictionless datapackage* [@frictionless_2026] — a
CSV file accompanied by a JSON descriptor containing units, metadata, and bibliographic
information — enabling FAIR-compliant [@wilkinson_2016_fair_160018] data reuse and sharing.

# Statement of Need

The ability to extract quantitative data from published figures is essential across scientific
research. Meta-analyses, literature benchmarking, and database curation all require numerical
data that is often available only in graphical form. This problem is particularly acute for
historical literature, where measurements were never stored digitally beyond the printed figure,
but it equally affects modern publications that do not accompany figures with machine-readable
raw data.

`svgdigitizer` addresses this need for researchers who require systematic, reproducible, and
metadata-rich digitization of scientific plots. Beyond one-off data extraction, it is designed
for workflows in which the same figure may be re-digitized with different sampling parameters,
or in which digitized data from many publications must be aggregated into a common curated
dataset. The FAIR frictionless datapackage output format enables digitized data to be shared,
versioned, and integrated into databases with minimal friction.

A primary motivation for `svgdigitizer` is the [echemdb.org](https://www.echemdb.org/cv)
community database of cyclic voltammograms [@echemdb_2026], where contributions are curated as SVG
files digitized with `svgdigitizer`. This workflow enables electrochemists to contribute
historical literature data systematically, with each entry carrying full provenance metadata
and physically meaningful units.

# State of the Field
Several tools are available for extracting numerical data from published plots, ranging from web-based interfaces to windows-only desktop and cross-platform applications, and spanning both open-source and commercial licenses. Examples include WebPlotDigitizer [@rohatgi_2022], Engauge Digitizer [@mark_mitchell_2020_3941227], and OriginPro [@origin_2026]. These tools typically provide interactive workflows for recovering data points from graphical representations through manual selection or semi-automated detection methods, enabling plotted information to be converted into reusable numerical datasets. Both tools are
well-suited to one-off, GUI-driven data extraction. However, neither exports physical units,
neither produces structured metadata, and neither offers a programmable Python API for
integration into automated workflows.

`svgdigitizer` was designed as a distinct tool rather than a contribution to existing projects
for three principal reasons. First, its input format is fundamentally different: rather than
working with raster images and mouse clicks, `svgdigitizer` operates on SVG files in which
curves are represented as Bézier paths drawn with vector graphics tools. The curve tracing —
the most labor-intensive step — is stored as a reusable, version-controllable artifact that can
be reprocessed at any time with different parameters, without repeating the manual work. Second,
`svgdigitizer`'s output is a structured FAIR datapackage with physical units, and this design
is central to the tool's purpose rather than an optional feature. Third, deep integration with
the scientific Python ecosystem — `astropy.units` [@astropy_2022_astropy_167] for unit parsing, `pandas` [@pandas_2026_pandas_18675244] for
tabular output, `frictionless` [@frictionless_2026] for datapackage creation — serves specialized scientific
workflows that require FAIR data as a first-class output, which is not addressed by other digitizer solutions.

# Software Design

`svgdigitizer` is organized in a layered class hierarchy, each layer adding abstraction over
the one below:

- `SVG`: parses the SVG DOM and exposes labeled paths and text elements.
- `SVGPlot`: reads axis reference-point labels (e.g., `x1: -40`, `x2: 40`) and constructs an
  affine transformation from SVG pixel space to plot data space.
- `SVGFigure`: adds unit handling, metadata extraction, and frictionless datapackage output.
- `CV` (`svgdigitizer.electrochemistry`): a domain-specific subclass for cyclic voltammograms.

Two coordinate transformation modes are supported: *axis-aligned* (default, for standard
upright plots) and *mark-aligned* (for skewed or scanned figures with non-orthogonal axes).
Bézier path segments are sampled by solving polynomial root-finding problems via `scipy`
[@scipy], yielding data points at configurable equidistant intervals along the x (or y) axis.
This enables dense, uniform sampling of curved regions without user-specified point placement.

Unit handling uses `astropy.units` to parse axis labels (e.g., `E2: 1 V vs. RHE`), convert
to SI where needed, and optionally reconstruct a time axis from a scan rate annotation (e.g.,
`scan rate: 50 mV / s`) through dimensional analysis. Metadata from annotations embedded
in the SVG and from external YAML and BibTeX files is merged into the datapackage descriptor,
producing a self-describing output bundle.

Advanced annotation features include support for **scale bars** (deriving axis scale from a
labeled reference bar), numeric **scaling factors** (
rescaling of an axis often found for a curve in multi-signal overlays), and
**scatter plots** (extracting individual data points without Bézier interpolation).

A CLI built with `click` [@click_exposes the full feature set without Python knowledge in a convenient way. Notably, the
`paginate` command converts PDF pages to SVG+PNG files ready for annotation, while optionally renaming (`--rename`) the file base to a sluggified identifier generated from the citation (retrieved with the extracted DOI from the PDF via [doi.org](https://doi.org)) streamlining provenance metadata collection. After curve tracing the `digitize` command yields a datapackage. 

# Research Impact Statement

`svgdigitizer` underpins the [echemdb.org](https://www.echemdb.org/cv) cyclic voltammogram
database [@echemdb], a community-curated collection of electrochemical measurements from the
literature. Every entry in this database was digitized using `svgdigitizer` and stored as a
frictionless datapackage, enabling programmatic access to historical electrochemical data. The
database is consumed by the companion package `unitpackage` [@engstfeld_2026_19051513], which provides a
high-level API for querying and comparing digitized datasets. Both tools form the data layer of
a lightweight file-system-based approach to research data management described in
[@engstfeld_2025_lightweight_013].

The package is distributed via [PyPI](https://pypi.org/project/svgdigitizer/) and
[conda-forge](https://github.com/conda-forge/svgdigitizer-feedstock), is archived on Zenodo
[@engstfeld_2026_18777355] under DOI 10.5281/zenodo.8428961, and has been under active development
since June 2021 with over 1,600 commits from multiple contributors.

<!-- PLACEHOLDER: Add specific publications that have used or cited svgdigitizer. -->
[@bergmann_2023_initiobased_8815], [@heubach_2025_reproducibility_1910], [@fritsche_2026_microstructure_116061], [@engstfeld_2025_lightweight_013]

# AI Usage Disclosure

No generative AI tools were used in the development of this software or the preparation of
supporting materials. The initial draft of this manuscript was produced with the assistance of
Claude Sonnet 4.6 (Anthropic) as a writing aid. All content was reviewed, revised, and
validated by the authors, who take full responsibility for the accuracy of the manuscript.

# Acknowledgements

AKE gratefully acknowledges support by the DFG (German Science Foundation) through the
collaborative research centre SFB-1316 (project ID: 327886311).


# References

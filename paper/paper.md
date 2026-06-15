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
and command-line tool that recovers the data from such figures by digitizing curves
manually traced in carefully annotated Scalable Vector Graphics (SVG) files,
a XML-based format that allows programmatic access to its elements.
The user imports a figure image into a
vector graphics editor, e.g., Inkscape [@inkscape_2025], traces the curve of interest with Bézier
paths, and annotates the coordinate system with text labels  (\autoref{fig:workflow} left). `svgdigitizer` then applies an
affine coordinate transformation to map SVG pixel coordinates to plot data coordinates and
samples the Bézier paths at user-defined intervals to produce a tabular dataset. Physical unit
information encoded in axis labels is parsed via `astropy.units` [@astropy_2022_astropy_167] and propagated to
the output. The digitized data is exported as a *frictionless datapackage* [@frictionless_2026] — a
CSV file accompanied by a JSON descriptor containing units, metadata, and bibliographic
information, enabling FAIR (Findable, Accessible, Interoperable, and Reusable)-compliant [@wilkinson_2016_fair_160018] data  (\autoref{fig:workflow} right).

![`svgdigitizer` transforms an annotated SVG figure (left) into a frictionless datapackage consisting of a CSV file with the curve data and a JSON descriptor containing axis units and extracted metadata (right).\label{fig:workflow}](workflow.png)

# Statement of Need

The ability to extract quantitative data from published figures is essential across scientific
research. Meta-analyses, literature benchmarking, and database curation all require numerical
data that is often available only in graphical form. This problem is particularly acute for
historical literature, where measurements were never stored digitally beyond the printed figure,
but it equally affects modern publications that do not accompany figures with machine-readable
raw data.
While in most cases specific values or summary statistics of measurement data is sufficient, and which can often be extracted from the text body manually or large language models, in some cases the entire curve must be preserved.

`svgdigitizer` addresses this need for researchers who require systematic, reproducible, and
metadata-rich digitization of the entire curve in a scientific plot (see \autoref{fig:workflow}). Beyond one-off data extraction, it is designed
for workflows in which the same figure may be re-digitized with different sampling parameters,
or in which digitized data from many publications must be aggregated into a common curated
dataset. The FAIR frictionless datapackage output format enables digitized data to be shared,
versioned, and integrated into databases with minimal friction.

A primary motivation for `svgdigitizer` is the
community database of cyclic voltammograms [@echemdb_2026; @ECHEMDATA], where contributions are curated as SVG
files digitized with `svgdigitizer`. This workflow enables electrochemists to contribute
historical literature data systematically, with each entry carrying full provenance metadata
and physically meaningful units.

# State of the Field

Several tools are available for extracting numerical data from published plots, ranging from web-based interfaces to windows-only desktop and cross-platform applications, and spanning both open-source and commercial licenses.
Examples include WebPlotDigitizer [@rohatgi_2022], starry-digitizer (built on WebPlotDigitizer) [@KATSURA2025], Engauge Digitizer [@mark_mitchell_2020_3941227], or OriginPro [@originpro_2026].
These tools typically provide interactive workflows for recovering data points from graphical representations through manual selection or semi-automated detection methods, enabling plotted information to be converted into reusable numerical datasets. Furthermore they are
well-suited to one-off, GUI-driven data extraction. However, they usually do not allow exporting physical units,
nor produce structured metadata, nor offer a programmable Python API for
integration into automated workflows.

In the following, we briefly summarize the current limitations of the available tools.
`svgdigitizer` was designed as a distinct tool rather than a contribution to existing projects for several reasons.
First, the commonly available tools
work with raster images where individual data points are selected on the curve by mouse clicks and to some extent by auto detection methods, which then present the final dataset. starry-digitizer allows interpolating between selected datapoints to get a more fine grained dataset.
Second, common tools sample across one of the axis (usually the $x$-axis). This presents an issue when a curve follows a path that has multiple $y$-axis values per $x$-axis value, leading to scattering of the output data upon sampling along the $x$-axis.
Third, in most cases once the digitization process is finished, the curve-tracing and plot annotation (input data for the extraction process) is not preserved in a reusable, version-controllable artifact that can
be reprocessed at any time with different parameters, without repeating the manual work.
Fourth, extraction of physical units and the creation of standardized file formats including metadata is a central aspect to render output data reusable, which has only been adopted recently in the starry-digitizer.
Finally, open source APIs are lacking, which limit the integration with
the other scientific ecosystems, such as Python, and the development of domain specific modules to extract specific types of data according to pre defined standards.

# Software Design

The `svgdigitizer` module is organized in a layered class hierarchy, each layer adding abstraction over
the one below:

- `SVG`: parses the carefully annotated SVG document object model (DOM) and exposes labeled paths and text elements.
- `SVGPlot`: reads axis reference-point labels, e.g., `x1: -40`, `x2: 40`, and constructs an
  affine transformation from SVG pixel space to plot data space.
- `SVGFigure`: adds unit handling, metadata extraction, and frictionless datapackage output.
- `CV` (`svgdigitizer.electrochemistry`): a domain-specific subclass for cyclic voltammograms.

Two coordinate transformation modes are supported: *axis-aligned* (default, for standard
upright plots) and *mark-aligned* (for skewed or scanned figures with non-orthogonal axes).

The carefully annotated SVG files used by `svgdigitizer` contain the following elements, required for the data recovery workflow.
A curve which consists of individual points manually placed by the user on the curve, which are connected by
Bézier path segments.
 During the recovery process, these curves are sampled by solving polynomial root-finding problems via `scipy`
[@virtanen_2020_scipy_261], yielding data points at configurable equidistant intervals along the $x$ (or $$y$) axis.
This enables dense, uniform sampling of curved regions without user-specified point placement.
Axis labels contain an identifier (two for each axis), the value, a unit, and in some special cases also additional information, such as `E2: 1 V vs. RHE`.
The units follow the `astropy.units` notation, allowing for example, transformation of the data into SI units.
The label is decomposed using regular expressions, where the values allow for reconstructing the curve.
A text label `scan rate: 50 mV / s` can be added to the curve, which allows reconstructing the time axis of the time series data.
Metadata from annotations embedded
in the SVG, such as additional text fields with comments or other information about the figure, is extracted as Python dictionary.

Advanced annotation features include support for **scale bars** (deriving axis scale from a
labeled reference bar), numeric **scaling factors** (rescaling of an axis often found
for a curve in multi-signal overlays), and
**scatter plots** (extracting individual data points without Bézier interpolation).

The standard output of svgdigitizer are frictionless datapackages, which consist of a CSV (including the curve data) and a JSON (providing information on the axis units and additional metadata from the SVG) file.
During the creation of the datapackage, additional metadata can be added from external YAML and BibTeX files into the datapackage descriptor,
producing a self-describing output bundle.

A CLI built with `click` [@click_2026] exposes the full feature set without Python knowledge in a convenient way. Notably, the
`paginate` command converts PDF pages to SVG and PNG files ready for annotation (where the PNG is linked into the SVG),
while optionally renaming (`--rename`) the file base to a sluggified identifier generated from the citation (retrieved with the extracted DOI from the PDF via [doi.org](https://doi.org)) 
streamlining provenance metadata collection.
After curve tracing the `digitize` command yields a datapackage.

# Research Impact Statement

`svgdigitizer` underpins the cyclic voltammogram
database [@echemdb_2026; @ECHEMDATA], a community-curated collection of electrochemical measurements from the
literature.
Some of the data were extracted for specific scientific purposes to address specific questions in the field of electrochemistry [@bergmann_2023_initiobased_8815; @heubach_2025_reproducibility_1910].
The input data of the database is stored in the above described file formats (SVG and YAML), which allows adjusting curve tracings or resolve other annotation errors by the community.[@ECHEMDATA]
The output data is made accessible to the community via the `unitpackage` [@engstfeld_2026_19051513] API.
Both tools form the data layer of a lightweight file-system-based approach 
to research data management described in [@engstfeld_2025_lightweight_013].
`svgdigitizer` was also used by Fritsche et al. to extract geometric features from weld cross sections of refill friction stir spot welds joining additive-manufactured to wrought aluminium alloys [@fritsche_2026_microstructure_116061].

The package is distributed via [PyPI](https://pypi.org/project/svgdigitizer/) and
[conda-forge](https://github.com/conda-forge/svgdigitizer-feedstock), is archived on Zenodo
[@engstfeld_2026_18777355] under DOI 10.5281/zenodo.8428961, and has been under active development
since June 2021 with over 1,600 commits from multiple contributors.

# AI Usage Disclosure

No generative AI tools were used in the development of the `svgdigitizer` software package and its repository, including code, tests, and documentation. The initial draft of this manuscript was produced with the assistance of
Claude Sonnet 4.6 (Anthropic) as a writing aid, based on the documentation of the `svgdigitizer` project. All content was reviewed, revised, and
validated by the authors, who take full responsibility for the accuracy of the manuscript.

# Acknowledgements

AKE gratefully acknowledges support by the DFG (German Science Foundation) through NFDI4Chem (project number: 441958208).


# References

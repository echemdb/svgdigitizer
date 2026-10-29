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
date: 26 October 2026
bibliography: paper.bib
---

# Summary

Scientific knowledge is communicated primarily through publications, where quantitative data is
most often presented as two-dimensional figures rather than as machine-readable tables. Once a
study is published, the underlying numerical data frequently becomes inaccessible — particularly
for older literature where digital data was never archived. `svgdigitizer` is a Python library
and command-line tool that recovers the data from such figures by digitizing curves
manually traced in carefully annotated Scalable Vector Graphics (SVG) files,
an XML-based format that also allows programmatic access to its elements.
The annotated SVG file is the persistent record of the digitization, which can be kept under version control, corrected later, and re-processed at any time to re-derive the data.
The user imports a figure image into a
vector graphics editor, e.g., Inkscape [@inkscape_2025], creates a high-level model of the curve of interest by tracing it with Bézier
paths, and annotates the coordinate system with text labels  (\autoref{fig:workflow} left). `svgdigitizer` then applies an
affine coordinate transformation to map SVG pixel coordinates to plot data coordinates and
samples the Bézier paths at user-defined intervals to produce a tabular dataset. Physical unit
information encoded in axis labels is parsed via `astropy.units` [@astropy_2022_astropy_167] and propagated to
the output. The digitized data is exported as a *Frictionless Data Package* [@frictionless_2026] — a
CSV file accompanied by a JSON descriptor containing units, metadata, and bibliographic
information, enabling FAIR (Findable, Accessible, Interoperable, and Reusable)-compliant [@wilkinson_2016_fair_160018] data  (\autoref{fig:workflow} right).

![`svgdigitizer` transforms an annotated SVG figure (left) into a Data Package consisting of a CSV file with the curve data and a JSON descriptor containing axis units and extracted metadata (right).\label{fig:workflow}](workflow.png)

# Statement of Need

The ability to extract quantitative data from published figures is essential across scientific
research. Meta-analyses, literature benchmarking, and database curation all require numerical
data that is often available only in graphical form. This problem is particularly acute for
historical literature, where measurements were never stored digitally beyond the printed figure,
but it equally affects modern publications that do not accompany figures with machine-readable
raw data.
While in many cases specific values or summary statistics of the measurement data are sufficient, which can often be extracted from the text body, in other cases the entire curve must be preserved.

`svgdigitizer` addresses this need for researchers who require systematic, reproducible, and
metadata-rich digitization of the entire curve in a scientific plot (see \autoref{fig:workflow}).
Rather than treating digitization as a one-off extraction, it preserves the manual curve tracing, which models the measurement data, and plot annotation as a reusable SVG artifact.
The same figure can therefore be re-processed with different sampling parameters,
annotation errors can be corrected later by anyone with access to the file, and digitized data from many publications can be aggregated into a common curated
dataset in which every entry can be traced back to, and re-derived from, its annotated figure. The FAIR Data Package output format enables digitized data to be shared,
versioned, and integrated into databases with minimal friction.

A primary motivation for `svgdigitizer` is the
community database of cyclic voltammograms [@echemdb_2026; @ECHEMDATA], where contributions are curated as SVG
files digitized with `svgdigitizer` in a version-controlled repository. This workflow enables electrochemists to contribute
historical literature data systematically, with each entry carrying full provenance metadata
and physically meaningful units, and allows the community to review and correct the tracings at any time.

# State of the Field

Several tools are available for extracting numerical data from published plots, ranging from web-based interfaces to Windows-only desktop and cross-platform applications, and spanning both open-source and commercial licenses.
Examples include WebPlotDigitizer [@rohatgi_2024], starry-digitizer [@KATSURA2025], Engauge Digitizer [@mark_mitchell_2020_3941227], and OriginPro [@originpro_2026], as well as the Python-based PlotDigitizer [@dilawar_singh_2024_13292942], which supports batch processing of similar plots, and PyDigitizer [@nedelcu_2023_pydigitizer_012015].
These tools provide interactive or command-line workflows in which data points are selected on a raster image by mouse clicks or (semi-)automated detection, and they are well suited to one-off data extraction.

All of these tools perform the digitization on a raster image and produce a list of data points as their result.
`svgdigitizer` differs from them in the following aspects.
First and most importantly, the digitization itself, i.e., the traced curve together with the axis calibration, units, and metadata, is preserved in an annotated SVG file.
This plain-text artifact can be stored under version control next to the data, reviewed and corrected by others, and re-processed at any time, e.g., with a different sampling interval, without repeating the manual work.
Some tools, such as WebPlotDigitizer [@rohatgi_2024], can save the axis calibration together with the selected points or the settings of their automatic extraction in tool-specific project files, but not the traced curve itself, nor the physical units and metadata of the plot.
Second, the traced Bézier path used in our work is a continuous model of the curve rather than a set of selected points.
Data points are sampled from this model at any desired resolution, segment by segment along the path, so that curves with multiple $y$-values per $x$-value, such as cyclic voltammograms, are reproduced without the scattering that occurs in common tools, which sample along one of the axes. Note that starry-digitizer mitigates this by interpolating between selected points.
Third, physical units and metadata are exported in our tool along with the data as a standardized Frictionless Data Package, so that the output is self-describing and can be validated and processed by generic tools.
Finally, the Python API allows building domain-specific modules on top of the general workflow, such as the module for cyclic voltammograms described below.

We built `svgdigitizer` as a separate tool rather than contributing to an existing digitizer, because its central design decision, to make the annotated vector graphic rather than a list of extracted points the primary record of a digitization, determines the data model of the entire workflow from the input to the output.
Instead of implementing a graphical interface of its own, `svgdigitizer` relies on established vector graphics editors, such as Inkscape, for tracing, and focuses on the reproducible conversion of the annotated SVG into data.

# Software Design

The central design decision of `svgdigitizer` is to rely on curves traced manually by the user rather than on automatic curve detection.
This choice costs human effort for every figure, and it requires the user to follow annotation conventions and to work in an external vector graphics editor.
In return, every data point originates from a traced path that can be inspected directly on top of the original figure in the vector graphics program.
A inaccurate tracing or label can be corrected later, by anyone, directly in the SVG, without redoing the rest of the work.
Furthermore, manual tracing avoids misdetection of curves, e.g., of overlapping or crossing curves of the same color or of curves partially hidden behind labels.
Since tracing and labeling are done in a general-purpose vector graphics editor, the user does not need to learn a dedicated graphical interface, and the package does not need to maintain one.

The `svgdigitizer` module is organized in a layered class hierarchy, in which each layer adds abstraction over
the one below.

- `SVG`: parses the carefully annotated SVG document object model (DOM) and exposes labeled paths and text elements.
- `SVGPlot`: reads axis reference-point labels, e.g., `x1: -40`, `x2: 40`, and constructs an
  affine transformation from SVG pixel space to plot data space.
- `SVGFigure`: adds unit handling, metadata extraction, and Data Package output.
- `CV` (`svgdigitizer.electrochemistry`): a domain-specific subclass for cyclic voltammograms.

Two coordinate transformation modes are supported, the default *axis-aligned* mode for standard
upright plots and the *mark-aligned* mode for skewed or scanned figures with non-orthogonal axes.

An annotated SVG contains a curve, traced as a path which consists of Bézier segments through points placed manually by the user on the curve, and text labels for two reference points on each axis, consisting of an identifier, a value, and optionally a unit, which can include a reference, such as `E2: 1 V vs. RHE`.
The labels are decomposed with regular expressions, and the units are parsed with `astropy.units`, which allows, e.g., converting the data into SI units.
The curves are sampled by solving polynomial root-finding problems via `scipy`
[@virtanen_2020_scipy_261], yielding data points at configurable equidistant intervals along the $x$ (or $y$) axis, independent of how many points the user placed on the curve.
For scatter plots, the sampling is omitted and the placed points are used directly.
Further labels, e.g., `scan rate: 50 mV / s` to reconstruct the time axis of time series data, scale bars, and scaling factors of individual curves, are interpreted in the same way, while all other text annotations are extracted as metadata.

The output is a Data Package, i.e., a CSV file with the curve data and a JSON descriptor with the axis units and the metadata from the SVG, which can be complemented with metadata from external YAML and BibTeX files.
A CLI built with `click` [@click_2026] exposes this workflow without Python knowledge.
For example, the `paginate` command converts the pages of a PDF into SVG files ready for annotation and optionally names them after the citation retrieved via the DOI of the publication.
After the curves have been traced, the `figure` and `cv` commands convert the annotated SVG into a Data Package.

# Research Impact Statement

`svgdigitizer` underpins the cyclic voltammogram
database [@echemdb_2026; @ECHEMDATA], a community-curated collection of electrochemical measurements from the
literature.
Some of the data were extracted for specific scientific purposes to address specific questions in the field of electrochemistry [@bergmann_2023_initiobased_8815; @heubach_2025_reproducibility_1910].
The input data of the database is stored in the above described file formats (SVG and YAML), which allows adjusting curve tracings or resolve other annotation errors by the community [@ECHEMDATA].
The output data is made accessible to the community via the `unitpackage` [@engstfeld_2026_19051513] API.
Both tools form the data layer of a lightweight file-system-based approach
to research data management described in [@engstfeld_2025_lightweight_013].
`svgdigitizer` was also used by Fritsche et al. to extract geometric features from weld cross sections of refill friction stir spot welds joining additive-manufactured to wrought aluminum alloys [@fritsche_2026_microstructure_116061].

The package is distributed via [PyPI](https://pypi.org/project/svgdigitizer/) and
[conda-forge](https://github.com/conda-forge/svgdigitizer-feedstock), is archived on Zenodo
[@engstfeld_2026_21364209], and has been under active development
since June 2021 with about 1,800 commits from multiple contributors.

# AI Usage Disclosure

No generative AI tools were used in the development of the `svgdigitizer` software package, including code, tests, and documentation, with one exception. During the revision of this manuscript, the community guidelines and project metadata of the repository (contributing guidelines, code of conduct, citation file, and the corresponding sections of the README and documentation) were drafted with the assistance of Claude Opus 5.5 (Anthropic) and reviewed by the authors. The initial draft of this manuscript was produced with the assistance of
Claude Sonnet 4.6 (Anthropic) as a writing aid, based on the documentation of the `svgdigitizer` project. All content was reviewed, revised, and
validated by the authors, who take full responsibility for the accuracy of the manuscript.

# Acknowledgements

AKE gratefully acknowledges support by the DFG (German Science Foundation) through NFDI4Chem (project number 441958208).


# References

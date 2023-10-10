---
jupytext:
  formats: ipynb,md:myst
  text_representation:
    extension: .md
    format_name: myst
    format_version: 0.13
    jupytext_version: 1.14.5
kernelspec:
  display_name: Python 3 (ipykernel)
  language: python
  name: python3
---

Digitizing plots for echemdb
============================

The [echemdb.org](https://www.echemdb.org/cv) collection accepts plots commonly found in electrochemical research papers, e.g., cyclic voltammograms. The following example plot is provided in Figure 2a in the {download}`publication example (PDF)<./files/mustermann_2021_svgdigitizer_1/mustermann_2021_svgdigitizer_1.pdf>`.

```{image} files/images/sample_data_2.png
:class: bg-primary mb-1
:width: 450px
:align: center
```

Data uploaded to [echemdb.org](https://www.echemdb.org/cv) requires specifically annotated SVG files, including a specific metadata file, and a bibliography file explained in the following step by step tutorial.

## Step 1: Prepare PDF and BIB files

**1: Create a new directory**

The directory should be named `FirstAuthorName_Year_FirstTitleWord_FirstPageNr`.

```{note}
**Only use lowercase names and words.**
```

For the example PDF this comes down to

`mustermann_2021_svgdigitizer_1`

The page number should be the page number in the published pdf. Since the example is not published the page number is `1`. In other cases this could be `1021`.

Put the publication PDF in the newly created directory. The PDF should be named according to the same scheme:

`mustermann_2021_svgdigitizer_1.pdf`

**2: Place a BIB file in the folder**

A suggested approach is to search for the article with [Google Scholar](https://scholar.google.com/).

Modify the scholar settings so that a BibTeX link appears below the citation:

Click on the 3 lines next to the Google Scholar logo and choose ***Settings***

```{image} files/images/scholar_options_selection.png
:class: bg-primary mb-1
:width: 200px
:align: center
```

Select `Show links to import citations into BibTeX`

```{image} files/images/scholar_options_bibtex.png
:class: bg-primary mb-1
:width: 300px
:align: center
```

An `import into BibTeX` link appears below the linked article:

```{image} files/images/scholar_options_bibtex_link.png
:class: bg-primary mb-1
:width: 500px
:align: center
```

Download the bib file or save the content to a file named:

`mustermann_2021_svgdigitizer_1.bib`

Open the file and change the key, such that it matches the folder name:

```{image} files/images/bibtex_key.png
:class: bg-primary mb-1
:width: 550px
:align: center
```

```{note}
Fix any typos in the title and other entries if necessary.
```

**The folder should now contain the following files:**

`mustermann_2021_svgdigitizer_1.bib`

`mustermann_2021_svgdigitizer_1.pdf`

## Step 2: Prepare SVG and PNG files from the PDF

Use the [CLI](cli.md) to create SVG and PNG files from the PDF, i.e., execute the following command in the folder with the PDF.

```{code-cell} ipython3
:tags: [remove-stderr]

!svgdigitizer paginate mustermann_2021_svgdigitizer_1.pdf
```

The resulting filenames are of the form:

`mustermann_2021_svgdigitizer_1_p0.png`

`mustermann_2021_svgdigitizer_1_p0.svg`

```{note}
The page count starts from 0. It does not reflect the original page number in the PDF.
```

## Step 3: Digitize a plot

**1: Select an svg file with a plot to be digitized**

The data in Figure 2a in the example PDF on page 2 (filename containing `_p1`)  contains three curves, which can be identified by their colors. Each digitized curve should be in a separate SVG file.
Therefore, create a copy of the SVG file of page two (`mustermann_2021_svgdigitizer_1_p1.svg`) and rename it to`mustermann_2021_svgdigitizer_1_f2a_blue.svg`. Here, `_f2a_blue` indicates that the digitized curve is in Fig. 2b and that the curve is blue. The identifier will later also be included in the SVG file.

```{note}
`_p1` can be ommited since the figure can unambiguously be identified by the figure and curve identifier label, e.g., `_f2a_blue`).
```

**2: Annotate the SVG and curve tracing**

In principle the SVG is annotated and the curve us traced in the same way as described in the [usage](usage.md) section. A few additional notes are provide below the {download}`annotated SVG <./files/mustermann_2021_svgdigitizer_1/mustermann_2021_svgdigitizer_1_f2a_blue.svg>`.

```{image} files/images/inkscape_final.png
:class: bg-primary mb-1
:width: 550px
:align: center
```

Some remarks on the specific annotations:

* The units on the x-axis must be equivalent to a voltage `U` given in units of `V` and those on the y-axis equivalent to current `I` in units of `A` or current density `j` in units of `A / m2`.
* The voltage unit can given vs. a reference, such as `V vs. RHE`. In that case the dimension should be a potential `E` instead of voltage `U`.
* The curve identifier should be a short unambiguous string, preferably without special characters.
* A scan rate is mandatory. The information is not necessarily found in the figure (legend).
* Add a figure identifier such as `figure: 2a`
* Add tags describing the data with commonly used acronyms. In this case: `tags: BCV, HER`. Otherwise the data can hardly be classified.
* Feel free to add a comment to the plot. Use a full sentence, for example, `comment: The curve is a bit noisy.`
* Add a text field highlighting any additional measurements which were acquired simultaneously with the digitized curve and are shown in the same figure. In the example, the bottom plot shows DEMS data. This can be indicated by `linked: DEMS`. The field can contain multiple types of measurements if applicable. Also feel free to use acronyms commonly used in the community.

## Step 4: Create a metadata file for each digitized curve

Create a YAML file with the same name as the SVG file: `mustermann_2021_svgdigitizer_1_f2a_blue.yaml`

The general structure of the yaml file for the website is provided at [echemdb/electrochemistry-metadata-schema](https://github.com/echemdb/metadata-schema/blob/main/examples/file_schemas/svgdigitizer.yaml). Howevere, it is possibly more convenient to reuse existing YAML files which exist already in the [repository](https://github.com/echemdb/website/tree/main/literature)

Adjust all keys in the file according to the content of the research article.

## Step 5: Submit to echemdb.org

Propose a pull request in the GitHub repository that adds your directory to `website/literature`, e.g., by uploading the YAML, SVG and BIB files you created at https://github.com/echemdb/website/upload/main/literature/mustermann_2021_svgdigitizer_1 (replace `mustermann_2021_svgdigitizer_1` with the name of your data).

## Notes

If you want to test whether your files were prepared correctly for [echemdb.org](https://www.echemdb.org/cv), run:

`svgdigitizer cv mustermann_2021_svgdigitizer_1_f2a_blue.svg --metadata mustermann_2021_svgdigitizer_1_f2a_blue.yaml --sampling-interval 0.001 --bibliography`

This creates a CSV with the data of the plot and a JSON package file that you can inspect to verify that the data has been correctly extracted.

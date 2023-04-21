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

Command Line Interface
======================

The CLI allows creating SVG files from PDFs and allows digitizing the processed SVG files. Certain plot types have specific commands to recover different kinds of metadata. All options are revealed

```{note}
The preceding `!` in the following examples is used to evaluate bash commands in [jupyter notebooks](https://jupyter-tutorial.readthedocs.io/en/stable/workspace/ipython/shell.html). Remove the `!` to evaluate the command in the shell.
```

```{code-cell} ipython3
!svgdigitizer
```

```{code-cell} ipython3
!svgdigitizer cv --help
```

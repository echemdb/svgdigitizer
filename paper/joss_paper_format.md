# JOSS Paper Format Requirements

Source: https://joss.readthedocs.io/en/latest/paper.html
Retrieved: 2026-03-18

---

## Paper Specifications

| Property | Requirement |
|----------|-------------|
| Format | Markdown (`paper.md`) with YAML metadata header |
| Length | 750–1750 words |
| Purpose | High-level description only — API docs belong in software documentation, not the paper |

---

## Required Sections (6 mandatory)

### 1. Summary
A description of the high-level functionality and purpose of the software for a diverse,
non-specialist audience.

### 2. Statement of Need
Clarifies the research purpose, contextualizes within existing work, identifies problems solved,
target audiences, and relationship to alternatives.

### 3. State of the Field
Comparison with commonly-used packages, including a "build vs. contribute" justification explaining
the unique contributions of this software.

### 4. Software Design
Trade-offs weighed, architecture chosen, and relevance to research applications — demonstrating
substantive design thinking rather than superficial descriptions.

### 5. Research Impact Statement
Evidence of realized impact (publications, external use, integrations) or credible near-term
significance. Must be specific and compelling, not aspirational.

### 6. AI Usage Disclosure
Transparent disclosure of any use of generative AI in the software creation, documentation,
or paper authoring.

---

## Required Elements (beyond sections)

- Author list with affiliations
- Key references (full venue names, not abbreviations)
- Representative research projects using the software
- Recent publications enabled by the software
- Financial support acknowledgements

---

## YAML Metadata Header

```yaml
---
title: 'Paper Title Here'
tags:
  - keyword1
  - keyword2
authors:
  - name: Given Name Surname
    orcid: 0000-0000-0000-0000
    affiliation: 1
  - name: Another Author
    orcid: 0000-0000-0000-0000
    affiliation: "1, 2"
affiliations:
  - name: Institution Name, Country
    index: 1
    ror: 00xxxxxx   # optional ROR for top-level org
  - name: Another Institution, Country
    index: 2
date: 18 March 2026   # format: %e %B %Y
bibliography: paper.bib
---
```

**Author name fields:** Use `name`, or constituent parts:
`given-names`, `surname`, `dropping-particle`, `non-dropping-particle`, `suffix`.
Use `literal` as last resort for non-Western name forms.

**ROR identifiers** annotate top-level organizations only (not departments).

---

## Markdown Syntax Reference

### Inline Markup

| Effect | Syntax |
|--------|--------|
| Emphasis | `*text*` |
| Strong | `**text**` |
| Strikeout | `~~text~~` |
| Subscript | `H~2~O` |
| Superscript | `Ca^2+^` |
| Code | `` `code` `` |
| Small caps | `[text]{.sc}` |

### Figures

```markdown
![Caption text.](path/to/image.png)

![Caption with explicit size.](path/to/image.png){width="80%"}
```

Images scale automatically; explicit sizing: `{height="9pt"}` or `{width="100%"}`.

### Tables

Grid tables are supported with:
- Column/row spanning
- Multi-row headers and footers
- Intra-cellular block elements
- Alignment control via colons in separator lines

### Equations

```markdown
Inline: $E = mc^2$

Display:
$$
\frac{\partial u}{\partial t} = \nabla^2 u
\label{eq:diffusion}
$$
```

Cross-reference: `\ref{eq:diffusion}` or `\autoref{eq:diffusion}`

### Citations

BibLaTeX/BibTeX entries in `paper.bib`:

```markdown
Parenthetical: [@identifier]
Narrative:     Author et al. [@identifier] showed that...
With locator:  [@identifier, p. 42]
```

### Cross-References

```markdown
\ref{label}       # number only
\autoref{label}   # type + number (e.g., "Figure 1")
```

Label figures/tables in captions: `[]{label="fig:overview"}`

### Footnotes

```markdown
Text with footnote.[^fn1]

[^fn1]: Footnote content here.
```

### Headings

Use `#` symbols (1–5 levels); recommended to limit to 2–3 levels in the paper.

---

## Compilation Methods

### 1. GitHub Actions (recommended)
Add the Open Journals PDF Generator action to the repository. It auto-compiles on push and
makes the PDF available under Actions → Artifacts.

### 2. Docker (local preview)
```bash
docker run --rm \
  --volume $PWD/paper:/data \
  --user $(id -u):$(id -g) \
  --env JOURNAL=joss \
  openjournals/inara
```

### 3. Local (inara)
Clone the `inara` repository, install dependencies, and run `make`.

---

## Technical Notes

- Markdown is converted via Pandoc to both JATS XML and PDF
- PDFs are generated using ConTeXt for tagged PDF/A-3 accessibility compliance

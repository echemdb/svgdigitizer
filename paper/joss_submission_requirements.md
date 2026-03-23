# JOSS Submission Requirements Summary

Source: https://joss.readthedocs.io/en/latest/submitting.html
Retrieved: 2026-03-18

---

## Software Criteria

- Must be open source (OSI-approved license)
- Hosted where users can browse code, open issues, and propose changes without payment or approval barriers
- Must have an obvious research application
- Must be feature-complete (not a half-baked solution)
- Cloneable without registration; source files browsable online
- Readable issue tracker accessible without registration; public issue creation permitted

## Author Requirements

- Must be a major contributor to the submitted software
- Must have a GitHub account for review participation
- Paper must not focus on new research results *using* the software (that belongs in a domain journal)

## Paper & Repository Requirements

- Paper file named `paper.md` containing:
  - Title
  - Summary
  - Author names and affiliations
  - Key references (BibTeX)
- Paper, BibTeX file, and figures stored in the Git repository alongside the software
- Paper may live in a short-lived branch created from the default branch

---

## Pre-Review Screening Gates (All Must Be Met)

1. **Public Development History**
   Repository must be public for 6+ months with active development spanning that period.
   Automated checks verify genuine commit distribution — not repository dumps.

2. **Demonstrated Research Impact**
   Evidence the software is used for research (at minimum by the developers, ideally by others).
   Acceptable signals: published/preprint citations, DOIs, documented adoption, research workflow
   integration. Future aspirations are insufficient.

3. **Good Open Source Practices**
   - Multi-author projects: issues, pull requests, and public discussion expected.
   - Single-author projects: multiple indicators required, such as meaningful public commit history
     over time, tagged releases or changelog, tests/CI, clear documentation, CONTRIBUTING file,
     and stated support expectations.

4. **Iterative Development**
   History shows ongoing refinement, not concentrated bursts. Evidence that software has been
   refined through feedback over time.

---

## Scope & Significance Factors

- Research impact through publications, external adopters, or comparative benchmarks
- Meaningful architectural decisions / design thinking
- Open development practices showing sustained, collaborative effort
- Easy installation, understanding, and testing for users
- Likelihood of being cited by researchers in the domain
- Evidence of open development from early stages (not private-then-public releases)

---

## AI Usage Disclosure

Authors using generative AI must provide a statement including:

- Tools/models used (with versions) and where they were applied
- Nature and scope of assistance (code generation, refactoring, documentation, copy-editing, etc.)
- Confirmation that human authors reviewed and validated all AI outputs and made core design decisions

Non-disclosure may result in desk rejection, mandatory revisions, or post-publication correction/withdrawal.

---

## Key Policies

| Policy | Rule |
|--------|------|
| Conflict of Interest | All authors must disclose financial, personal, or professional relationships that may affect objectivity |
| Preprints | Allowed on arXiv, bioRxiv, etc. before, during, or after submission — not considered prior publication |
| Authorship | Financial contributions or general supervision alone are insufficient; active direction and non-code contributions are acceptable |
| Co-publication | Allowed when software implementation reflects substantial scientific effort; disclose related publications |
| Fees | None — no submission or publication fees |

---

## Submission Process

1. Make software available in an open repository with an OSI-approved license
2. Ensure software meets review criteria (full-featured, well-documented, automated testing)
3. Write `paper.md` in Markdown with title, summary, author information, references
4. Optionally create a metadata file (JOSS provides an automation script)
5. Fill in the submission form at the JOSS portal
6. Await managing editor's pre-review issue creation in the JOSS reviews repository

---

## Review Timeline & Expectations

- Associate EiC performs initial check and assigns a handling editor
- Handling editor assigns 2+ reviewers; review conducted in the JOSS reviews repository
- Authors respond to reviewer issues on the submission repository's issue tracker
- **Authors must respond within 2 weeks; complete changes within 4–6 weeks** (unless negotiated)
- Prolonged unresponsiveness may result in rejection

### Upon Acceptance

1. Create a tagged release of the software
2. Deposit with a data-archiving service (Zenodo, figshare, etc.) and obtain a DOI
3. Update the review thread with the DOI
4. JOSS assigns its own DOI and deposits metadata with CrossRef

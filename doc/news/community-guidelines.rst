**Added:**

* Added `CONTRIBUTING.md` with guidelines for reporting issues, asking questions and contributing code or documentation.
* Added `CODE_OF_CONDUCT.md` based on the Contributor Covenant 3.0.
* Added "Contributing and support" sections to the README and the documentation landing page.
* Added `CITATION.cff` so that GitHub shows a "Cite this repository" button.
* Added a `cff` pixi task and a CI check that validate `CITATION.cff`.

**Changed:**

* Changed the DOI in the README and the documentation to the Zenodo concept DOI, which always refers to the latest release.

**Removed:**

* Removed `.zenodo.json`. Zenodo now takes the release metadata from `CITATION.cff`.

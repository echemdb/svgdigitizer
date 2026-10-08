# Contributing to svgdigitizer

Thank you for your interest in svgdigitizer! Contributions of all kinds are welcome: bug reports, questions, feature ideas, documentation improvements and code. If you use svgdigitizer in your research, citing it ([DOI: 10.5281/zenodo.5874747](https://doi.org/10.5281/zenodo.5874747)) is a great way to support the project, too.

Everyone participating in this project is expected to follow our [Code of Conduct](CODE_OF_CONDUCT.md). Please report unacceptable behavior to <conduct@echemdb.org>.

## Questions, bugs, and feature requests

Please use the [issue tracker](https://github.com/echemdb/svgdigitizer/issues). Search the existing issues first, check the [documentation](https://echemdb.github.io/svgdigitizer/) and make sure you are using the latest version. For usage questions, open an issue with the `question` label.

If your bug involves data, which could be subject of a copyright or embargo (such as published or unpublished data), please try to reproduce the bug with a minimal example (such as a dummy PDF or SVG) that does not contain confidential content. If that is not possible, contact the maintainers by email at <info@echemdb.org> before sharing any files publicly.

When reporting a bug, please include

- the versions of svgdigitizer and Python, your operating system and how you installed svgdigitizer,
- the SVG file and the command or Python code you ran (a minimal example is best),
- the full error message or traceback, and what you expected to happen instead.

## Contributing code or documentation

We use [pixi](https://pixi.sh) for development. Fork the repository, clone your fork and create a branch:

```sh
git clone https://github.com/<your-username>/svgdigitizer.git
cd svgdigitizer
git checkout -b my-feature
```

The development environment is set up automatically on first use:

```sh
pixi run doctest   # run the doctests
pixi run pytest    # run the tests
pixi run lint      # run pylint, black and isort
pixi run doc       # build the documentation in doc/generated/html
```

Further commands can be inferred from the [pyproject.toml](pyproject.toml).

To run the tests with a specific Python version, select an environment, e.g., `pixi run -e python-312 doctest`.

We format the code with black and isort and check it with pylint; CI enforces all three, so please run `pixi run lint` before committing. Public functions and classes should have docstrings with examples that serve as doctests.

Then open a pull request against `master`. Please make sure that

- you added a news entry: copy [`doc/news/TEMPLATE.rst`](doc/news/TEMPLATE.rst) to `doc/news/<your-branch-name>.rst` and fill in the relevant sections,
- your change is covered by a test (usually a doctest),
- the documentation is updated, if needed,
- tests and linters pass (CI runs them on all supported Python versions and platforms).

If you add, remove, or change the version numbers of a dependency, update both `pyproject.toml` and `flake.nix`.

Issues labeled [`good first issue`](https://github.com/echemdb/svgdigitizer/issues?q=is%3Aissue+is%3Aopen+label%3A%22good+first+issue%22) are a good place to start. If you are unsure about anything, just open an issue or a draft pull request and ask. We are happy to help.

By contributing, you agree that your contributions are licensed under the project's [GPL-3.0-or-later](LICENSE) license.

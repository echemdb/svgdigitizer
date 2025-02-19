# Sphinx Documentation svgdigitizer

This documentation is automatically built and uploaded to GitHub Pages.


To build the documentation locally, type:

```sh
pixi run doc
```

The build requires internet access, since data is pulled from
external repositories to evaluate the documentation content.

The generated html can be found in `doc/generated/html` and can be served via

```sh
python -m http.server 8880 -b localhost --directory doc/generated/html &
```

Then open http://localhost:8880/ with your browser.

Most documentation files are written in mystnb, which can be converted into interactive ipynb with jupytext, by using jupyter.

```sh
pixi run jupyter lab
```

# Tracing CVs with Inkscape from publication

The cyclic voltammogram we trace is provided in Figure 2a in the [publication example](publication_example.pdf) and looks as follows:

[<img src="sample_data_2.png" width="450"/>](sample_data_2.png)

Using `svgdigitizer paginate Publication_example.pdf` creates for each page in the pdf a`svg` and `png` file in the same folder.

The plot is located on page two and contains three curves, which can be identified by their colors.

Preferably each digitized curve should be placed in a single svg file. Therefore, create a copy of the svg with the respective ending `*_p2.svg` and rename it using a simple and unique identifier, e.g., `*_p2_blue.svg`.


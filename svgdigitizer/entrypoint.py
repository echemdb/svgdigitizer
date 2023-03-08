r"""
The svgdigitizer suite.

EXAMPLES::

    >>> from svgdigitizer.test.cli import invoke
    >>> invoke(cli, "--help")  # doctest: +NORMALIZE_WHITESPACE
    Usage: cli [OPTIONS] COMMAND [ARGS]...
      The svgdigitizer suite.
    Options:
      --help  Show this message and exit.
    Commands:
      cv        Digitize a cylic voltammogram.
      digitize  Digitize a plot.
      paginate  Render PDF pages as individual SVG files with linked PNG images.
      plot      Display a plot of the data traced in an SVG.

"""
# ********************************************************************
#  This file is part of svgdigitizer.
#
#        Copyright (C) 2021-2023 Albert Engstfeld
#        Copyright (C)      2021 Johannes Hermann
#        Copyright (C) 2021-2023 Julian Rüth
#        Copyright (C)      2021 Nicolas Hörmann
#
#  svgdigitizer is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  svgdigitizer is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with svgdigitizer. If not, see <https://www.gnu.org/licenses/>.
# ********************************************************************
import os

import click


@click.group(help=__doc__.split("EXAMPLES")[0])
def cli():
    r"""
    Entry point of the command line interface.

    This redirects to the individual commands listed below.
    """


# The --skewed flag that is shared by many of the subcommands
skewed_option = click.option(
    "--skewed",
    is_flag=True,
    help="Detect non-orthogonal skewed axes going through the markers instead of assuming that axes are perfectly horizontal and vertical.",
)

si_option = click.option(
    "--si",
    is_flag=True,
    help="Converts units of the plot and CSV to SI (if possible).",
)


def _outfile(template, suffix=None, outdir=None):
    r"""
    Return a file name for writing.

    The file is named like `template` but with the suffix changed to `suffix`
    if specified. The file is created in `outdir`, if specified, otherwise in
    the directory of `template`.

    EXAMPLES::

        >>> from svgdigitizer.test.cli import invoke, TemporaryData
        >>> with TemporaryData("**/xy.svg") as directory:
        ...     outname = _outfile(os.path.join(directory, "xy.svg"), suffix=".csv")
        ...     with open(outname, mode="wb") as csv:
        ...         _ = csv.write(b"...")
        ...     os.path.exists(os.path.join(directory, "xy.csv"))
        True

    ::

        >>> with TemporaryData("**/xy.svg") as directory:
        ...     outname = _outfile(os.path.join(directory, "xy.svg"), suffix=".csv", outdir=os.path.join(directory, "subdirectory"))
        ...     with open(outname, mode="wb") as csv:
        ...         _ = csv.write(b"...")
        ...     os.path.exists(os.path.join(directory, "subdirectory", "xy.csv"))
        True

    """
    if suffix is not None:
        template = f"{os.path.splitext(template)[0]}{suffix}"

    if outdir is not None:
        template = os.path.join(outdir, os.path.basename(template))

    os.makedirs(os.path.dirname(template) or ".", exist_ok=True)

    return template


def _create_svgplot(svg, sampling_interval, skewed):
    r"""
    Return an :class:`SVGPlot` as read from the stream `svg`.

    EXAMPLES::

        >>> from svgdigitizer.test.cli import invoke, TemporaryData
        >>> with TemporaryData("**/xy.svg") as directory:
        ...     svg = os.path.join(directory, "xy.svg")
        ...     with open(svg, mode="rb") as infile:
        ...         _create_svgplot(infile, sampling_interval=None, skewed=False)
        <svgdigitizer.svgplot.SVGPlot object at 0x...>

    """
    from svgdigitizer.svg import SVG
    from svgdigitizer.svgplot import SVGPlot

    return SVGPlot(
        SVG(svg),
        sampling_interval=sampling_interval,
        algorithm="mark-aligned" if skewed else "axis-aligned",
    )


@click.command()
@click.option(
    "--sampling-interval",
    type=float,
    default=None,
    help="Sampling interval on the x-axis.",
)
@skewed_option
@click.argument("svg", type=click.File("rb"))
def plot(svg, sampling_interval, skewed):
    r"""
    Display a plot of the data traced in an SVG.

    EXAMPLES::

        >>> from svgdigitizer.test.cli import invoke, TemporaryData
        >>> with TemporaryData("**/xy.svg") as directory:
        ...     invoke(cli, "plot", os.path.join(directory, "xy.svg"))

    """
    svgplot = _create_svgplot(svg, sampling_interval=sampling_interval, skewed=skewed)
    svgplot.plot()


@click.command()
@click.option(
    "--sampling-interval",
    type=float,
    default=None,
    help="Sampling interval on the x-axis.",
)
@click.option(
    "--outdir",
    type=click.Path(file_okay=False),
    default=None,
    help="write output files to this directory",
)
@skewed_option
@click.argument("svg", type=click.Path(exists=True))
def digitize(svg, sampling_interval, outdir, skewed):
    r"""
    Digitize a plot.

    Produces a CSV from the curve traced in the SVG.

    EXAMPLES::

        >>> from svgdigitizer.test.cli import invoke, TemporaryData
        >>> with TemporaryData("**/xy_rate.svg") as directory:
        ...     invoke(cli, "digitize", os.path.join(directory, "xy_rate.svg"))

    """
    with open(svg, mode="rb") as infile:
        svg_plot = _create_svgplot(
            infile, sampling_interval=sampling_interval, skewed=skewed
        )

    svg_plot.df.to_csv(_outfile(svg, suffix=".csv", outdir=outdir), index=False)


@click.command(name="cv")
@click.option(
    "--sampling-interval",
    type=float,
    default=None,
    help="sampling interval on the x-axis in volts",
)
@click.option(
    "--metadata", type=click.File("rb"), default=None, help="yaml file with metadata"
)
@click.option("--package", is_flag=True, help="create .json in data package format")
@click.option(
    "--outdir",
    type=click.Path(file_okay=False),
    default=None,
    help="write output files to this directory",
)
@click.argument("svg", type=click.Path(exists=True))
@si_option
@skewed_option
def digitize_cv(svg, sampling_interval, metadata, package, outdir, skewed, si):
    r"""
    Digitize a cylic voltammogram.

    For inclusion in the echemdb.

    EXAMPLES::

        >>> from svgdigitizer.test.cli import invoke, TemporaryData
        >>> with TemporaryData("**/xy_rate.svg") as directory:
        ...     invoke(cli, "cv", os.path.join(directory, "xy_rate.svg"))

    TESTS:

    The command can be invoked on files in the current directory::

        >>> from svgdigitizer.test.cli import invoke, TemporaryData
        >>> cwd = os.getcwd()
        >>> with TemporaryData("**/xy_rate.svg") as directory:
        ...     os.chdir(directory)
        ...     try:
        ...         invoke(cli, "cv", "xy_rate.svg")
        ...     finally:
        ...         os.chdir(cwd)

    The command can be invoked without sampling when data is not given in volts::

        >>> from svgdigitizer.test.cli import invoke, TemporaryData
        >>> from svgdigitizer.svg import SVG
        >>> from svgdigitizer.svgplot import SVGPlot
        >>> from svgdigitizer.electrochemistry.cv import CV
        >>> with TemporaryData("**/xy_rate.svg") as directory:
        ...     with open(os.path.join(directory, "xy_rate.svg"), mode="rb") as svg:
        ...         print(CV(SVGPlot(SVG(svg))).figure_schema.get_field("E").custom["unit"])
        mV
        >>> with TemporaryData("**/xy_rate.svg") as directory:
        ...     invoke(cli, "cv", os.path.join(directory, "xy_rate.svg"))

    """
    from svgdigitizer.electrochemistry.cv import CV

    if sampling_interval is not None:
        # Rewrite the sampling interval in terms of the unit on the x-axis.
        with open(svg, mode="rb") as infile:
            cv = CV(
                _create_svgplot(infile, sampling_interval=None, skewed=skewed),
                si_units=si,
            )

            from astropy import units as u

            sampling_interval /= u.Unit(
                cv.figure_schema.get_field(cv.svgplot.xlabel).custom["unit"]
            ).to(u.V)

    if metadata:
        import yaml

        metadata = yaml.load(metadata, Loader=yaml.SafeLoader)

    with open(svg, mode="rb") as infile:
        cv = CV(
            _create_svgplot(infile, sampling_interval=sampling_interval, skewed=skewed),
            metadata=metadata,
            si_units=si,
        )

    csvname = _outfile(svg, suffix=".csv", outdir=outdir)
    cv.df.to_csv(csvname, index=False)

    if package:
        package = _create_package(cv.metadata, csvname, outdir)

    with open(
        _outfile(svg, suffix=".json", outdir=outdir),
        mode="w",
        encoding="utf-8",
    ) as json:
        _write_metadata(json, package.to_dict() if package else cv.metadata)


def _create_package(metadata, csvname, outdir):
    r"""
    Return a data package built from a :param:`metadata` dict and tabular data
    in :param:`csvname`.

    This is a helper method for :meth:`digitize_cv`.
    """
    from frictionless import Package, Resource, Schema

    package = Package(
        resources=[
            Resource(
                path=os.path.basename(csvname),
                basepath=outdir or os.path.dirname(csvname),
            )
        ],
    )
    package.infer()
    package.custom = metadata

    # Update fields in the datapackage describing the data in the CSV
    package_schema = package.resources[0].schema
    data_description_schema = Schema.from_descriptor(package.custom["data description"])

    new_fields = []
    for name in package_schema.field_names:
        if not name in data_description_schema.field_names:
            raise KeyError(
                f"Field with name {name} is not specified in `data_description.fields`."
            )
        new_fields.append(
            data_description_schema.get_field(name).to_dict()
            | package_schema.get_field(name).to_dict()
        )

    package.resources[0].schema = Schema.from_descriptor({"fields": new_fields})
    del package.custom["data description"]["fields"]

    return package


def _write_metadata(out, metadata):
    r"""
    Write `metadata` to the `out` stream in JSON format.

    This is a helper method for :meth:`digitize_cv`.
    """

    def defaultconverter(item):
        r"""
        Return `item` that Python's json package does not know how to serialize
        in a format that Python's json package does know how to serialize.
        """
        from datetime import date, datetime

        # The YAML standard knows about dates and times, so we might see these
        # in the metadata. However, standard JSON does not know about these so
        # we need to serialize them as strings explicitly.
        if isinstance(item, (datetime, date)):
            return str(item)

        raise TypeError(f"Cannot serialize ${item} of type ${type(item)} to JSON.")

    import json

    json.dump(metadata, out, default=defaultconverter, ensure_ascii=False, indent=4)
    # json.dump does not save files with a newline, which compromises the tests
    # where the output files are compared to an expected json.
    out.write("\n")


def _create_linked_svg(svg, png):
    r"""
    Write an SVG to `svg` that shows `png` as a linked image.

    This is a helper method for :meth:`paginate`.
    """
    from PIL import Image

    width, height = Image.open(png).size

    import svgwrite

    drawing = svgwrite.Drawing(
        svg,
        size=(f"{width}px", f"{height}px"),
        profile="full",
    )

    from svgwrite.extensions.inkscape import Inkscape

    Inkscape(drawing)

    img = drawing.add(
        svgwrite.image.Image(
            png,
            insert=(0, 0),
            size=(f"{width}px", f"{height}px"),
        )
    )

    # workaround: add missing locking attribute for image element
    # https://github.com/mozman/svgwrite/blob/c8cbf6f615910b3818ccf939fce0e407c9c789cb/svgwrite/extensions/inkscape.py#L50
    elements = drawing.validator.elements
    elements["image"].valid_attributes = {
        "sodipodi:insensitive",
    } | elements["image"].valid_attributes
    img.attribs["sodipodi:insensitive"] = "true"

    drawing.save(pretty=True)


@click.command()
@click.option("--onlypng", is_flag=True, help="Only produce png files")
@click.option(
    "--outdir",
    type=click.Path(file_okay=False),
    default=None,
    help="write output files to this directory",
)
@click.argument("pdf")
def paginate(onlypng, pdf, outdir):
    r"""
    Render PDF pages as individual SVG files with linked PNG images.

    The SVG and PNG files are written to the PDF's directory.

    EXAMPLES::

        >>> from svgdigitizer.test.cli import invoke, TemporaryData
        >>> with TemporaryData("**/mustermann_2021_svgdigitizer_1.pdf") as directory:
        ...     invoke(cli, "paginate", os.path.join(directory, "mustermann_2021_svgdigitizer_1.pdf"))

    """
    from pdf2image import convert_from_path

    pages = convert_from_path(pdf, dpi=600)
    pngs = [
        _outfile(pdf, suffix=f"_p{page}.png", outdir=outdir)
        for page in range(len(pages))
    ]

    for page, png in zip(pages, pngs):
        page.save(png, "PNG")

        if not onlypng:
            _create_linked_svg(_outfile(png, suffix=".svg", outdir=outdir), png)


cli.add_command(plot)
cli.add_command(digitize)
cli.add_command(digitize_cv)
cli.add_command(paginate)

# Register command docstrings for doctesting.
# Since commands are not functions anymore due to their decorator, their
# docstrings would otherwise be ignored.
__test__ = {
    name: command.__doc__ for (name, command) in cli.commands.items() if command.__doc__
}

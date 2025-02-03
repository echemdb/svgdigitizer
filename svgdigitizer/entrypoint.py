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
      cv        Digitize a cylic voltammogram and create a frictionless...
      digitize  Digitize a 2D plot.
      figure    Digitize a figure with units on the axis and create a...
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
import logging
import os

import click

logger = logging.getLogger("svgdigitizer")


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

bibliography_option = click.option(
    "--bibliography",
    is_flag=True,
    help="Adds bibliography data from a bibfile as descriptor to the datapackage.",
)

si_option = click.option(
    "--si-units",
    is_flag=True,
    help="Convert units of the plot and CSV to SI (only if they are compatible with astropy units).",
)

sampling_interval_option = click.option(
    "--sampling-interval",
    type=float,
    default=None,
    help="Sampling interval on the x-axis with respect to the x-axis values.",
)

outdir_option = click.option(
    "--outdir",
    type=click.Path(file_okay=False),
    default=None,
    help="Write output files to this directory.",
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


def _create_bibliography(svg, metadata):
    r"""
    Return a bibtex string built from a BIB file and a key provided in `metadata['source']['citation key']`,
    when both requirements are met. Otherwise an empty string is returned.

    This is a helper method for :meth:`_create_outfiles`.
    """
    from pybtex.database import parse_file

    metadata.setdefault("source", {})
    metadata["source"].setdefault("citation key", "")

    bibkey = metadata["source"]["citation key"]
    if not bibkey:
        logger.warning(
            'No bibliography key found in metadata["source"]["citation key"]'
        )
        return ""

    bib_directory = os.path.dirname(svg)

    bibfile = f"{os.path.join(bib_directory, bibkey)}.bib"

    if not os.path.exists(bibfile):
        logger.warning(
            f"A citation key with name {bibkey} was provided, but no BIB file was found."
        )
        return ""

    bibliography = parse_file(bibfile, bib_format="bibtex")
    return bibliography.entries[bibkey].to_string("bibtex")


@click.command()
@sampling_interval_option
@skewed_option
@click.argument("svg", type=click.File("rb"))
def plot(svg, sampling_interval, skewed):
    """
    Display a plot of the data traced in an SVG.
    \f

    EXAMPLES::

        >>> from svgdigitizer.test.cli import invoke, TemporaryData
        >>> with TemporaryData("**/xy.svg") as directory:
        ...     invoke(cli, "plot", os.path.join(directory, "xy.svg"))

    """
    svgplot = _create_svgplot(svg, sampling_interval=sampling_interval, skewed=skewed)
    svgplot.plot()


@click.command()
@sampling_interval_option
@outdir_option
@skewed_option
@click.argument("svg", type=click.Path(exists=True))
def digitize(svg, sampling_interval, outdir, skewed):
    """
    Digitize a 2D plot.

    Produces a CSV from the curve traced in the SVG.
    \f

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


@click.command(name="figure")
@sampling_interval_option
@outdir_option
@click.option(
    "--metadata", type=click.File("rb"), default=None, help="yaml file with metadata"
)
@click.argument("svg", type=click.Path(exists=True))
@si_option
@bibliography_option
@skewed_option
def digitize_figure(
    svg, sampling_interval, metadata, outdir, bibliography, skewed, si_units
):
    """
    Digitize a figure with units on the axis and create a frictionless datapackage.

    The resulting CVS contains a time axis, when text label with a scan rate is given
    in the SVG whose units must be of type `x-axis unit / time unit`, such as `scan rate: 50 K / s`.
    \f

    EXAMPLES::

        >>> from svgdigitizer.test.cli import invoke, TemporaryData
        >>> with TemporaryData("**/xy_rate.svg") as directory:
        ...     invoke(cli, "figure", os.path.join(directory, "xy_rate.svg"))

    TESTS:

    The command can be invoked on files in the current directory::

        >>> from svgdigitizer.test.cli import invoke, TemporaryData
        >>> cwd = os.getcwd()
        >>> with TemporaryData("**/xy_rate.svg") as directory:
        ...     os.chdir(directory)
        ...     try:
        ...         invoke(cli, "figure", "xy_rate.svg")
        ...     finally:
        ...         os.chdir(cwd)

    The command can be invoked without sampling when data is not given in volts::

        >>> from svgdigitizer.test.cli import invoke, TemporaryData
        >>> from svgdigitizer.svg import SVG
        >>> from svgdigitizer.svgplot import SVGPlot
        >>> from svgdigitizer.svgfigure import SVGFigure
        >>> with TemporaryData("**/xy_rate.svg") as directory:
        ...     with open(os.path.join(directory, "xy_rate.svg"), mode="rb") as svg:
        ...         print(SVGFigure(SVGPlot(SVG(svg))).figure_schema.get_field("E").custom["unit"])
        mV
        >>> with TemporaryData("**/xy_rate.svg") as directory:
        ...     invoke(cli, "figure", os.path.join(directory, "xy_rate.svg"))

    """
    if metadata:
        import yaml

        metadata = yaml.load(metadata, Loader=yaml.SafeLoader)

    with open(svg, mode="rb") as infile:
        from svgdigitizer.svgfigure import SVGFigure

        svgfigure = SVGFigure(
            _create_svgplot(infile, sampling_interval=sampling_interval, skewed=skewed),
            metadata=metadata,
            force_si_units=si_units,
        )

    _create_outfiles(
        svgfigure=svgfigure, svg=svg, outdir=outdir, bibliography=bibliography
    )


@click.command(name="cv")
@sampling_interval_option
@outdir_option
@click.option(
    "--metadata", type=click.File("rb"), default=None, help="yaml file with metadata"
)
@click.argument("svg", type=click.Path(exists=True))
@bibliography_option
@si_option
@skewed_option
def digitize_cv(
    svg, sampling_interval, metadata, outdir, skewed, bibliography, si_units
):
    """
    Digitize a cylic voltammogram and create a frictionless datapackage.

    The sampling interval should be provided in mV.

    For inclusion in www.echemdb.org.
    \f

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

    The command can be invoked without sampling when data is git not given in volts::

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
                force_si_units=si_units,
            )

            from astropy import units as u

            sampling_interval /= u.Unit(
                cv.figure_schema.get_field(cv.svgplot.xlabel).custom["unit"]
            ).to(
                u.V  # pylint: disable=no-member
            )

    if metadata:
        import yaml

        metadata = yaml.load(metadata, Loader=yaml.SafeLoader)

    with open(svg, mode="rb") as infile:
        svgfigure = CV(
            _create_svgplot(infile, sampling_interval=sampling_interval, skewed=skewed),
            metadata=metadata,
            force_si_units=si_units,
        )

    _create_outfiles(
        svgfigure=svgfigure, svg=svg, outdir=outdir, bibliography=bibliography
    )


def _create_outfiles(svgfigure, svg, outdir, bibliography):
    """Writes a datapackage consisting of a CSV and JSON file from a :param:'svgfigure'

    This is a helper method for CLI commands that digitize an svgfigure.
    """
    csvname = _outfile(svg, suffix=".csv", outdir=outdir)
    svgfigure.df.to_csv(csvname, index=False)

    metadata = svgfigure.metadata

    if bibliography:
        metadata.setdefault("source", {})
        metadata["source"].setdefault("bibdata", {})

        if metadata["source"]["bibdata"]:
            logger.warning(
                "The key with name `bibliography` in the metadata will be overwritten with the new bibliography data."
            )

        metadata["source"].update({"bibdata": _create_bibliography(svg, metadata)})

    package = _create_package(metadata, csvname, outdir)

    with open(
        _outfile(svg, suffix=".json", outdir=outdir),
        mode="w",
        encoding="utf-8",
    ) as json:
        _write_metadata(json, package.to_dict())


def _create_package(metadata, csvname, outdir):
    r"""
    Return a data package built from a :param:`metadata` dict and tabular data
    in :param:`csvname`.

    This is a helper method for :meth:`_create_outfiles`.
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
    resource = package.resources[0]

    resource.custom.setdefault("metadata", {})
    resource.custom["metadata"].setdefault("echemdb", metadata)

    # Update fields in the datapackage describing the data in the CSV
    package_schema = resource.schema
    data_description_schema = Schema.from_descriptor(
        {"fields": resource.custom["metadata"]["echemdb"]["data description"]["fields"]}
    )

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

    resource.schema = Schema.from_descriptor({"fields": new_fields})
    del resource.custom["metadata"]["echemdb"]["data description"]["fields"]

    return package


def _write_metadata(out, metadata):
    r"""
    Write `metadata` to the `out` stream in JSON format.

    This is a helper method for :meth:`_create_outfiles`.
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
@click.option("--onlypng", is_flag=True, help="Only produce png files.")
@click.option(
    "--outdir",
    type=click.Path(file_okay=False),
    default=None,
    help="Write output files to this directory.",
)
@click.argument("pdf")
def paginate(onlypng, pdf, outdir):
    """
    Render PDF pages as individual SVG files with linked PNG images.

    The SVG and PNG files are written to the PDF's directory.
    \f

    EXAMPLES::

        >>> from svgdigitizer.test.cli import invoke, TemporaryData
        >>> with TemporaryData("**/mustermann_2021_svgdigitizer_1.pdf") as directory:
        ...     invoke(cli, "paginate", os.path.join(directory, "mustermann_2021_svgdigitizer_1.pdf"))

    """
    import pymupdf

    doc = pymupdf.open(pdf)
    for page_idx, page in enumerate(doc):
        pix = page.get_pixmap(dpi=600)
        png = _outfile(pdf, suffix=f"_p{page_idx}.png", outdir=outdir)
        pix.save(png)
        if not onlypng:
            _create_linked_svg(_outfile(png, suffix=".svg", outdir=outdir), png)


cli.add_command(plot)
cli.add_command(digitize)
cli.add_command(digitize_figure)
cli.add_command(digitize_cv)
cli.add_command(paginate)

# Register command docstrings for doctesting.
# Since commands are not functions anymore due to their decorator, their
# docstrings would otherwise be ignored.
__test__ = {
    name: command.__doc__ for (name, command) in cli.commands.items() if command.__doc__
}

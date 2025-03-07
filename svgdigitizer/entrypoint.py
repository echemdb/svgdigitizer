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
      create-svg     Write an SVG that shows `png` or `jpeg` as a linked image.
      cv             Digitize a cylic voltammogram and create a frictionless...
      digitize       Digitize a 2D plot.
      figure         Digitize a figure with units on the axis and create a...
      get-citation   Get the citation from the DOI provided PDF file.
      get-doi        Get the DOI from the provided PDF file.
      paginate       Render PDF pages as individual SVG files with linked PNG...
      plot           Display a plot of the data traced in an SVG.
      rename-by-key  Rename the provided PDF file by the key derived from...

"""
# ********************************************************************
#  This file is part of svgdigitizer.
#
#        Copyright (C) 2021-2023 Albert Engstfeld
#        Copyright (C) 2021-2025 Johannes Hermann
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
    "--metadata", type=click.File("rb"), default=None, help="YAML file with metadata"
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
    del resource.custom["metadata"]["echemdb"]["data description"]

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


def _create_linked_svg(svg, img, template_file):
    r"""
    Write an SVG to `svg` that shows `image` as a linked image.

    This is a helper method for :meth:`paginate`.
    """
    _create_svg(svg, img, template_file, linked=True)


def _create_svg(svg, img, template_file, linked):
    r"""
    Write an SVG to `svg` that shows `image` either as a linked or embedded image.

    This is a helper method for :meth:`paginate`.
    """
    # pylint: disable=too-many-locals
    from PIL import Image

    width, height = Image.open(img).size

    import svgwrite

    drawing = svgwrite.Drawing(
        svg,
        size=(f"{width}px", f"{height}px"),
        profile="full",
    )

    from svgwrite.extensions.inkscape import Inkscape

    inkscape = Inkscape(drawing)

    image_layer = inkscape.layer(id="image-layer", locked=True)
    # add properties for svgedit
    image_layer.attribs["class"] = "layer"
    image_layer.set_desc(title="image-layer")
    drawing.add(image_layer)

    if linked:
        image_layer.add(
            svgwrite.image.Image(
                img,
                insert=(0, 0),
                size=(width, height),
            )
        )
    else:
        import base64
        import mimetypes

        img_mimetype = mimetypes.guess_type(img)[0].split("/")
        with open(img, "rb") as f:
            encoded = base64.b64encode(f.read()).decode()
        img_data = f"data:image/{img_mimetype};base64,{encoded}"
        image_layer.add(
            svgwrite.image.Image(
                href=(img_data),
                insert=(0, 0),
                size=(width, height),
            )
        )

    digitization_layer = inkscape.layer(id="digitization-layer", locked=False)

    digitization_layer.attribs["class"] = "layer"
    digitization_layer.set_desc(title="digitization-layer")
    drawing.add(digitization_layer)

    if template_file:
        from xml.etree import ElementTree as ET

        template_svg_root = ET.parse(template_file).getroot()
        main_root = ET.ElementTree(ET.fromstring(drawing.tostring()))
        layer_id = "digitization-layer"
        source_layer = template_svg_root.find(
            f".//{{http://www.w3.org/2000/svg}}g[@id='{layer_id}']"
        )
        target_layer = main_root.find(
            f".//{{http://www.w3.org/2000/svg}}g[@id='{layer_id}']"
        )
        if source_layer is not None and target_layer is not None:
            for elem in source_layer:
                target_layer.append(elem)
        main_root.write(svg, xml_declaration=True, encoding="utf-8")
    else:
        drawing.save(pretty=True)


def _extract_doi(pdf):
    "Extract DOI from first PDF page."
    import re

    import pymupdf

    doc = pymupdf.open(pdf)
    text = doc.get_page_text(0)
    matches = re.findall(r"10\.\d{4,9}\/[-._;()/:a-zA-Z0-9]+", text)
    if len(matches) == 1:
        return matches[0]

    raise KeyError(f"{len(matches)} DOIs found. Extraction of DOI failed.")


@click.command()
@click.argument("pdf")
def get_doi(pdf):
    r"""
    Get the DOI from the provided PDF file.

    """
    print(_extract_doi(pdf))


def _download_citation(doi):
    "Download citation for DOI"
    import requests

    resp = requests.get(
        "https://doi.org/" + doi,
        headers={"Accept": "application/x-bibtex; charset=utf-8"},
        timeout=5,
    )
    if resp.ok:
        return resp.text
    return ""


@click.command()
@click.argument("pdf")
def get_citation(pdf):
    r"""
    Get the citation from the DOI provided PDF file.

    """
    doi = _extract_doi(pdf)
    citation = _download_citation(doi)

    if citation:
        print(citation)
    else:
        raise KeyError("Failed to get citation.")


def _build_identifier(citation):
    """
    Build the entry identifier based on bibtex citation.

    TESTS:

        >>> from svgdigitizer.entrypoint import _build_identifier
        >>> from pybtex.database import parse_string
        >>> bibtex_string = ' @article{Mart_nez_Hincapi__2021, title={Surface charge and interfacial acid-base properties: pKa,2 of carbon dioxide at Pt(110)/perchloric acid solution interfaces.}, volume={388}, ISSN={0013-4686}, url={http://dx.doi.org/10.1016/j.electacta.2021.138639}, DOI={10.1016/j.electacta.2021.138639}, journal={Electrochimica Acta}, publisher={Elsevier BV}, author={Martínez-Hincapié, R. and Rodes, A. and Climent, V. and Feliu, J.M.}, year={2021}, month=aug, pages={138639} }' #pylint: disable=line-too-long
        >>> bibliography = parse_string(bibtex_string, bib_format="bibtex")
        >>> _build_identifier(bibliography)
        'martinez-hincapie_2021_surface_138639'

    """
    from slugify import slugify

    entry = list(citation.entries.values())[0]
    first_author = entry.persons["author"][0].last_names[0]
    title_words = entry.fields["title"].split(" ")
    first_word = title_words[0]
    if "the" == first_word:  # maybe add more words?
        first_word = title_words[1]
    year = entry.fields["year"]
    first_page = (
        entry.fields["pages"].split("–")[0].split("-")[0]
    )  # split unicode "–" and normal hypen "-"
    slugified_strs = [
        slugify(item) for item in [first_author, year, first_word, first_page]
    ]
    identifier = "_".join(slugified_strs)
    return identifier


@click.command()
@click.argument("pdf")
def rename_by_key(pdf):
    r"""
    Rename the provided PDF file by the key derived from citation.

    """
    from pybtex.database import parse_string

    doi = _extract_doi(pdf)
    citation = _download_citation(doi)
    bibliography = parse_string(citation, bib_format="bibtex")
    identifier = _build_identifier(bibliography)
    os.rename(pdf, identifier + ".pdf")


@click.command()
@click.option(
    "--template",
    type=str,
    default=None,
    help="Add builtin template elements in SVG files.",
)
@click.option(
    "--template-file",
    type=click.Path(dir_okay=False),
    default=None,
    help="Add template elements from a custom SVG in the SVG file.",
)
@click.option(
    "--outdir",
    type=click.Path(file_okay=False),
    default=None,
    help="Write output files to this directory.",
)
@click.argument("img")
def create_svg(img, template, outdir):
    r"""
    Write an SVG that shows `png` or `jpeg` as a linked image.

    """
    import mimetypes

    mimetype = mimetypes.guess_type(img)[0]
    if mimetype and mimetype.split("/")[1] in ["jpeg", "png"]:
        svg = _outfile(img, suffix=".svg", outdir=outdir)
        _create_svg(svg, img, template, True)
    else:
        raise click.BadParameter("Only PNG or JPEG image formats are supported.")


def _parse_pages_option(_ctx, _param, value):
    import re

    if value is None:
        return None

    match = re.fullmatch(r"(\d+)(?:-(\d+))?", value)
    if not match:
        raise click.BadParameter(
            "Invalid format. Use a single number or a range like '3-5'."
        )

    start = int(match.group(1))
    end = int(match.group(2)) if match.group(2) else start

    if start > end:
        raise click.BadParameter(
            "Invalid range. Start must be less than or equal to end."
        )

    return list(range(start, end + 1))


@click.command()
@click.option(
    "--pages",
    callback=_parse_pages_option,
    help="Specify a single page (e.g., '2') or a range (e.g., '3-5').",
)
@click.option(
    "--template",
    type=click.Choice(["basic"]),
    default=None,
    help="Add builtin template elements in SVG files.",
)
@click.option("--onlypng", is_flag=True, help="Only produce PNG files.")
@click.option(
    "--template",
    type=click.Choice(["basic"]),
    default=None,
    help="Add builtin template elements in SVG files.",
)
@click.option(
    "--template-file",
    type=click.Path(dir_okay=False),
    default=None,
    help="Add template elements from a custom SVG in SVG files.",
)
@click.option(
    "--outdir",
    type=click.Path(file_okay=False),
    default=None,
    help="Write output files to this directory.",
)
@click.argument("pdf")
def paginate(pages, onlypng, template, template_file, pdf, outdir):
    """
    Render PDF pages as individual SVG files with linked PNG images.

    The SVG and PNG files are written to the PDF's directory.
    \f

    EXAMPLES::

        >>> from svgdigitizer.test.cli import invoke, TemporaryData
        >>> with TemporaryData("**/mustermann_2021_svgdigitizer_1.pdf") as directory:
        ...     invoke(cli, "paginate", os.path.join(directory, "mustermann_2021_svgdigitizer_1.pdf"))

    TESTS::

        >>> from svgdigitizer.test.cli import invoke, TemporaryData

    """
    from importlib.resources import files

    import pymupdf

    if template and template_file:
        raise click.BadParameter(
            "Please provide either a file or a builtin template name."
        )
    if template:
        template_file = files("svgdigitizer").joinpath(
            "assets", f"template_{template}.svg"
        )

    doc = pymupdf.open(pdf)
    num_pages = doc.page_count
    if not pages:
        page_range = range(num_pages)
    else:
        page_range = pages
        if page_range not in range(num_pages):
            raise click.BadParameter(
                f"Invalid range. Page numbers must be within 0-{num_pages}."
            )
    for page_idx in page_range:
        pix = doc.load_page(page_idx).get_pixmap(dpi=600)
        png = _outfile(pdf, suffix=f"_p{page_idx}.png", outdir=outdir)
        pix.save(png)
        if not onlypng:
            _create_linked_svg(
                _outfile(png, suffix=".svg", outdir=outdir), png, template_file
            )


cli.add_command(plot)
cli.add_command(digitize)
cli.add_command(digitize_figure)
cli.add_command(digitize_cv)
cli.add_command(paginate)
cli.add_command(create_svg)
cli.add_command(get_doi)
cli.add_command(get_citation)
cli.add_command(rename_by_key)

# Register command docstrings for doctesting.
# Since commands are not functions anymore due to their decorator, their
# docstrings would otherwise be ignored.
__test__ = {
    name: command.__doc__ for (name, command) in cli.commands.items() if command.__doc__
}

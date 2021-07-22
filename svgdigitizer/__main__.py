#*********************************************************************
#  This file is part of svgdigitizer.
#
#        Copyright (C) 2021 Albert Engstfeld
#        Copyright (C) 2021 Johannes Hermann
#        Copyright (C) 2021 Julian Rüth
#        Copyright (C) 2021 Nicolas Hörmann
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
#*********************************************************************
import click

@click.group()
def cli(): pass

@click.command()
@click.option('--sampling_interval', type=float, default=None, help='specify sampling interval (for now in mV)')
@click.argument('svg')
def plot(svg, sampling_interval):
    from svgdigitizer.svgplot import SVGPlot
    SVGPlot(svg, sampling_interval=sampling_interval).plot()

@click.command()
@click.option('--sampling_interval', type=float, default=None, help='specify sampling interval (for now in mV)')
@click.argument('basename')
def digitize(basename, sampling_interval):
    from svgdigitizer.svgplot import SVGPlot
    SVGPlot(basename, sampling_interval=sampling_interval).create_csv()

@click.command()
@click.option('--onlypng', is_flag=True, help='Only produce png files')
@click.argument('pdf')
def paginate(onlypng, pdf):
    from pdf2image import convert_from_path
    import svgwrite
    from PIL import Image
    basename = pdf.split('.')[0]
    pages = convert_from_path(pdf, dpi=600,)
    for idx, page in enumerate(pages):
        base_image_path = f'{basename}_p{idx}'
        page.save(f'{base_image_path}.png', 'PNG')
        if not onlypng:
            image = Image.open(f'{base_image_path}.png')
            width, height = image.size
            dwg = svgwrite.Drawing(f'{base_image_path}.svg', 
            size = (f'{width}px',
                    f'{height}px'), profile='tiny')
            dwg.add(svgwrite.image.Image(f'{base_image_path}.png', insert=(0,0), size = (f'{width}px',
                    f'{height}px')))
            dwg.save()


cli.add_command(plot)
cli.add_command(digitize)
cli.add_command(paginate)

if __name__ == "__main__":
    cli()

import click

@click.group()
def cli(): pass

@click.command()
@click.argument('svg')
def plot(svg):
    from svgdigitizer.svgdigitizer import SvgData
    SvgData(svg).plot()

@click.command()
@click.argument('basename')
def digitize(basename):
    from svgdigitizer.csvcreator import CreateCVdata
    CreateCVdata(basename).create_csv()

@click.command()
@click.option('--onlypng')
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

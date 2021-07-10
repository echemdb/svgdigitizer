import click

@click.group()
def cli(): pass

@click.command()
@click.option('--sampling_interval',  help='specify sampling interval (for now in mV)')
@click.argument('svg')
def plot(svg):
    from svgdigitizer.svgdigitizer import SvgData
    if sampling_interval:
        SvgData(svg, sampling_interval=float(sampling_interval)).plot()
    else:
        SvgData(svg).plot()

@click.command()
@click.option('--sampling_interval',  help='specify sampling interval (for now in mV)')
@click.argument('basename')
def digitize(basename, sampling_interval):
    from svgdigitizer.csvcreator import CreateCVdata
    if sampling_interval:
        CreateCVdata(basename, sampling_interval=float(sampling_interval)).create_csv()
    else:
        CreateCVdata(basename).create_csv()

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

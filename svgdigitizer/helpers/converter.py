import click

@click.group()
def cli(): pass

@click.command()
@click.argument('basename')
def topng(basename):
    from pdf2image import convert_from_path
    pages = convert_from_path(f'{basename}.pdf', dpi=600,)
    for idx, page in enumerate(pages):
        page.save(f'{basename}_p{idx}.png', 'PNG')

@click.command()
@click.argument('basename')
def tosvg(basename):
    from pdf2image import convert_from_path
    import svgwrite
    from PIL import Image
    pages = convert_from_path(f'{basename}.pdf', dpi=600,)
    for idx, page in enumerate(pages):
        base_image_path = f'{basename}_p{idx}'
        page.save(f'{base_image_path}.png', 'PNG')
        
        image = Image.open(f'{base_image_path}.png')
        width, height = image.size
        dwg = svgwrite.Drawing(f'{base_image_path}.svg', 
        size = (f'{width}px',
                f'{height}px'), profile='tiny')
        dwg.add(svgwrite.image.Image(f'{base_image_path}.png', insert=(0,0), size = (f'{width}px',
                f'{height}px')))
        dwg.save()

cli.add_command(topng)
cli.add_command(tosvg)

if __name__ == "__main__":
    cli()

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

cli.add_command(plot)
cli.add_command(digitize)

if __name__ == "__main__":
    cli()

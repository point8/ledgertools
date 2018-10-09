import json
import click
import pickle

from ledgertools.read import read_file
from ledgertools.version import __version__

@click.group(help='CLI tools for working with ledger')
@click.version_option(version=__version__, prog_name='Ledger Tools')
def cli():
    pass


@cli.command(help='Import ledger style file')
@click.option('-f', '--file', 'in_file', help='Input file name', prompt='Input file name')
@click.option('-n', '--name', default='transactions.json', help='Output file name')
@click.option('-p', '--pickle', 'as_pickle', is_flag=True, help='Output as pickle file')
@click.option('--stdout', is_flag=True, help='Output to stdout, supresses output files')
def read(in_file, name, as_pickle, stdout):
    click.secho(f'Reading input file: {in_file}', fg='green')
    transactions = read_file(in_file)

    if stdout:
        print(json.dumps(transactions, sort_keys=True, indent=4, ensure_ascii=False))
        return 0
    if as_pickle:
        name = name.replace('json', 'pkl')
        with open(name, 'wb') as out_file:
            # Pickle the 'data' dictionary using the highest protocol available.
            pickle.dump(transactions, out_file, pickle.HIGHEST_PROTOCOL)
    else:
        with open(name, 'w', encoding='utf-8') as out_file:
            json.dump(transactions, out_file, sort_keys=True, indent=4, ensure_ascii=False)

    if not stdout:
        click.secho(f'Saving output to: {name}', fg='green')


def main():
    cli()

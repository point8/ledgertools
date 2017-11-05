# Ledger Tools

Command line tools for working with [ledger](http://ledger-cli.org)

## Available commands

```
$ ledgert --help

Usage: ledgert [OPTIONS] COMMAND [ARGS]...

  CLI tools for working with ledger

Options:
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  read  Import ledger style file
```

### Import ledger style files

Reading ledger journal file and save as json formatted file

```
ledgert read -f /path/to/input/ledger/file
```

* `--file` input file name
* `--name` option to provide output file name
* `--pickle` option to save as serialized object instead of json


## Local Setup

## pip

Simply use `pip install -U .` for a local installation.

### Development

Use `pip install -e .` for a local development installation. Where `-e` _"installs a project in editable mode (i.e.
setuptools "develop mode") from a local project path"_ thus every change of the source is made directly available.


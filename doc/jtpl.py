#!/usr/bin/env python3

"""
    Command line utility for applying jinja 2 template from
    yaml, json or toml
"""
import sys
import os
import argparse

from pathlib import Path

try:
    import jinja2
except ImportError:
    print('jinja2 is required',file=sys.stderr)
    sys.exit(1)


def _load_json( path: Path ):
    import json
    with path.open() as f:
        return json.loads(f.read())


def _load_ini( path: Path ):
    import configparser
    parser = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
    parser.read_file( path.as_posix()  )
    return { s: dict(p.items()) for s,p in parser.items() }


def _load_yaml( path: Path ):
    try:
        import yaml
    except ImportError:
        print('PyYaml no installed',file=sys.stderr)
        sys.exit(1)
    with path.open() as f:
        return yaml.safe_load(f)


def _load_properties( path: Path ):
    from configparser import SafeConfigParser
    from io import StringIO
    with path.open() as f:
        parser = configparser.ConfigParser()
        parser.readfp(StringIO("[ROOT]\n"+fp.read()))
    return { k:v for k,v in parser.items("ROOT") }
            

def _load_toml( path: Path ):
    try:
        import toml
    except ImportError:
        print('Toml no installed',file=sys.stderr)
        sys.exit(1)
    with path.open() as f:
        return toml.loads(f.read())



# Global list of available format parsers on your system
_FORMATS = {
    "json": _load_json,
    "ini": _load_ini,
    "yaml": _load_yaml,
    "yml": _load_yaml,
    "toml": _load_toml,
    "properties": _load_properties,
}
        

def _render(template: Path, config):
    with template.open() as f:
        tpl = jinja2.Template(f.read())    
        return tpl.render(config)    


def _get_loader_for( path: Path ):
    """ Guess format from filename
    """
    return _FORMATS.get(path.suffix.lstrip('.'))


def _get_output( path: Path ):
    """ Guess output file
    """
    if path.suffix == '.j2':
        return path.with_suffix('')
    else:
        return path.with_suffix(path.suffix + '.out')


def main():
    
    import argparse

    p =  argparse.ArgumentParser(description='Apply template to file')
    p.add_argument('inputs', nargs='+',help='Input files')
    p.add_argument('-c','--config', help="Config file", required=True)
    p.add_argument('-f','--format' , help="Format",  choices=list(_FORMATS.keys()))
    
    args = p.parse_args()
    input_files = args.inputs

    config = Path(args.config)
    loader = _FORMATS[args.format] if args.format else _get_loader_for(config)
    if not loader:
        print('Cannot guess format for %s' % confif, file=sys.stderr)
        sys.exit(1)

    # Load configuration
    config = loader(config) 

    for inp in args.inputs:
        templ = Path(inp)
        outp  = _get_output( templ )
        with outp.open('w') as f:
            f.write(_render(templ,config))

main()

"""Restore an exported /experiments/{id}/artifacts response safely, offline."""
import argparse
import base64
import json
from pathlib import Path


def restore(payload, destination):
    destination = Path(destination).resolve()
    if destination.exists():
        raise ValueError('Destination must not exist')
    checked=[]
    for name, encoded in payload['files'].items():
        path=destination/name
        if Path(name).is_absolute() or not path.resolve().is_relative_to(destination):
            raise ValueError('Unsafe artifact path')
        checked.append((path,base64.b64decode(encoded,validate=True)))
    destination.mkdir(parents=True)
    for path, data in checked:
        path.parent.mkdir(parents=True,exist_ok=True)
        path.write_bytes(data)

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('archive',type=Path)
    parser.add_argument('destination',type=Path)
    args=parser.parse_args()
    restore(json.loads(args.archive.read_text()),args.destination)

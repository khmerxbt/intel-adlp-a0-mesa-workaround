#!/usr/bin/env python3
"""Download a pinned source archive and extract it without escaping the target."""
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import tarfile
import urllib.request
ROOT = Path(__file__).resolve().parents[1]

def verify(data, expected):
    if hashlib.sha256(data).hexdigest() != expected:
        raise ValueError('source SHA256 mismatch')

def extract(data, destination):
    destination = Path(destination).resolve()
    if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
        raise FileExistsError('refusing to overwrite source directory: '+str(destination))
    with tarfile.open(fileobj=io.BytesIO(data), mode='r:*') as archive:
        entries=[]; tops=set()
        for member in archive.getmembers():
            path=Path(member.name)
            if path.is_absolute() or '..' in path.parts or not path.parts:
                raise ValueError('unsafe archive path')
            tops.add(path.parts[0]); rel=Path(*path.parts[1:])
            if len(path.parts)==1:
                continue
            if not (member.isdir() or member.isfile() or member.issym()):
                raise ValueError('unsupported archive entry')
            if member.issym():
                target=Path(member.linkname)
                if target.is_absolute(): raise ValueError('absolute archive link')
                resolved=(destination/rel.parent/target).resolve()
                if destination not in resolved.parents and resolved!=destination:
                    raise ValueError('escaping archive link')
            entries.append((member,rel))
        if len(tops)!=1: raise ValueError('expected one archive root')
        destination.mkdir(parents=True,exist_ok=True)
        # Regular data first; then links, so archive parent links cannot redirect writes.
        for member,rel in entries:
            if member.issym(): continue
            target=destination/rel
            if member.isdir(): target.mkdir(parents=True,exist_ok=True)
            else:
                target.parent.mkdir(parents=True,exist_ok=True)
                with archive.extractfile(member) as stream: target.write_bytes(stream.read())
                target.chmod(member.mode & 0o777)
        for member,rel in entries:
            if member.issym():
                target=destination/rel;target.parent.mkdir(parents=True,exist_ok=True)
                target.symlink_to(member.linkname)
        for member,rel in entries:
            if member.issym() and destination not in (destination/rel).resolve().parents:
                raise ValueError('escaping archive link chain')

def fetch(key, destination, archive_path=None):
    lock=json.loads((ROOT/'sources.lock.json').read_text())[key]
    if archive_path:
        data=Path(archive_path).read_bytes();verify(data,lock['sha256'])
    else:
        data=None;errors=[]
        for url in [lock['url']]+([lock['fallback_url']] if lock.get('fallback_url') else []):
            try:
                with urllib.request.urlopen(url,timeout=120) as stream: candidate=stream.read()
                verify(candidate,lock['sha256']);data=candidate;break
            except Exception as exc: errors.append(str(exc))
        if data is None: raise RuntimeError('unable to retrieve verified source: '+'; '.join(errors))
    extract(data,destination)
    print('Verified and extracted '+key)

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source',choices=json.loads((ROOT/'sources.lock.json').read_text()))
    parser.add_argument('destination',type=Path)
    parser.add_argument('--archive',type=Path,help='verify an existing archive without downloading')
    args=parser.parse_args();fetch(args.source,args.destination,args.archive)

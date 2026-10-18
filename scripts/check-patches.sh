#!/bin/sh
set -eu
repo=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
work=$(mktemp -d)
trap 'rm -rf "$work"' EXIT HUP INT TERM
if [ "$#" = 1 ]; then
 python3 "$repo/scripts/fetch_sources.py" mesa "$work/source" --archive "$1"
else
 python3 "$repo/scripts/fetch_sources.py" mesa "$work/source"
fi
for patchfile in "$repo"/patches/*.patch; do
 patch --dry-run -d "$work/source" -p1 < "$patchfile"
 patch -d "$work/source" -p1 < "$patchfile"
done
printf '%s\n' 'PASS: ordered patches apply cleanly to verified Mesa source'

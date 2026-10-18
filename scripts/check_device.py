#!/usr/bin/env python3
"""Read minimal PCI graphics identity; no GPU submission, kernel changes or serials."""
import argparse,json
from pathlib import Path

def inspect(root):
 rows=[]
 for path in sorted(Path(root).glob('*')):
  try:
   vendor=int((path/'vendor').read_text(),16);device=int((path/'device').read_text(),16)
   revision=int((path/'revision').read_text(),16);cls=int((path/'class').read_text(),16)
  except (OSError,ValueError): continue
  if cls>>16!=3: continue
  rows.append({'vendor':f'{vendor:04x}','device':f'{device:04x}','revision':f'{revision:02x}',
   'matches_tested_identity':vendor==0x8086 and device==0x46a1 and revision==0})
 return rows
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--sysfs',default='/sys/bus/pci/devices');a=p.parse_args()
 print(json.dumps({'graphics_devices':inspect(a.sysfs),'note':'Identity match is not a stability guarantee; other ES models are unvalidated.'},indent=2))

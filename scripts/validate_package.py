#!/usr/bin/env python3
"""Check published text, local documentation links and required source metadata."""
import ast,json,re,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FORBIDDEN={
 'private workstation path':r'/Users/|/vol[12]/',
 'private IPv4 address':r'\b(?:192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|172\.(?:1[6-9]|2\d|3[01])\.\d{1,3}\.\d{1,3})\b',
 'machine UUID':r'\b[0-9a-f]{8}-(?:[0-9a-f]{4}-){3}[0-9a-f]{12}\b',
 'credential':r'(?i)(?:gh[pousr]_[A-Za-z0-9]{25,}|github_pat_[A-Za-z0-9_]{25,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----)',
}

def main():
 errors=[];files=[]
 for f in ROOT.rglob('*'):
  rel=f.relative_to(ROOT)
  if any(x in {'.git','work','out','.cache','__pycache__'} for x in rel.parts) or not f.is_file():continue
  files.append(f)
  try:s=f.read_text()
  except UnicodeDecodeError:errors.append(str(rel)+': unexpected binary');continue
  if f.name!='validate_package.py':
   for label,pattern in FORBIDDEN.items():
    if re.search(pattern,s):errors.append(str(rel)+': '+label)
  if f.suffix=='.py':ast.parse(s,filename=str(rel))
  if f.suffix=='.sh':
   r=subprocess.run(['sh','-n',str(f)],capture_output=True,text=True)
   if r.returncode: errors.append(str(rel)+': shell syntax')
  if f.suffix=='.json':json.loads(s)
  if f.suffix=='.md':
   for target in re.findall(r'\]\(([^)]+)\)',s):
    if target.startswith(('https://','http://','#','mailto:')):continue
    target=target.split('#',1)[0]
    if target and not (f.parent/target).exists():errors.append(str(rel)+': broken local link '+target)
 lock=json.loads((ROOT/'sources.lock.json').read_text())
 for key,x in lock.items():
  if not re.fullmatch('[0-9a-f]{64}',x['sha256']) or not x['url'].startswith('https://'):errors.append('invalid source pin: '+key)
 if errors:print('\n'.join(errors));return 1
 print(f'PASS: {len(files)} text files; source pins, syntax, links and publication privacy checks')
 return 0
if __name__=='__main__':sys.exit(main())

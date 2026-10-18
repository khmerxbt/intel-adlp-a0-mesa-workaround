import hashlib,importlib.util,io,json,tarfile,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def module(name):
 spec=importlib.util.spec_from_file_location(name,ROOT/'scripts'/(name+'.py'))
 value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
fetch=module('fetch_sources');device=module('check_device')
def archive(entries):
 data=io.BytesIO()
 with tarfile.open(fileobj=data,mode='w') as t:
  for name,body,kind in entries:
   x=tarfile.TarInfo(name)
   if kind=='link':x.type=tarfile.SYMTYPE;x.linkname=body;t.addfile(x)
   else:
    b=body.encode();x.size=len(b);t.addfile(x,io.BytesIO(b))
 return data.getvalue()
class SourceTests(unittest.TestCase):
 def test_checksum_mismatch_rejected(self):
  with self.assertRaises(ValueError):fetch.verify(b'changed','0'*64)
 def test_extract_regular_and_internal_link(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'source';fetch.extract(archive([('src/a','value','file'),('src/sub/b','../a','link')]),out)
   self.assertEqual((out/'sub/b').read_text(),'value')
 def test_escape_paths_rejected(self):
  for name in ['../escape','/absolute','root/../../escape']:
   with self.subTest(name=name),tempfile.TemporaryDirectory() as d:
    with self.assertRaises(ValueError):fetch.extract(archive([(name,'x','file')]),Path(d)/'source')
 def test_escape_link_rejected(self):
  with tempfile.TemporaryDirectory() as d:
   with self.assertRaises(ValueError):fetch.extract(archive([('root/b','../../outside','link')]),Path(d)/'source')
 def test_empty_submodule_directory_allowed(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'source';out.mkdir()
   fetch.extract(archive([('root/a','x','file')]),out)
   self.assertEqual((out/'a').read_text(),'x')
 def test_existing_source_preserved(self):
  with tempfile.TemporaryDirectory() as d:
   out=Path(d)/'source';out.mkdir();(out/'keep').write_text('original')
   with self.assertRaises(FileExistsError):fetch.extract(archive([('root/a','x','file')]),out)
   self.assertEqual((out/'keep').read_text(),'original')
class IdentityTests(unittest.TestCase):
 def test_later_revision_not_claimed_tested(self):
  with tempfile.TemporaryDirectory() as d:
   for n,revision in [('a',0),('b',4)]:
    p=Path(d)/n;p.mkdir()
    for k,v in {'vendor':'0x8086','device':'0x46a1','revision':hex(revision),'class':'0x030000'}.items():(p/k).write_text(v)
   self.assertEqual([x['matches_tested_identity'] for x in device.inspect(d)],[True,False])
 def test_non_graphics_device_excluded(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'a';p.mkdir()
   for k,v in {'vendor':'0x8086','device':'0x46a1','revision':'0x00','class':'0x010000'}.items():(p/k).write_text(v)
   self.assertEqual(device.inspect(d),[])
if __name__=='__main__':unittest.main()

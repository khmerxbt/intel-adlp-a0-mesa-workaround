#!/usr/bin/env python3
"""Build installed driver targets and six relevant regression executables."""
import argparse,json,subprocess
from pathlib import Path
TESTS={'isl_adlp_a0_ccs_test','isl_surf_get_image_offset_test','isl_aux_info_test',
'isl_tile_std_y_test','isl_tilememcpy_test','isl_surf_get_image_range_B_tile_test'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('build',type=Path);p.add_argument('--jobs',type=int,default=4);a=p.parse_args()
 if a.jobs<1: p.error('--jobs must be positive')
 build=a.build.resolve();targets=json.loads(subprocess.check_output(['meson','introspect','--targets',str(build)]))
 outputs=[];found=set()
 for target in targets:
  if target['name'] in TESTS:found.add(target['name'])
  if target['installed'] or target['name'] in TESTS:
   outputs += [str(Path(f).relative_to(build)) for f in target['filename']]
 assert found==TESTS, 'missing regression executables'
 subprocess.run(['ninja','-C',str(build),'-j'+str(a.jobs),*outputs],check=True)

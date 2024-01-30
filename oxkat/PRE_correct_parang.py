#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import glob
import json
import os
import os.path as o
import subprocess
import sys
from multiprocessing import Pool


sys.path.append(o.abspath(o.join(o.dirname(sys.modules[__name__].__file__), "..")))
from oxkat import generate_jobs as gen
from oxkat import config as cfg


def correct_parang(subms,field):
	print(f'{subms}, field {field} ')
	syscall = 'python3 '+cfg.TOOLS+'/correct_parang.py --noparang --applyantidiag --chunksize 5000 '
	syscall += '--field '+field+' --rawcolumn DATA --storecolumn DATA ' 
	syscall += subms
	syscall = syscall.split()
	subprocess.run(syscall,stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)


with open('project_info.json') as f:
    project_info = json.load(f)


if not cfg.CAL_1GC_DOPOL:
	print('Polcal disabled in the config, skipping PA correction')
	sys.exit()

polcal_tag = project_info['polcal_tag']
if polcal_tag == 'None':
	print('No primary polarisation calibrator present, skipping PA correction')
	sys.exit()


myms = project_info['working_ms']
master_field_list = project_info['master_field_list'].split(',')
subms_list = sorted(glob.glob(myms+'/SUBMSS/*.ms'))
print(f'Found {len(subms_list)} sub MS in {myms}')


j = cfg.CAL_1GC_PAWORKERS
pool = Pool(processes = j)
pool.starmap(correct_parang,zip(subms_list,master_field_list))


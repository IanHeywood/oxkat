#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import glob
import json
import os
import os.path as o
import subprocess
import sys
sys.path.append(o.abspath(o.join(o.dirname(sys.modules[__name__].__file__), "..")))


from oxkat import generate_jobs as gen
from oxkat import config as cfg


with open('project_info.json') as f:
    project_info = json.load(f)


if not cfg.CAL_1GC_DOPOL:
	print('Polcal disabled in the config, skipping PA correction')
	sys.exit()

myms = project_info['working_ms']
bpcal = project_info['primary_id']
targets = project_info['target_ids']
pcals = project_info['secondary_ids']
polcal = project_info['polcal_id']
polcal_tag = project_info['polcal_tag']
fields = [bpcal]+targets+pcals
if polcal_tag != 'None': 
	fields += polcal
else:
	print('No primary polarisation calibrator present, skipping PA correction')

fields = sorted(fields)

for field in fields:
	syscall = 'python3 '+cfg.TOOLS+'/correct_parang.py --noparang --applyantidiag --chunksize 500000 '
	syscall += '--field '+field+' --rawcolumn DATA --storecolumn DATA ' 
	syscall += myms
	subprocess.run([syscall],shell=True)

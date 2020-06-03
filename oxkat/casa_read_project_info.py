#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


# Spoonfeed CASA's python2 the contents of the python3 project_info.p file
# without having to ruin my life with string formats.


import pickle


def str_iterator(inlist):
	xx = []
	for yy in inlist:
		xx.append(str(yy))
	return xx

project_info = pickle.load(open('project_info.p','rb'))

myms = str(project_info['master_ms'])
nchan = int(project_info['nchan'])
ref_ant = str(project_info['ref_ant'])
bpcal = str(project_info['primary_id'])
bpcal_name = str(project_info['primary_name'])
primary_tag = str(project_info['primary_tag'])
pcal_names = str_iterator(project_info['secondary_names'])
pcals = str_iterator(project_info['secondary_ids'])
pcal_dirs = project_info['secondary_dirs']
target_names = str_iterator(project_info['target_names'])
targets = str_iterator(project_info['target_ids'])
target_dirs = project_info['target_dirs']
target_cal_map = str_iterator(project_info['target_cal_map'])
target_ms = str_iterator(project_info['target_ms'])


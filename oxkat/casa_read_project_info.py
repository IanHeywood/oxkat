#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import json
import sys
execfile('oxkat/config.py')


def str_iterator(inlist):
	xx = []
	for yy in inlist:
		xx.append(str(yy))
	return xx


with open('project_info.json') as f:
	project_info = json.load(f)

master_ms = str(project_info['master_ms'])
myms = str(project_info['working_ms'])
band = str(project_info['band'])
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

if PRE_FIELDS != '':

	pre_field_list = PRE_FIELDS.split(',')

	user_targets = []
	user_pcals = []
	user_cal_map = []

	names = False
	for src in [bpcal_name]+target_names+pcal_names:
		if src in pre_field_list:
			names = True

	if names:
		if bpcal_name not in pre_field_list:
			print('Pre-field selection does not include a primary calibrator')
			sys.exit()
		for src in target_names:
			if src in pre_field_list:
				user_targets.append(src)
		for src in pcal_names:
			if src in pre_field_list:
				user_pcals.append(src)

	if not names:
		if bpcal not in pre_field_list:
			print('Pre-field selection does not include a primary calibrator')
			sys.exit()
		for src in targets:
			idx = targets.index(src)
			if src in pre_field_list:
				user_targets.append(target_names[idx])
		for src in pcals:
			idx = pcals.index(src)
			if src in pre_field_list:
				user_pcals.append(pcal_names[idx])

	for src in user_targets:
		idx = target_names.index(src)
		user_cal_map.append(target_cal_map[idx])









#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import json
import os.path as o
import sys
sys.path.append(o.abspath(o.join(o.dirname(sys.modules[__name__].__file__), "..")))

from oxkat import generate_jobs as gen
from oxkat import config as cfg

PRE_FIELDS = cfg.PRE_FIELDS


with open('project_info.json') as f:
    project_info = json.load(f)


bpcal_name = project_info['primary_name']
target_names = project_info['target_names']
pcal_names = project_info['secondary_names']
bpcal = project_info['primary_id']
targets = project_info['target_ids']
pcals = project_info['secondary_ids']
target_cal_map = project_info['target_cal_map']



if PRE_FIELDS != '':

	pre_field_list = PRE_FIELDS.split(',')

	user_targets = []
	user_pcals = []
	user_pcal_ids = []
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

	# for src in user_pcals:
	# 	idx = pcal_names.index(src)
	# 	user_pcal_ids.append(pcals[idx])









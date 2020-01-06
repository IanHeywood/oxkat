#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import os
import pickle
import sys
from optparse import OptionParser


def main()


	parser = OptionParser(usage='%prog [options]')
	parser_add_option('--ms',dest='master_ms',help='Master Measurement Set',default='')
	parser.add_option('--primary',dest='primary',help='Primary calibrator',default='')
	parser.add_option('--secondary',dest='secondary',help='Secondary calibrator',default='')
	parser.add_option('--target',dest='target',help='Target field, or comma-separated fields list',default='')
	parser.add_option('--refant',dest='refant',help='Reference antenna (default = 0)')
	parser.add_option('--overwrite',dest='overwrite',action='store_true',default=False)


	(options,args) = parser.parse_args()
	primary = options.primary
	secondary = options.secondary
	target = options.target
	refant = options.refant
	overwrite = options.overwrite


	outpick = 'project_info.p'


	if os.path.isfile(outpick) and not overwrite:
		print('Cannot overwrite existing pickle.')
		sys.exit()


	if '' in [master_ms,primary,secondary,target]:
		print('Please specify MS and full field information.')
		sys.exit()




if __name__ == "__main__":


    main()

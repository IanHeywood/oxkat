#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import glob
import os.path as o
import pickle
import sys
sys.path.append(o.abspath(o.join(o.dirname(sys.modules[__name__].__file__), "..")))


from oxkat import generate_jobs as gen




def main():

    RAGAVI_CONTAINER = gen.RAGAVI_CONTAINER

	dependency = sys.argv[1]

	caltabs = sorted(glob.glob('cal_*'))

	for caltab in caltabs:

		gaintype = caltab.split('.')[-1][0]

		print gaintype
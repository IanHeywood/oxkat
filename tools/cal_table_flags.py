#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import glob
import numpy
import sys
from pyrap.tables import table


def main():

	pat = sys.argv[1]

	tabs = glob.glob('*'+pat+'*')

	for tab in tabs:

		tt = table(tab)

		flags = tt.getcol('FLAG')

		flag_pc = 100.0 * round(flags.sum() / float(flags.size),2)

		print tab,flag_pc


if __name__ == "__main__":


    main()
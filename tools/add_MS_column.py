#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk

import sys
from optparse import OptionParser
from pyrap.tables import table


def add_data_col(msname,colname):
    tt = table(msname,readonly=False)
    colnames = tt.colnames()
    if colname in colnames:
        print(colname+' already exists, will not be created')
    else:
        print('Adding '+colname+' to '+msname)
        desc = tt.getcoldesc('DATA')
        desc['name'] = colname
        desc['comment'] = desc['comment'].replace(' ','_')
        tt.addcols(desc)
    tt.done()


def main():

    parser = OptionParser(usage = '%prog [options] msname')
    parser.add_option('--colname', dest = 'colname', default = 'DIR1_DATA', help = 'Name (or comma-separated list) of new data column(s) (default = DIR1_DATA)')
    (options,args) = parser.parse_args()
    colname = options.colname

    if len(args) != 1:
        print('Please specify a Measurement Set')
        sys.exit()
    else:
        msname = args[0].rstrip('/')

    for col in colname.split(','):
        add_data_col(msname,col)


if __name__ == '__main__':

    main()

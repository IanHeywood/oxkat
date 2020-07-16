#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import sys
from optparse import OptionParser
from pyrap.tables import table


def copycol(msname,fromcol,tocol):

    tt = table(msname,readonly=False,ack=False)

    colnames = tt.colnames()
    if fromcol not in colnames or tocol not in colnames:
        print('One or more requested columns not present in MS')
        sys.exit()

    total_rows = tt.nrows()
    chunk = total_rows // 10
    for start_row in range(0, total_rows, chunk):
        num_rows = min(chunk, total_rows - start_row)
        data = tt.getcol(fromcol, start_row, num_rows)
        tt.putcol(tocol, data, start_row, num_rows)
    tt.close()


def main():


    parser = OptionParser(usage = '%prog [options] msname')
    parser.add_option('--fromcol', dest = 'fromcol', default = 'MODEL_DATA', help = 'Name of source column (default = MODEL_DATA')
    parser.add_option('--tocol', dest = 'tocol', default = 'DIR1_DATA', help = 'Name of destination column (default = DIR1_DATA')
    (options,args) = parser.parse_args()
    fromcol = options.fromcol
    tocol = options.tocol


    if len(args) != 1:
        print('Please specify a Measurement Set')
        sys.exit()
    else:
        msname = args[0].rstrip('/')


    copycol(msname,fromcol,tocol)



if __name__ == '__main__':

    main()
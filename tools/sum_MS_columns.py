#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import sys
from optparse import OptionParser
from pyrap.tables import table


def sumcol(msname,src,dest,subtract,rowchunk):

    tt = table(msname,readonly=False)

    colnames = tt.colnames()
    if src not in colnames or dest not in colnames:
        print('One or more requested columns not present in MS')
        sys.exit()

    print(msname)
    if subtract:
        print('Subtracting '+src+' from '+dest)
    else:
        print('Adding '+src+' to '+dest)

    nrows = tt.nrows()
    for start_row in range(0,nrows,rowchunk):
        nr = min(rowchunk,nrows-start_row)
        print('Processing rows:',start_row,' to ',(start_row+nrows))
        src_data = tt.getcol(src,start_row,nr)
        dest_data = tt.getcol(dest,start_row,nr)
        if subtract:
            dest_data = dest_data - src_data
        else:
            dest_data += src_data
        tt.putcol(dest,dest_data,start_row,nr)


def main():


    parser = OptionParser(usage = '%prog [options] msname')
    parser.add_option('--src', dest = 'src', help = 'Name of source column.')
    parser.add_option('--dest', dest = 'dest', help = 'Name of destination column to which source column will be added.')
    parser.add_option('--subtract', dest = 'subtract', default = False, help = 'Enable to subtract source column from destination column.', action = 'store_true')
    parser.add_option('--rowchunk', dest = 'rowchunk', default = 500000, help = 'Number of chunks to process at once (default = 500000)')
    (options,args) = parser.parse_args()
    src = options.src
    dest = options.dest
    subtract = options.subtract
    rowchunk = int(options.rowchunk)


    if len(args) != 1:
        print('Please specify a Measurement Set')
        sys.exit()
    else:
        msname = args[0].rstrip('/')


    sumcol(msname,src,dest,subtract,rowchunk)



if __name__ == '__main__':

    main()
#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import numpy
import sys
from optparse import OptionParser
from pyrap.tables import table


def sumcol(msname,src,dest,field,subtract,rowchunk):

    if field == '': 
        tt = table(msname,readonly=False)
    else:
        print('Selecting FIELD_ID '+str(field))
        t0 = table(msname,readonly=False)
        tt = t0.query(query='FIELD_ID=='+str(field))

    colnames = tt.colnames()
    if src not in colnames or dest not in colnames:
        print('One or more requested columns not present in MS')
        sys.exit()

    spws = numpy.unique(tt.getcol('DATA_DESC_ID'))
    print('Spectral windows: '+str(spws))

    print(msname)
    if subtract:
        print('Subtracting '+src+' from '+dest)
    else:
        print('Adding '+src+' to '+dest)

    for spw in spws:
        spw_tab = tt.query(query='DATA_DESC_ID=='+str(spw))

        nrows = spw_tab.nrows()
        for start_row in range(0,nrows,rowchunk):
            nr = min(rowchunk,nrows-start_row)
            print('Processing rows: '+str(start_row)+' to '+str(start_row+nr)+' for SPW '+str(spw))
            src_data = spw_tab.getcol(src,start_row,nr)
            dest_data = spw_tab.getcol(dest,start_row,nr)
            if subtract:
                dest_data = dest_data - src_data
            else:
                dest_data += src_data
            spw_tab.putcol(dest,dest_data,start_row,nr)
        spw_tab.done()
    tt.done()

    if field != '': t0.done()


def main():


    parser = OptionParser(usage = '%prog [options] msname')
    parser.add_option('--src', dest = 'src', help = 'Name of source column.')
    parser.add_option('--dest', dest = 'dest', help = 'Name of destination column to which source column will be added.')
    parser.add_option('--field', dest = 'field', default = '', help = 'Field selection (default = all fields)')
    parser.add_option('--subtract', dest = 'subtract', default = False, help = 'Enable to subtract source column from destination column.', action = 'store_true')
    parser.add_option('--rowchunk', dest = 'rowchunk', default = 500000, help = 'Number of chunks to process at once (default = 500000)')
    (options,args) = parser.parse_args()
    src = options.src
    dest = options.dest
    field = options.field
    subtract = options.subtract
    rowchunk = int(options.rowchunk)


    if len(args) != 1:
        print('Please specify a Measurement Set')
        sys.exit()
    else:
        msname = args[0].rstrip('/')


    sumcol(msname,src,dest,field,subtract,rowchunk)



if __name__ == '__main__':

    main()
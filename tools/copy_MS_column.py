#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import numpy
import sys
from optparse import OptionParser
from pyrap.tables import table


def copycol(msname,fromcol,tocol,field,rowchunk):

    if field == '': 
        tt = table(msname,readonly=False)
    else:
        print('Selecting FIELD_ID '+str(field))
        t0 = table(msname,readonly=False)
        tt = t0.query(query='FIELD_ID=='+str(field))

    colnames = tt.colnames()
    if fromcol not in colnames or tocol not in colnames:
        print('One or more requested columns not present in MS')
        sys.exit()

    spws = numpy.unique(tt.getcol('DATA_DESC_ID'))
    print('Spectral windows: '+str(spws))

    for spw in spws:
        spw_tab = tt.query(query='DATA_DESC_ID=='+str(spw))
            
        nrows = spw_tab.nrows()
        for start_row in range(0,nrows,rowchunk):
            nr = min(rowchunk,nrows-start_row)
            print('Processing rows: '+str(start_row)+' to '+str(start_row+nr)+' for SPW '+str(spw))
            spw_tab.putcol(tocol,spw_tab.getcol(fromcol,start_row,nr),start_row,nr)
        spw_tab.done()
    tt.done()

    if field != '': t0.done()


def main():


    parser = OptionParser(usage = '%prog [options] msname')
    parser.add_option('--fromcol', dest = 'fromcol', default = 'MODEL_DATA', help = 'Name of source column (default = MODEL_DATA')
    parser.add_option('--tocol', dest = 'tocol', default = 'DIR1_DATA', help = 'Name of destination column (default = DIR1_DATA')
    parser.add_option('--field', dest = 'field', default = '', help = 'Field selection (default = all fields)')
    parser.add_option('--rowchunk', dest = 'rowchunk', default = 500000, help = 'Number of chunks to process at once (default = 500000)')
    (options,args) = parser.parse_args()
    fromcol = options.fromcol
    tocol = options.tocol
    field = options.field
    rowchunk = int(options.rowchunk)


    if len(args) != 1:
        print('Please specify a Measurement Set')
        sys.exit()
    else:
        msname = args[0].rstrip('/')


    copycol(msname,fromcol,tocol,field,rowchunk)



if __name__ == '__main__':

    main()
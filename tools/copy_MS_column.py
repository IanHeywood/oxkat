#!/usr/bin/env python
# ian.heywood@physics.ox.ac.uk


import sys
from optparse import OptionParser
from pyrap.tables import table


def copycol(msname,fromcol,tocol,field,rowchunk):

    if field == '': 
        tt = table(msname,readonly=False)
    else:
        t0 = table(msname,readonly=False)
        tt = table.query(query='FIELD_ID=='+str(field))

    colnames = tt.colnames()
    if fromcol not in colnames or tocol not in colnames:
        print('One or more requested columns not present in MS')
        sys.exit()

    # total_rows = tt.nrows()
    # chunk = total_rows // 10
    # for start_row in range(0, total_rows, chunk):
    #     num_rows = min(chunk, total_rows - start_row)
    #     data = tt.getcol(fromcol, start_row, num_rows)
    #     tt.putcol(tocol, data, start_row, num_rows)
    # tt.close()

    nrows = tt.nrows()
    for start_row in range(0,nrows,rowchunk):
        nr = min(rowchunk,nrows-start_row)
        print('Processing rows:',start_row,' to ',(start_row+nr))
        tt.putcol(tocol,tt.getcol(fromcol,start_row,nr),start_row,nr)

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
    field = options.tocol
    rowchunk = int(options.rowchunk)


    if len(args) != 1:
        print('Please specify a Measurement Set')
        sys.exit()
    else:
        msname = args[0].rstrip('/')


    copycol(msname,fromcol,tocol,field,rowchunk)



if __name__ == '__main__':

    main()